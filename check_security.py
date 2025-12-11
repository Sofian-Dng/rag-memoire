#!/usr/bin/env python3
"""
Script de vérification de sécurité avant le push Git
Vérifie qu'aucune clé API ou mot de passe n'est exposé
"""

import os
import re
import sys

# Patterns pour détecter les clés API
PATTERNS = [
    r'sk-[a-zA-Z0-9]{20,}',  # OpenAI API key
    r'AIza[a-zA-Z0-9_-]{35}',  # Google API key
    r'ghp_[a-zA-Z0-9]{36}',  # GitHub token
    r'xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,32}',  # Slack token
]

# Fichiers à vérifier
FILES_TO_CHECK = ['app.py', 'requirements.txt', 'README.md', 'DEPLOYMENT.md']

# Fichiers à ignorer (déjà dans .gitignore)
IGNORED_FILES = ['.env', '.git', '__pycache__', 'faiss_index', 'chroma_db']

def check_file(filepath):
    """Vérifie un fichier pour des clés API potentielles"""
    if not os.path.exists(filepath):
        return True, []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        issues = []
        for i, line in enumerate(content.split('\n'), 1):
            for pattern in PATTERNS:
                if re.search(pattern, line):
                    issues.append(f"Ligne {i}: Possible clé API détectée")
        
        return len(issues) == 0, issues
    except Exception as e:
        return False, [f"Erreur lors de la lecture: {e}"]

def check_gitignore():
    """Vérifie que .gitignore contient .env"""
    if not os.path.exists('.gitignore'):
        return False, ".gitignore n'existe pas"
    
    with open('.gitignore', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '.env' in content:
        return True, ".env est bien dans .gitignore"
    else:
        return False, ".env n'est PAS dans .gitignore"

def check_env_file():
    """Vérifie si .env existe et s'il serait tracké"""
    if os.path.exists('.env'):
        return True, ".env existe (c'est normal, il sera ignoré par git)"
    else:
        return True, ".env n'existe pas (c'est OK)"

def main():
    print("🔒 Vérification de sécurité avant le push Git\n")
    print("=" * 50)
    
    all_ok = True
    
    # Vérifier .gitignore
    print("\n1. Vérification de .gitignore...")
    ok, msg = check_gitignore()
    if ok:
        print(f"   ✅ {msg}")
    else:
        print(f"   ❌ {msg}")
        all_ok = False
    
    # Vérifier .env
    print("\n2. Vérification du fichier .env...")
    ok, msg = check_env_file()
    print(f"   ℹ️  {msg}")
    
    # Vérifier les fichiers pour des clés API
    print("\n3. Vérification des fichiers pour des clés API...")
    for filepath in FILES_TO_CHECK:
        if os.path.exists(filepath):
            ok, issues = check_file(filepath)
            if ok:
                print(f"   ✅ {filepath}: Aucune clé API détectée")
            else:
                print(f"   ❌ {filepath}: Problèmes détectés:")
                for issue in issues:
                    print(f"      - {issue}")
                all_ok = False
        else:
            print(f"   ⚠️  {filepath}: Fichier non trouvé (ignoré)")
    
    # Résumé
    print("\n" + "=" * 50)
    if all_ok:
        print("✅ TOUT EST SÉCURISÉ ! Vous pouvez pousser sur GitHub en toute sécurité.")
        print("\n📝 Rappel: Les secrets doivent être configurés dans Streamlit Secrets")
        print("   lors du déploiement, pas dans le code.")
        return 0
    else:
        print("❌ PROBLÈMES DÉTECTÉS ! Ne poussez PAS avant de corriger.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

