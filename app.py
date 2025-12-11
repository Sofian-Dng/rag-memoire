import os
import shutil
import streamlit as st
from dotenv import load_dotenv
import nest_asyncio

# Permettre les boucles d'événements imbriquées pour Streamlit
nest_asyncio.apply()
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from openai import OpenAI

# Importer le text splitter selon la version disponible
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        from langchain_community.text_splitter import RecursiveCharacterTextSplitter

# Configuration des chemins
DATA_PATH = "data/"
FAISS_PATH = "faiss_index/"

# Charger les variables d'environnement
def load_env_file():
    """Charge le fichier .env depuis le répertoire courant"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_path):
        # Lire et nettoyer le fichier du BOM
        try:
            with open(env_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig supprime automatiquement le BOM
                content = f.read()
            
            # Réécrire le fichier sans BOM
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception:
            pass  # Si erreur, continuer quand même
        
        load_dotenv(dotenv_path=env_path, override=True)
        return True
    return False

# Charger le .env au démarrage
load_env_file()

# Chargement des secrets (local .env ou Streamlit secrets pour déploiement)
def get_secret(key):
    """Récupère une variable depuis .env ou st.secrets"""
    # Recharger le .env à chaque fois pour être sûr (seulement en mode développement)
    if not hasattr(get_secret, '_env_loaded'):
        load_env_file()
        get_secret._env_loaded = True
    
    # Essayer d'abord avec os.getenv (pour développement local avec .env)
    value = os.getenv(key)
    if value is not None and value.strip() != '':
        return value.strip()
    
    # Essayer aussi avec la clé nettoyée du BOM (au cas où le BOM serait dans le nom de la clé)
    # Le BOM UTF-8 est \ufeff
    if value is None:
        # Essayer de lire directement depuis le fichier .env
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r', encoding='utf-8-sig') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' in line:
                            env_key, env_value = line.split('=', 1)
                            # Nettoyer la clé du BOM et des espaces
                            env_key = env_key.strip().lstrip('\ufeff').strip()
                            if env_key == key:
                                return env_value.strip()
            except Exception:
                pass
    
    # Sinon essayer avec st.secrets (pour déploiement)
    try:
        return st.secrets[key]
    except (AttributeError, KeyError):
        return None
    except Exception:
        # Capturer toutes les autres exceptions (comme StreamlitSecretNotFoundError)
        return None

# Fonction d'authentification
def authenticate():
    """Affiche un formulaire de connexion et vérifie les identifiants"""
    st.title("🔐 Authentification")
    
    username = get_secret("USERNAME")
    password = get_secret("PASSWORD")
    
    # Nettoyer les valeurs (enlever les espaces)
    if username:
        username = username.strip()
    if password:
        password = password.strip()
    
    if username is None or password is None:
        st.error("⚠️ Les identifiants ne sont pas configurés. Veuillez définir USERNAME et PASSWORD dans .env ou st.secrets")
        # Debug: afficher ce qui a été chargé
        with st.expander("🔍 Debug - Variables chargées"):
            st.write(f"USERNAME chargé: {repr(username)}")
            st.write(f"PASSWORD chargé: {repr(password)}")
            st.write(f"Fichier .env existe: {os.path.exists('.env')}")
        return False
    
    with st.form("login_form"):
        input_username = st.text_input("Nom d'utilisateur")
        input_password = st.text_input("Mot de passe", type="password")
        submit_button = st.form_submit_button("Se connecter")
        
        if submit_button:
            # Nettoyer aussi les entrées utilisateur
            input_username = input_username.strip()
            input_password = input_password.strip()
            
            # Debug en cas d'échec
            if input_username != username or input_password != password:
                st.error("❌ Identifiants incorrects")
                with st.expander("🔍 Debug - Comparaison"):
                    st.write(f"Username attendu: {repr(username)}")
                    st.write(f"Username saisi: {repr(input_username)}")
                    st.write(f"Match username: {input_username == username}")
                    st.write(f"Password attendu: {repr('*' * len(password) if password else None)}")
                    st.write(f"Password saisi: {repr('*' * len(input_password) if input_password else None)}")
                    st.write(f"Match password: {input_password == password}")
                return False
            else:
                st.session_state.authenticated = True
                st.rerun()
    
    return st.session_state.get("authenticated", False)

# Fonction pour obtenir les embeddings (locaux, rapides)
def get_embeddings():
    """Retourne les embeddings locaux (Sentence Transformers) - beaucoup plus rapides que Gemini"""
    # Utiliser un modèle français léger et rapide
    model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={'device': 'cpu'},  # Utiliser CPU (plus compatible)
        encode_kwargs={'normalize_embeddings': True}
    )

# Fonction d'indexation des documents
def index_documents():
    """Indexe les documents PDF dans FAISS"""
    try:
        # Vérifier si l'index existe déjà
        if os.path.exists(FAISS_PATH) and os.path.exists(os.path.join(FAISS_PATH, "index.faiss")):
            st.info("📚 Chargement de l'index existant...")
            embeddings = get_embeddings()
            vector_store = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
            st.success("✅ Index chargé avec succès !")
            return vector_store
        
        # Sinon, créer un nouvel index
        st.info("📚 Création d'un nouvel index...")
        
        # Vérifier que le dossier data existe
        if not os.path.exists(DATA_PATH):
            st.error(f"❌ Le dossier {DATA_PATH} n'existe pas. Veuillez le créer et y placer vos fichiers PDF.")
            return None
        
        # Charger les fichiers PDF
        pdf_files = [f for f in os.listdir(DATA_PATH) if f.endswith('.pdf')]
        
        if not pdf_files:
            st.error(f"❌ Aucun fichier PDF trouvé dans {DATA_PATH}")
            return None
        
        st.info(f"📄 {len(pdf_files)} fichier(s) PDF trouvé(s). Indexation en cours...")
        
        # Charger et segmenter les documents
        documents = []
        for pdf_file in pdf_files:
            loader = PyPDFLoader(os.path.join(DATA_PATH, pdf_file))
            docs = loader.load()
            # Ajouter le nom du fichier comme métadonnée
            for doc in docs:
                doc.metadata['source'] = pdf_file
            documents.extend(docs)
        
        # Segmenter les documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(documents)
        
        st.info(f"📝 {len(splits)} segments créés. Génération des embeddings en cours...")
        st.info("💡 Utilisation d'embeddings locaux (rapides) - le modèle sera téléchargé la première fois uniquement")
        
        # Utiliser les embeddings locaux (beaucoup plus rapides)
        with st.spinner("Chargement du modèle d'embeddings (première fois uniquement)..."):
            embeddings = get_embeddings()
        
        # Pour les petits documents (< 100 segments), traiter tout en une fois (plus rapide)
        # Pour les gros documents, utiliser des lots pour éviter les timeouts
        if len(splits) < 100:
            # Traitement en une seule fois pour les petits documents
            with st.spinner("Génération des embeddings (quelques secondes)..."):
                try:
                    vector_store = FAISS.from_documents(splits, embeddings)
                except Exception as e:
                    st.warning(f"⚠️ Erreur, nouvelle tentative...")
                    vector_store = FAISS.from_documents(splits, embeddings)
        else:
            # Traitement par lots pour les gros documents
            batch_size = 50  # Lots plus grands pour réduire le nombre d'appels
            total_batches = (len(splits) + batch_size - 1) // batch_size
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Créer le vector store progressivement
            vector_store = None
            for i in range(0, len(splits), batch_size):
                batch = splits[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                
                status_text.text(f"Traitement du lot {batch_num}/{total_batches} ({len(batch)} segments)...")
                progress_bar.progress(batch_num / total_batches)
                
                try:
                    if vector_store is None:
                        # Premier lot : créer le vector store
                        vector_store = FAISS.from_documents(batch, embeddings)
                    else:
                        # Lots suivants : ajouter au vector store existant
                        vector_store.add_documents(batch)
                except Exception as e:
                    # En cas d'erreur, réessayer une fois
                    st.warning(f"⚠️ Erreur sur le lot {batch_num}, nouvelle tentative...")
                    try:
                        if vector_store is None:
                            vector_store = FAISS.from_documents(batch, embeddings)
                        else:
                            vector_store.add_documents(batch)
                    except Exception as e2:
                        st.error(f"❌ Erreur persistante sur le lot {batch_num}: {str(e2)}")
                        raise e2
            
            progress_bar.empty()
            status_text.empty()
        
        # Sauvegarder l'index
        os.makedirs(FAISS_PATH, exist_ok=True)
        vector_store.save_local(FAISS_PATH)
        
        st.success(f"✅ Index créé avec succès ! {len(splits)} segments indexés.")
        return vector_store
        
    except Exception as e:
        st.error(f"❌ Erreur lors de l'indexation : {str(e)}")
        return None

# Fonction pour générer une réponse (approche directe avec plus de contexte)
def generate_answer(vector_store, question, mode="question"):
    """Génère une réponse développée en utilisant plusieurs segments de documents
    
    Args:
        vector_store: Le vector store FAISS
        question: La question de l'utilisateur
        mode: "question" pour réponses normales, "redaction" pour format mémoire académique
    """
    
    # Récupérer plusieurs documents pertinents (10 segments pour maximum de contexte)
    docs = vector_store.similarity_search(question, k=10)
    
    if not docs:
        return "Aucun document pertinent trouvé.", []
    
    # Construire le contexte à partir de tous les documents trouvés
    context_parts = []
    sources_info = []
    
    for i, doc in enumerate(docs, 1):
        source_name = doc.metadata.get("source", "Inconnu")
        page = doc.metadata.get("page", "N/A")
        content = doc.page_content
        
        context_parts.append(f"[Document {i} - Source: {source_name}, Page: {page}]\n{content}")
        sources_info.append((source_name, page))
    
    # Combiner tous les contextes
    full_context = "\n\n---\n\n".join(context_parts)
    
    # Créer le prompt selon le mode
    if mode == "redaction":
        # PROMPT MODE RÉDACTION - Format mémoire académique ultra-précis
        prompt_text = f"""Vous êtes un chercheur rédigeant un mémoire académique de niveau universitaire. Votre tâche est de rédiger un texte qui pourra être INTÉGRÉ DIRECTEMENT dans un mémoire, en respectant les normes académiques les plus strictes.

