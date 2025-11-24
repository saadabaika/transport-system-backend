from rest_framework import serializers
from gestion.models import *
import json


class TransporteurExterneSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransporteurExterne
        fields = '__all__'


class CamionSerializer(serializers.ModelSerializer):
    transporteur_externe_details = TransporteurExterneSerializer(source='transporteur_externe', read_only=True)
    
    class Meta:
        model = Camion
        fields = '__all__'

class EmployeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employe
        fields = '__all__'

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'

class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = '__all__'

class TrajetSerializer(serializers.ModelSerializer):
    camion_details = CamionSerializer(source='camion', read_only=True)
    chauffeur_details = EmployeSerializer(source='chauffeur', read_only=True)
    client_details = ClientSerializer(source='client', read_only=True)
    destination_details = DestinationSerializer(source='destination', read_only=True)
    transporteur_externe_details = TransporteurExterneSerializer(source='transporteur_externe', read_only=True)
    
    # Pour gérer les frais supplémentaires
    frais_supplementaires_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Trajet
        fields = '__all__'
        extra_kwargs = {
            'camion': {'required': False, 'allow_null': True},
            'chauffeur': {'required': False, 'allow_null': True},
        }
    
    def get_frais_supplementaires_list(self, obj):
        """Convertir le JSON des frais en liste pour le frontend"""
        if obj.frais_supplementaires and obj.frais_supplementaires != '{}':
            try:
                frais_dict = json.loads(obj.frais_supplementaires)
                return [{"nom": nom, "montant": float(montant)} for nom, montant in frais_dict.items()]
            except (json.JSONDecodeError, ValueError):
                return []
        return []
    
    def validate(self, data):
        """Validation conditionnelle selon le type de sous-traitance"""
        type_sous_traitance = data.get('type_sous_traitance', self.instance.type_sous_traitance if self.instance else 'interne')
        
        if type_sous_traitance in ['interne', 'je_recois']:
            # Pour interne et je reçois, camion et chauffeur sont obligatoires
            if not data.get('camion'):
                raise serializers.ValidationError({"camion": "Ce champ est obligatoire pour les trajets internes et 'Je reçois'."})
            if not data.get('chauffeur'):
                raise serializers.ValidationError({"chauffeur": "Ce champ est obligatoire pour les trajets internes et 'Je reçois'."})
        elif type_sous_traitance == 'je_donne':
            # Pour je donne, camion et chauffeur doivent être null
            data['camion'] = None
            data['chauffeur'] = None
            data['frais_deplacement'] = 0
            
        return data
    
    def to_internal_value(self, data):
        """Convertir la liste des frais en JSON pour la sauvegarde"""
        # Faire une copie pour éviter de modifier les données originales
        data = data.copy()
        
        if 'frais_supplementaires_list' in data:
            frais_list = data.get('frais_supplementaires_list', [])
            frais_dict = {}
            
            # Si c'est une string (venant du frontend), la parser
            if isinstance(frais_list, str):
                try:
                    frais_list = json.loads(frais_list)
                except json.JSONDecodeError:
                    frais_list = []
            
            for frais in frais_list:
                if isinstance(frais, dict) and frais.get('nom') and frais.get('montant') is not None:
                    try:
                        frais_dict[frais['nom']] = float(frais['montant'])
                    except (ValueError, TypeError):
                        continue
            
            data['frais_supplementaires'] = json.dumps(frais_dict)
        
        return super().to_internal_value(data)
    
    def create(self, validated_data):
        # S'assurer que les valeurs par défaut sont correctes
        validated_data.setdefault('frais_supplementaires', '{}')
        validated_data.setdefault('total_frais_supplementaires', 0)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data.setdefault('frais_supplementaires', instance.frais_supplementaires)
        return super().update(instance, validated_data)

class PaiementSousTraitanceSerializer(serializers.ModelSerializer):
    trajet_details = TrajetSerializer(source='trajet', read_only=True)
    transporteur_externe_details = TransporteurExterneSerializer(source='transporteur_externe', read_only=True)
    
    class Meta:
        model = PaiementSousTraitance
        fields = '__all__'

class LigneFactureSerializer(serializers.ModelSerializer):
    # ⭐ SUPPRIMEZ la référence à destination ⭐
    class Meta:
        model = LigneFacture
        fields = '__all__'

class FactureSerializer(serializers.ModelSerializer):
    client_details = ClientSerializer(source='client', read_only=True)
    lignes = LigneFactureSerializer(many=True, read_only=True)
    
    class Meta:
        model = Facture
        fields = '__all__'
        read_only_fields = ('numero_facture', 'created_at', 'updated_at')

