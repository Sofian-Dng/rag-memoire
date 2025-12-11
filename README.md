# 🤖 Assistant RAG Mémoire - Wokisme

Application Streamlit de chatbot RAG (Retrieval-Augmented Generation) pour assister la rédaction d'un mémoire académique sur le wokisme.

## ✨ Fonctionnalités

- 🔐 **Authentification par mot de passe**
- 📚 **Indexation de documents PDF** avec FAISS
- 💬 **Chatbot conversationnel** avec GPT-4
- ✍️ **Deux modes de réponse** :
  - **Mode Question** : Réponses conversationnelles développées
  - **Mode Rédaction** : Textes formatés prêts à être intégrés dans un mémoire académique
- 📖 **Citations automatiques** des sources PDF

## 🚀 Installation locale

1. **Cloner le repository** :
   ```bash
   git clone https://github.com/VOTRE_USERNAME/rag-memoire.git
   cd rag-memoire
   ```

2. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurer les variables d'environnement** :
   Créez un fichier `.env` à la racine du projet :
   ```env
   OPENAI_API_KEY=votre-clef-openai
   USERNAME=admin
   PASSWORD=votre-mot-de-passe
   ```

4. **Ajouter vos PDFs** :
   Placez vos fichiers PDF dans le dossier `data/`

5. **Lancer l'application** :
   ```bash
   python -m streamlit run app.py
   ```

## 📖 Utilisation

1. **Se connecter** avec les identifiants configurés
2. **Indexer les documents** : Cliquez sur "📚 Indexer les documents" dans la sidebar
3. **Choisir le mode** :
   - Décocher = Mode Question (réponses normales)
   - Cocher = Mode Rédaction (format mémoire)
4. **Poser vos questions** dans le chat

## 🌐 Déploiement en ligne

Voir le fichier `DEPLOYMENT.md` pour les instructions complètes de déploiement sur Streamlit Community Cloud.

## 📝 Structure du projet

```
rag-memoire/
├── app.py                 # Application principale
├── requirements.txt       # Dépendances Python
├── .env                   # Variables d'environnement (local)
├── .gitignore            # Fichiers à ignorer
├── data/                 # Dossier contenant les PDFs
├── faiss_index/          # Index vectoriel (généré automatiquement)
└── README.md             # Ce fichier
```

## 🔧 Technologies utilisées

- **Streamlit** : Interface web
- **LangChain** : Framework RAG
- **FAISS** : Base de données vectorielle
- **OpenAI GPT-4** : Modèle de langage
- **Sentence Transformers** : Embeddings locaux

## ⚠️ Notes importantes

- L'indexation peut prendre quelques minutes selon le nombre de PDFs
- Les réponses utilisent jusqu'à 10 segments de documents pour le contexte
- Le mode Rédaction génère des textes prêts à copier-coller dans votre mémoire

## 📄 Licence

Ce projet est destiné à un usage académique personnel.

