import json
import os

print("🎯 EXTRACTION MANUELLE DES DONNÉES MÉTIER")

# Lire le fichier
with open('cleaned_sqlite_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Liste COMPLÈTE des modèles à EXCLURE (tables système)
exclude_models = [
    'contenttypes.contenttype',
    'auth.permission',
    'auth.group', 
    'auth.user',
    'sessions.session',
    'admin.logentry',
    'authtoken.token',
    'authtoken.tokenproxy'
]

# Garder TOUT SAUF les tables système
business_data = [item for item in data if item['model'] not in exclude_models]

print(f"📊 {len(business_data)} objets métier à charger (sur {len(data)} total)")

# Compter par modèle
from collections import Counter
model_counts = Counter(item['model'] for item in business_data)
print("📋 DÉTAIL DES DONNÉES:")
for model, count in model_counts.items():
    print(f"   {model}: {count}")

# Sauvegarder
with open('pure_business.json', 'w', encoding='utf-8') as f:
    json.dump(business_data, f, indent=2, ensure_ascii=False)

print("✅ Fichier pure_business.json créé")

# Charger
print("📥 Chargement des données...")
os.system('python manage.py loaddata pure_business.json')

print("🎉 CHARGEMENT TERMINÉ!")