FORMAT ET STYLE OBLIGATOIRES :
- Rédigez comme un chercheur universitaire : ton scientifique, précis, objectif
- Structurez en paragraphes cohérents et bien enchaînés
- Utilisez un vocabulaire académique et spécialisé
- Évitez les formulations familières ou conversationnelles
- Chaque paragraphe doit développer une idée principale
- Utilisez des transitions logiques entre les paragraphes
- Intégrez les citations de manière fluide dans le texte
- Format de citation : (Source: nom_fichier.pdf, Page: X)
- Longueur : minimum 4-6 paragraphes développés
- Pas de formules de politesse, pas de "je", pas de "nous" sauf si nécessaire
- Écrivez comme si c'était déjà dans votre mémoire

STRUCTURE ATTENDUE :
1. Introduction du sujet (1-2 paragraphes)
2. Développement argumenté avec synthèse des sources (2-4 paragraphes)
3. Conclusion/synthèse (1 paragraphe)

CONTEXTE (plusieurs documents pertinents) :
{full_context}

SUJET/QUESTION: {question}

RÉDACTION ACADÉMIQUE (texte prêt à être intégré dans un mémoire) :"""
    
    else:
        # PROMPT MODE QUESTION - Réponses normales et conversationnelles
        prompt_text = f"""Vous êtes un assistant expert en rédaction de mémoire académique. Votre rôle est de fournir des réponses DÉVELOPPÉES, DÉTAILLÉES et ARGUMENTÉES basées strictement sur le CONTEXTE fourni ci-dessous.

