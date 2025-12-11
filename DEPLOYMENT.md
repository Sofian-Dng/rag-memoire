# 🚀 Guide de Déploiement - Application RAG Mémoire

## Option 1 : Streamlit Community Cloud (Recommandé - Gratuit)

### Étape 1 : Préparer votre code sur GitHub

1. **Créer un compte GitHub** (si vous n'en avez pas) : https://github.com

2. **Créer un nouveau repository** :
   - Allez sur GitHub
   - Cliquez sur "New repository"
   - Nommez-le (ex: `rag-memoire`)
   - Choisissez "Public" ou "Private"
   - **Ne cochez PAS** "Initialize with README" (vous avez déjà des fichiers)

3. **Initialiser Git et pousser votre code** :
   ```bash
   # Dans le terminal, depuis votre dossier "rag memoire"
   git init
   git add app.py requirements.txt .gitignore
   git commit -m "Initial commit - RAG Mémoire app"
   git branch -M main
   git remote add origin https://github.com/VOTRE_USERNAME/rag-memoire.git
   git push -u origin main
   ```

### Étape 2 : Déployer sur Streamlit Community Cloud

1. **Créer un compte Streamlit** :
   - Allez sur https://share.streamlit.io/
   - Cliquez sur "Sign up" et connectez-vous avec votre compte GitHub

2. **Déployer l'application** :
   - Cliquez sur "New app"
   - Sélectionnez votre repository GitHub (`rag-memoire`)
   - **Main file path** : `app.py`
   - **App URL** : choisissez un nom (ex: `rag-memoire-wokisme`)
   - Cliquez sur "Deploy"

3. **Configurer les secrets** :
   - Une fois déployé, allez dans "Settings" → "Secrets"
   - Ajoutez vos secrets au format TOML :
     ```toml
     OPENAI_API_KEY = "votre-clef-openai"
     USERNAME = "admin"
     PASSWORD = "votre-mot-de-passe"
     ```
   - Cliquez sur "Save"

4. **Redéployer** :
   - L'application redémarre automatiquement avec les nouveaux secrets

### ⚠️ Important pour le déploiement

- **Les fichiers PDF** : Vous devrez les ajouter au repository GitHub ou utiliser un stockage cloud (S3, etc.)
- **L'index FAISS** : Ne sera pas dans le repo (dans .gitignore). L'utilisateur devra réindexer les documents après le déploiement
- **Limite de taille** : Streamlit Community Cloud a une limite de 1GB par app

---

## Option 2 : Render.com (Alternative gratuite)

1. **Créer un compte** : https://render.com
2. **Connecter votre repo GitHub**
3. **Créer un nouveau "Web Service"**
4. **Configuration** :
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
5. **Ajouter les variables d'environnement** dans "Environment" :
   - `OPENAI_API_KEY`
   - `USERNAME`
   - `PASSWORD`

---

## Option 3 : Railway.app (Alternative gratuite)

1. **Créer un compte** : https://railway.app
2. **Connecter votre repo GitHub**
3. **Créer un nouveau projet**
4. **Ajouter les variables d'environnement** dans "Variables"

---

## 📝 Notes importantes

### Pour que votre collègue puisse utiliser l'app :

1. **Partagez l'URL** de l'application déployée
2. **Donnez-lui les identifiants** (USERNAME et PASSWORD)
3. **Expliquez-lui** qu'il devra :
   - Se connecter avec les identifiants
   - Cliquer sur "Indexer les documents" pour créer l'index
   - Attendre la fin de l'indexation (peut prendre quelques minutes)

### Fichiers à inclure dans le repository :

✅ **À inclure** :
- `app.py`
- `requirements.txt`
- `.gitignore`
- `data/` (dossier avec les PDFs) - **OU** utilisez un stockage cloud séparé

❌ **À NE PAS inclure** (dans .gitignore) :
- `.env`
- `faiss_index/`
- `chroma_db/`

---

## 🔧 Dépannage

### Si l'app ne démarre pas :
- Vérifiez que tous les secrets sont bien configurés
- Vérifiez les logs dans Streamlit Community Cloud
- Assurez-vous que `requirements.txt` est à jour

### Si l'indexation échoue :
- Vérifiez que les PDFs sont bien dans le dossier `data/`
- Vérifiez les logs pour voir les erreurs

---

## 🎯 Recommandation finale

**Utilisez Streamlit Community Cloud** car :
- ✅ Gratuit
- ✅ Spécialement conçu pour Streamlit
- ✅ Configuration simple
- ✅ Gestion automatique des secrets
- ✅ Déploiement en quelques clics