class FactureCreateSerializer(serializers.ModelSerializer):
    lignes_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        default=list
    )
    
    class Meta:
        model = Facture
        fields = '__all__'
        read_only_fields = ('numero_facture', 'created_at', 'updated_at')

    def create(self, validated_data):
        lignes_data = validated_data.pop('lignes_data', [])
        facture = Facture.objects.create(**validated_data)
        
        for ordre, ligne_data in enumerate(lignes_data):
            # ⭐ NOUVELLE STRUCTURE SANS DESTINATION ⭐
            LigneFacture.objects.create(
                facture=facture,
                description=ligne_data.get('description', ''),
                quantite=ligne_data.get('quantite', 1),
                prix_unitaire=ligne_data.get('prix_unitaire', 0),
                tva=ligne_data.get('tva', 20.00),  # ⭐ AJOUT DU CHAMP TVA ⭐
                ordre=ordre
            )
        
        facture.calculer_totaux()
        return facture

    def update(self, instance, validated_data):
        lignes_data = validated_data.pop('lignes_data', None)
        
        # Mettre à jour les champs de la facture
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if lignes_data is not None:
            instance.lignes.all().delete()
            
            for ordre, ligne_data in enumerate(lignes_data):
                LigneFacture.objects.create(
                    facture=instance,
                    description=ligne_data.get('description', ''),
                    quantite=ligne_data.get('quantite', 1),
                    prix_unitaire=ligne_data.get('prix_unitaire', 0),
                    tva=ligne_data.get('tva', 20.00),  # ⭐ AJOUT DU CHAMP TVA ⭐
                    ordre=ordre
                )
        
        instance.calculer_totaux()
        return instance
    
class ChargeCamionSerializer(serializers.ModelSerializer):
    camion_details = CamionSerializer(source='camion', read_only=True)
    montant_mensuel = serializers.SerializerMethodField()
    
    class Meta:
        model = ChargeCamion
        fields = '__all__'
    
    def get_montant_mensuel(self, obj):
        """Retourne le montant mensuel pour les charges annuelles"""
        if obj.type_charge == 'annuelle':
            return obj.montant / 12
        return obj.montant
    
    def validate(self, data):
        type_charge = data.get('type_charge')
        categorie = data.get('categorie')
        
        # Validation pour le gazoil
        if categorie == 'gazoil':
            if not data.get('litres'):
                raise serializers.ValidationError({"litres": "Le nombre de litres est obligatoire pour le gazoil."})
            if not data.get('kilometrage'):
                raise serializers.ValidationError({"kilometrage": "Le kilométrage est obligatoire pour le gazoil."})
        
        # Pour les charges annuelles, dates début/fin sont requises
        if type_charge == 'annuelle':
            if not data.get('date_debut'):
                raise serializers.ValidationError({"date_debut": "La date de début est obligatoire pour les charges annuelles."})
            if not data.get('date_fin'):
                raise serializers.ValidationError({"date_fin": "La date de fin est obligatoire pour les charges annuelles."})
            
            if data['date_debut'] > data['date_fin']:
                raise serializers.ValidationError({"date_fin": "La date de fin doit être postérieure à la date de début."})
        
        # Pour les charges mensuelles, pas de dates début/fin
        if type_charge == 'mensuelle':
            data['date_debut'] = None
            data['date_fin'] = None
            data['statut'] = ''
        
        return data
    
from django.contrib.auth import authenticate
from rest_framework import serializers
from gestion.models import User
from django.utils import timezone

class UserSerializer(serializers.ModelSerializer):
    last_login_display = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'telephone', 'date_embauche', 'statut', 'last_login', 'last_login_display']
        read_only_fields = ['id', 'last_login', 'last_login_display']

    def get_last_login_display(self, obj):
        if obj.last_login:
            return obj.last_login.strftime('%d/%m/%Y %H:%M')
        return 'Jamais connecté'

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'telephone', 'date_embauche', 'password', 'confirm_password']

    def validate(self, data):
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Les mots de passe ne correspondent pas."})
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'telephone', 'date_embauche', 'statut']

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_new_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "Les nouveaux mots de passe ne correspondent pas."})
        return data

class AdminChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    confirm_new_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "Les nouveaux mots de passe ne correspondent pas."})
        return data

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    data['user'] = user
                else:
                    raise serializers.ValidationError('Compte utilisateur désactivé.')
            else:
                raise serializers.ValidationError('Identifiants invalides.')
        else:
            raise serializers.ValidationError('Must include username and password.')
        
        return data
    
from rest_framework import serializers
from gestion.models import OperationTVA, DeclarationTVA

class OperationTVASerializer(serializers.ModelSerializer):
    entreprise_display = serializers.CharField(source='get_entreprise_display', read_only=True)
    type_operation_display = serializers.CharField(source='get_type_operation_display', read_only=True)
    categorie_display = serializers.CharField(source='get_categorie_display', read_only=True)
    statut_tva_display = serializers.CharField(source='get_statut_tva_display', read_only=True)
    
    class Meta:
        model = OperationTVA
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by')

class OperationTVACreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationTVA
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'created_by')

    def validate(self, data):
        # Validation des dates
        if data['date_operation'] > timezone.now().date():
            raise serializers.ValidationError("La date d'opération ne peut pas être dans le futur")
        
        if data['date_valeur'] > timezone.now().date():
            raise serializers.ValidationError("La date de valeur ne peut pas être dans le futur")
            
        return data
    
from rest_framework import serializers
from gestion.models import OperationTVA, DeclarationTVA


class DeclarationTVASerializer(serializers.ModelSerializer):
    entreprise_display = serializers.CharField(source='get_entreprise_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    
    class Meta:
        model = DeclarationTVA
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class CalculDeclarationTVASerializer(serializers.Serializer):
    entreprise = serializers.ChoiceField(choices=OperationTVA.TYPE_ENTREPRISE)
    mois = serializers.IntegerField(min_value=1, max_value=12)
    annee = serializers.IntegerField(min_value=2020, max_value=2030)