INSTRUCTIONS IMPORTANTES :
- Fournissez une réponse COMPLÈTE et DÉVELOPPÉE (minimum 3-4 paragraphes si possible)
- Structurez votre réponse de manière claire et académique
- Utilisez TOUS les éléments pertinents du contexte fourni
- Citez vos sources entre parenthèses : (Source: nom_fichier.pdf, Page: X)
- Ton formel mais accessible
- Si plusieurs documents abordent le sujet, synthétisez-les de manière cohérente
- Développez les concepts, donnez des exemples si disponibles dans le contexte
- Ne vous contentez pas d'une réponse courte, EXPLIQUEZ et DÉVELOPPEZ

CONTEXTE (plusieurs documents pertinents) :
{full_context}

QUESTION: {question}

RÉPONSE DÉVELOPPÉE (minimum 3-4 paragraphes, bien structurée) :"""
    
    # Utiliser OpenAI directement (plus rapide et fiable, sans LangChain)
    try:
        client = OpenAI(api_key=get_secret("OPENAI_API_KEY"))
        
        # Déterminer le message système selon le mode
        if mode == "redaction":
            system_content = "Vous êtes un chercheur universitaire rédigeant un mémoire académique. Votre style doit être scientifique, précis et prêt à être intégré directement dans un document académique."
        else:
            system_content = "Vous êtes un assistant expert en rédaction académique. Vous fournissez des réponses développées, détaillées et bien structurées."
        
        # Appel direct à l'API OpenAI avec GPT-4 et plus de tokens pour des réponses développées
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",  # GPT-4 Turbo pour meilleure qualité
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.3,  # Légèrement augmenté pour plus de variété
            max_tokens=3000,  # Augmenté à 3000 tokens pour des réponses très développées
            timeout=90  # Timeout augmenté pour GPT-4 qui peut être plus lent
        )
        
        answer = response.choices[0].message.content
        
    except Exception as e:
        answer = f"Erreur lors de la génération: {str(e)}"
    
    return answer, docs

# Fonction principale
def main():
    """Fonction principale de l'application"""
    
    # Initialiser l'état de session
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = None
    
    if "mode" not in st.session_state:
        st.session_state.mode = "question"  # Mode par défaut : question
    
    # Vérifier l'authentification
    if not st.session_state.authenticated:
        if not authenticate():
            return
    
    # Vérifier que l'API key est disponible
    api_key = get_secret("OPENAI_API_KEY")
    if not api_key:
        st.error("⚠️ OPENAI_API_KEY n'est pas configurée. Veuillez la définir dans .env ou st.secrets")
        
        # Section de debug
        with st.expander("🔍 Debug - Informations de chargement"):
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
            st.write(f"**Chemin du fichier .env :** `{env_path}`")
            st.write(f"**Fichier .env existe :** {os.path.exists(env_path)}")
            
            if os.path.exists(env_path):
                st.write("**Contenu du fichier .env (masqué) :**")
                try:
                    with open(env_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        for i, line in enumerate(lines, 1):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                if 'PASSWORD' in key or 'API_KEY' in key:
                                    st.write(f"Ligne {i}: {key.strip()}=***")
                                else:
                                    st.write(f"Ligne {i}: {line.strip()}")
                except Exception as e:
                    st.write(f"Erreur lors de la lecture: {e}")
            
            st.write(f"**OPENAI_API_KEY chargée :** {bool(api_key)}")
            st.write(f"**USERNAME chargé :** {bool(get_secret('USERNAME'))}")
            st.write(f"**PASSWORD chargé :** {bool(get_secret('PASSWORD'))}")
            
            # Afficher toutes les variables d'environnement qui commencent par OPENAI, USERNAME ou PASSWORD
            st.write("**Variables d'environnement détectées :**")
            env_vars = {k: v for k, v in os.environ.items() if any(x in k for x in ['OPENAI', 'USERNAME', 'PASSWORD'])}
            for k, v in env_vars.items():
                if 'PASSWORD' in k or 'API_KEY' in k:
                    st.write(f"- {k}: ***")
                else:
                    st.write(f"- {k}: {v}")
        
        return
    
    # Charger automatiquement l'index s'il existe et n'est pas déjà chargé
    if st.session_state.vector_store is None:
        if os.path.exists(FAISS_PATH) and os.path.exists(os.path.join(FAISS_PATH, "index.faiss")):
            try:
                embeddings = get_embeddings()
                st.session_state.vector_store = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
                # Stocker l'erreur de chargement si elle existe
                if "index_load_error" in st.session_state:
                    del st.session_state["index_load_error"]
            except Exception as e:
                # Stocker l'erreur pour l'afficher dans la sidebar
                st.session_state["index_load_error"] = str(e)
    
    # Barre latérale
    with st.sidebar:
        st.title("🤖 Assistant RAG Mémoire")
        st.markdown("---")
        
        # Sélecteur de mode (Question / Rédaction)
        st.subheader("📝 Mode de réponse")
        mode_redaction = st.checkbox(
            "Mode Rédaction (format mémoire académique)",
            value=(st.session_state.mode == "redaction"),
            help="Cochez cette case pour obtenir des réponses formatées comme un chercheur dans un mémoire. Décochez pour des réponses normales."
        )
        
        # Mettre à jour le mode dans session_state
        if mode_redaction:
            st.session_state.mode = "redaction"
            st.info("✍️ Mode **Rédaction** activé : réponses prêtes à copier-coller dans votre mémoire")
        else:
            st.session_state.mode = "question"
            st.info("❓ Mode **Question** activé : réponses conversationnelles")
        
        st.markdown("---")
        
        # Afficher un message si l'index n'a pas pu être chargé
        if st.session_state.vector_store is None and os.path.exists(FAISS_PATH) and os.path.exists(os.path.join(FAISS_PATH, "index.faiss")):
            st.error("❌ Impossible de charger l'index existant")
            if "index_load_error" in st.session_state:
                with st.expander("🔍 Détails de l'erreur"):
                    st.text(st.session_state["index_load_error"])
            if st.button("🗑️ Supprimer l'index corrompu"):
                if os.path.exists(FAISS_PATH):
                    shutil.rmtree(FAISS_PATH)
                if "index_load_error" in st.session_state:
                    del st.session_state["index_load_error"]
                st.rerun()
        
        # Bouton d'indexation
        if st.button("📚 Indexer les documents", type="primary"):
            with st.spinner("Indexation en cours..."):
                vector_store = index_documents()
                if vector_store:
                    st.session_state.vector_store = vector_store
                    st.rerun()
        
        # Afficher le statut de l'index
        if st.session_state.vector_store:
            st.success("✅ Index disponible")
        else:
            st.warning("⚠️ Index non chargé. Cliquez sur 'Indexer les documents'.")
            # Debug: vérifier si le dossier existe
            if os.path.exists(FAISS_PATH):
                if os.path.exists(os.path.join(FAISS_PATH, "index.faiss")):
                    st.info("ℹ️ Index FAISS trouvé mais non chargé. Essayez de réindexer.")
                else:
                    st.info("ℹ️ Dossier index vide. Indexation nécessaire.")
        
        st.markdown("---")
        
        # Bouton de déconnexion
        if st.button("🚪 Se déconnecter"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Interface principale
    st.title("💬 Chatbot RAG - Assistant Mémoire")
    st.markdown("**Sujet :** Wokisme")
    st.markdown("---")
    
    # Plus besoin d'initialiser la chaîne QA, on utilise une approche directe
    
    # Afficher l'historique des messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Afficher les sources si disponibles
            if "sources" in message and message["sources"]:
                with st.expander("📚 Sources"):
                    for source in message["sources"]:
                        source_name = source.metadata.get("source", "Inconnu")
                        page = source.metadata.get("page", "N/A")
                        st.text(f"• {source_name} (Page {page})")
    
    # Entrée utilisateur
    if prompt := st.chat_input("Posez votre question sur le wokisme..."):
        # Vérifier que le vector store est disponible
        if st.session_state.vector_store is None:
            st.error("⚠️ Veuillez d'abord indexer les documents depuis la barre latérale.")
            return
        
        # Ajouter le message utilisateur à l'historique
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Afficher le message utilisateur
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Générer la réponse (approche directe et rapide)
        with st.chat_message("assistant"):
            with st.spinner("Réflexion en cours..."):
                try:
                    # Appel direct avec le mode sélectionné
                    answer, sources = generate_answer(
                        st.session_state.vector_store, 
                        prompt, 
                        mode=st.session_state.mode
                    )
                    
                    # Afficher la réponse
                    st.markdown(answer)
                    
                    # Afficher les sources
                    if sources:
                        with st.expander("📚 Sources utilisées"):
                            unique_sources = {}
                            for source in sources:
                                source_name = source.metadata.get("source", "Inconnu")
                                page = source.metadata.get("page", "N/A")
                                key = f"{source_name}_{page}"
                                if key not in unique_sources:
                                    unique_sources[key] = (source_name, page)
                            
                            for source_name, page in unique_sources.values():
                                st.text(f"• {source_name} (Page {page})")
                    
                    # Ajouter la réponse à l'historique
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })
                    
                except Exception as e:
                    error_msg = f"❌ Erreur lors de la génération de la réponse : {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })

# Point d'entrée
if __name__ == "__main__":
    main()

