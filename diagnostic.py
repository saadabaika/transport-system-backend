# debug_serializers.py
import os
import django
import sys

sys.path.append('C:/Users/saad/Desktop/transport-backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

print("=== DÉBOGAGE SÉRIALISEURS ===")

from gestion.models import Facture
from api.serializers import FactureSerializer
import json

try:
    # Récupérer les factures
    factures = Facture.objects.all()
    print(f"Factures en base: {factures.count()}")
    
    # Test de sérialisation simple
    print("\n1. Test sérialisation simple:")
    for facture in factures[:2]:
        print(f"Facture {facture.id}: {facture.numero_facture}")
        serializer = FactureSerializer(facture)
        print(f"  ✓ Sérialisation unitaire OK")
    
    # Test sérialisation multiple
    print("\n2. Test sérialisation multiple:")
    serializer = FactureSerializer(factures, many=True)
    print(f"  ✓ Sérialisation multiple OK")
    
    # Test conversion JSON
    print("\n3. Test conversion JSON:")
    try:
        json_data = json.dumps(serializer.data, ensure_ascii=False)
        print(f"  ✓ Conversion JSON réussie")
        print(f"  Taille: {len(json_data)} caractères")
    except Exception as e:
        print(f"  ✗ Erreur JSON: {e}")
        # Afficher les données problématiques
        for i, facture_data in enumerate(serializer.data):
            try:
                json.dumps(facture_data)
                print(f"    Facture {i}: OK")
            except Exception as e2:
                print(f"    Facture {i}: ERREUR - {e2}")
                print(f"      Données: {facture_data}")
                
except Exception as e:
    print(f"✗ Erreur: {e}")
    import traceback
    traceback.print_exc()