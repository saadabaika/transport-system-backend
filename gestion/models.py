from django.db import models
from django.utils import timezone
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal


class TransporteurExterne(models.Model):
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
    ]
    
    nom = models.CharField(max_length=200)
    ice = models.CharField(max_length=20, unique=True)
    telephone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    adresse = models.TextField(blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif')
    
    def __str__(self):
        return f"{self.nom} (ICE: {self.ice})"

class Camion(models.Model):
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('inactif', 'Inactif'),
        ('maintenance', 'En Maintenance'),
    ]
    
    TYPE_PROPRIETE = [
        ('interne', 'Interne'),
        ('externe', 'Externe'),
    ]
    
    immatriculation = models.CharField(max_length=20, unique=True)
    marque = models.CharField(max_length=50)
    modele = models.CharField(max_length=50)
    date_mise_service = models.DateField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif')
    type_propriete = models.CharField(max_length=20, choices=TYPE_PROPRIETE, default='interne')
    transporteur_externe = models.ForeignKey(TransporteurExterne, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        propriete = "Interne" if self.type_propriete == 'interne' else f"Externe - {self.transporteur_externe.nom}"
        return f"{self.immatriculation} - {self.marque} {self.modele} ({propriete})"

class Employe(models.Model):
    TYPE_EMPLOYE = [
        ('chauffeur', 'Chauffeur'),
        ('salarie', 'Salarié'),
        ('gerant', 'Gérant'),
    ]
    
    type_employe = models.CharField(max_length=20, choices=TYPE_EMPLOYE)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, blank=True)
    salaire_base = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, default='actif')
    date_embauche = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.type_employe})"

class Client(models.Model):
    nom = models.CharField(max_length=200)
    ice = models.CharField(max_length=20, unique=True)
    adresse = models.TextField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    def __str__(self):
        return self.nom

class Destination(models.Model):
    ville = models.CharField(max_length=100)
    frais_deplacement = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.ville} ({self.frais_deplacement} DH)"

class Trajet(models.Model):
    TYPE_TRAJET = [
        ('facture', 'Facturé'),
        ('non_facture', 'Non Facturé'),
    ]
    
    TYPE_SERVICE = [
        ('ars_distribution', 'ARS Distribution'),
        ('arn_logistique', 'ARN Logistique'),
        ('sous_traitance', 'Sous-traitance'),
    ]
    
    STATUT_PAIEMENT_FRAIS = [
        ('paye', 'Payé'),
        ('non_paye', 'Non Payé'),
        ('partiel', 'Partiel'),
    ]
    
    TYPE_SOUS_TRAITANCE = [
        ('je_donne', 'Je donne à un transporteur'),
        ('je_recois', 'Je reçois d\'un transporteur'),
        ('interne', 'Trajet interne'),
    ]
    
    date = models.DateField()
    camion = models.ForeignKey(Camion, on_delete=models.CASCADE, null=True, blank=True)
    chauffeur = models.ForeignKey(Employe, on_delete=models.CASCADE, null=True, blank=True, limit_choices_to={'type_employe': 'chauffeur'})
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE)
    n_conteneurs = models.IntegerField(default=1)
    numeros_conteneurs = models.CharField(max_length=500, blank=True)
    prix_trajet = models.DecimalField(max_digits=10, decimal_places=2)
    frais_deplacement = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    type_trajet = models.CharField(max_length=20, choices=TYPE_TRAJET, default='facture')
    type_service = models.CharField(max_length=20, choices=TYPE_SERVICE, default='ars_distribution')
    type_sous_traitance = models.CharField(max_length=20, choices=TYPE_SOUS_TRAITANCE, default='interne')
    
    # Champs pour la sous-traitance
    transporteur_externe = models.ForeignKey(TransporteurExterne, on_delete=models.SET_NULL, null=True, blank=True)
    prix_sous_traitance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    statut_paiement_sous_traitance = models.CharField(max_length=20, choices=STATUT_PAIEMENT_FRAIS, default='non_paye')
    
    # Champs existants
    frais_supplementaires = models.CharField(max_length=1000, blank=True, default='{}')
    total_frais_supplementaires = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    statut_paiement_frais = models.CharField(max_length=20, choices=STATUT_PAIEMENT_FRAIS, default='non_paye')
    remarques = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        # POUR LES TRAJETS "JE DONNE" : Forcer camion, chauffeur et frais à null/0
        if self.type_sous_traitance == 'je_donne':
            self.camion = None
            self.chauffeur = None
            self.frais_deplacement = 0
        
        # Calcul automatique du total des frais supplémentaires
        import json
        if self.frais_supplementaires and self.frais_supplementaires != '{}':
            try:
                frais_dict = json.loads(self.frais_supplementaires)
                total = sum(float(montant) for montant in frais_dict.values())
                self.total_frais_supplementaires = total
            except (json.JSONDecodeError, ValueError):
                self.total_frais_supplementaires = 0
        else:
            self.total_frais_supplementaires = 0
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        type_trajet = "Interne" if self.type_sous_traitance == 'interne' else self.type_sous_traitance
        return f"Trajet {self.id} - {self.client} vers {self.destination} ({type_trajet})"

class PaiementSousTraitance(models.Model):
    STATUT_PAIEMENT = [
        ('paye', 'Payé'),
        ('en_attente', 'En attente'),
        ('annule', 'Annulé'),
    ]
    
    trajet = models.ForeignKey(Trajet, on_delete=models.CASCADE)
    transporteur_externe = models.ForeignKey(TransporteurExterne, on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_paiement = models.DateField(null=True, blank=True)
    date_echeance = models.DateField()
    statut = models.CharField(max_length=20, choices=STATUT_PAIEMENT, default='en_attente')
    reference = models.CharField(max_length=100, blank=True)
    remarques = models.TextField(blank=True)
    
    def __str__(self):
        return f"Paiement {self.id} - {self.transporteur_externe.nom} - {self.montant} DH"
    
from django.db import models
from django.db.models import Sum
from datetime import datetime

class Facture(models.Model):
    TYPE_ENTREPRISE = [
        ('ars_distribution', 'ARS Distribution'),
        ('arn_logistique', 'ARN Logistique'),
    ]
    
    STATUT_FACTURE = [
        ('brouillon', 'Brouillon'),
        ('envoyee', 'Envoyée'),
        ('payee', 'Payée'),
        ('annulee', 'Annulée'),
    ]

    numero_facture = models.CharField(max_length=50, unique=True, editable=False)
    entreprise = models.CharField(max_length=20, choices=TYPE_ENTREPRISE)
    client = models.ForeignKey('Client', on_delete=models.CASCADE)
    date_facture = models.DateField()
    date_echeance = models.DateField()
    # ⭐ SUPPRIMEZ le champ TVA global ⭐
    statut = models.CharField(max_length=20, choices=STATUT_FACTURE, default='brouillon')
    conditions_paiement = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    total_ht = models.DecimalField(max_digits=15, decimal_places=2, default=0)       # ⭐ 12 → 15
    total_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=0)      # ⭐ 12 → 15
    montant_tva = models.DecimalField(max_digits=15, decimal_places=2, default=0)    # ⭐ 12 → 15
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.numero_facture:
            prefix = 'ARS' if self.entreprise == 'ars_distribution' else 'ARN'
            now = datetime.now()
            date_part = f"{now.year}-{now.month:02d}"
            
            # Trouver le PLUS GRAND numéro existant pour ce mois
            factures_existantes = Facture.objects.filter(
                numero_facture__startswith=f"{prefix}-{date_part}"
            )
            
            max_numero = 0
            for facture in factures_existantes:
                try:
                    numero_actuel = int(facture.numero_facture.split('-')[-1])
                    if numero_actuel > max_numero:
                        max_numero = numero_actuel
                except (ValueError, IndexError):
                    continue
            
            nouveau_numero = max_numero + 1
            self.numero_facture = f"{prefix}-{date_part}-{nouveau_numero:04d}"
        
        # Sauvegarder d'abord
        super().save(*args, **kwargs)
        
        # Calculer les totaux APRÈS la sauvegarde
        if self.pk and hasattr(self, 'lignes'):
            self.calculer_totaux()

    def calculer_totaux(self):
        from decimal import Decimal, InvalidOperation
        
        total_ht = Decimal('0')
        total_tva = Decimal('0')
        total_ttc = Decimal('0')
        
        for ligne in self.lignes.all():
            try:
                # ⭐ MÉTHODE SÉCURISÉE POUR CHAQUE CHAMP
                def safe_decimal_convert(value):
                    if value is None:
                        return Decimal('0')
                    try:
                        # Convertir en string puis en Decimal
                        return Decimal(str(value))
                    except (InvalidOperation, ValueError, TypeError):
                        return Decimal('0')
                
                # ⭐ CONVERSION SÉCURISÉE
                montant_ht = safe_decimal_convert(ligne.montant_ht)
                montant_tva = safe_decimal_convert(ligne.montant_tva)
                montant_ttc = safe_decimal_convert(ligne.montant_ttc)
                
                # ⭐ AJOUT AUX TOTAUX
                total_ht += montant_ht
                total_tva += montant_tva
                total_ttc += montant_ttc
                
            except Exception as e:
                print(f"⚠️ Erreur avec ligne facture {ligne.id}: {e}")
                continue
        
        # ⭐ MISE À JOUR DE LA FACTURE
        try:
            Facture.objects.filter(id=self.id).update(
                total_ht=total_ht,
                montant_tva=total_tva,
                total_ttc=total_ttc
            )
            
            # ⭐ RECHARGEMENT
            self.refresh_from_db()
            
        except Exception as e:
            print(f"❌ Erreur mise à jour facture {self.id}: {e}")

    def __str__(self):
        return f"Facture {self.numero_facture} - {self.client.nom}"

class LigneFacture(models.Model):
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='lignes')
    description = models.CharField(max_length=255)
    quantite = models.IntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # ⭐ 10 → 15
    tva = models.DecimalField(max_digits=5, decimal_places=2, default=20.00)
    montant_ht = models.DecimalField(max_digits=15, decimal_places=2, default=0)     # ⭐ 10 → 15
    montant_tva = models.DecimalField(max_digits=15, decimal_places=2, default=0)    # ⭐ 10 → 15
    montant_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=0)    # ⭐ 10 → 15
    ordre = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordre']

    def save(self, *args, **kwargs):
        from decimal import Decimal, InvalidOperation
        
        try:
            # Calcul du montant HT avec conversion sécurisée
            quantite_decimal = Decimal(str(self.quantite))
            prix_unitaire_decimal = Decimal(str(self.prix_unitaire))
            tva_decimal = Decimal(str(self.tva))
            
            self.montant_ht = quantite_decimal * prix_unitaire_decimal
            
            # Calcul TVA par ligne
            self.montant_tva = self.montant_ht * (tva_decimal / Decimal('100'))
            self.montant_ttc = self.montant_ht + self.montant_tva
            
        except (InvalidOperation, ValueError) as e:
            # Valeurs par défaut en cas d'erreur
            self.montant_ht = Decimal('0')
            self.montant_tva = Decimal('0')
            self.montant_ttc = Decimal('0')
            print(f"Erreur calcul ligne facture: {e}")
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ligne {self.ordre} - {self.description}"
    
from django.db import models
from django.utils import timezone
from datetime import datetime

class ChargeCamion(models.Model):
    TYPE_CHARGE = [
        ('mensuelle', 'Mensuelle'),
        ('annuelle', 'Annuelle'),
        ('occasionnelle', 'Occasionnelle'),
    ]
    
    CATEGORIE_CHARGE = [
        # Charges fixes annuelles
        ('assurance', 'Assurance'),
        ('vignette', 'Vignette'),
        ('visite_technique', 'Visite Technique'),
        ('tachygraphe', 'Tachygraphe'),
        ('extincteurs', 'Extincteurs'),
        
        # Charges variables mensuelles
        ('gazoil', 'Gazoil'),
        ('jawaz_autoroute', 'Jawaz Autoroute'),
        ('reparation', 'Réparation'),
        ('entretien', 'Entretien'),
        ('vidange', 'Vidange'),
        ('nettoyage', 'Nettoyage'),
        ('pneumatiques', 'Pneumatiques'),
        ('autre', 'Autre'),
    ]
    
    camion = models.ForeignKey(Camion, on_delete=models.CASCADE, related_name='charges')
    type_charge = models.CharField(max_length=20, choices=TYPE_CHARGE)
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHARGE)
    description = models.TextField(blank=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Champs spécifiques pour le gazoil
    litres = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    kilometrage = models.IntegerField(null=True, blank=True)
    prix_litre = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    
    # Date de la charge
    date_charge = models.DateField()
    
    # Pour les charges annuelles uniquement
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('expiree', 'Expirée'),
        ('renouvellee', 'Renouvelée'),
    ], default='active', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_charge', '-created_at']
    
    def save(self, *args, **kwargs):
        # Pour les charges mensuelles, pas de statut ni dates début/fin
        if self.type_charge == 'mensuelle':
            self.statut = ''
            self.date_debut = None
            self.date_fin = None
            
        # Calcul automatique du prix au litre pour le gazoil
        if self.categorie == 'gazoil' and self.litres and self.montant and self.litres > 0:
            self.prix_litre = self.montant / self.litres
            
        # Mettre à jour automatiquement le statut si date_fin est dépassée (uniquement pour annuelles)
        if self.type_charge == 'annuelle' and self.date_fin and self.date_fin < timezone.now().date():
            self.statut = 'expiree'
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_categorie_display()} - {self.camion.immatriculation} - {self.montant} DH"
    
    @property
    def periode_mois(self):
        return self.date_charge.month
    
    @property
    def periode_annee(self):
        return self.date_charge.year
    
from django.contrib.auth.models import AbstractUser
from django.db import models

from django.contrib.auth.models import AbstractUser
from django.db import models
import json

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('employe', 'Employé'),
        ('facturation', 'Agent Facturation'),  # ⭐ NOUVEAU RÔLE
    ]
    
    STATUT_CHOICES = [
        ('actif', 'Actif'),
        ('bloque', 'Bloqué'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employe')
    telephone = models.CharField(max_length=20, blank=True)
    date_embauche = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='actif')
    
    # SUPPRIMEZ le champ permissions
    # permissions = models.TextField(default='{}', blank=True)
    
    # Gardez les related_name personnalisés
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="gestion_user_set",
        related_query_name="gestion_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="gestion_user_set",
        related_query_name="gestion_user",
    )
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_employe(self):
        return self.role == 'employe'
    def is_facturation(self):  # ⭐ NOUVELLE MÉTHODE
        return self.role == 'facturation'
    
    # SUPPRIMEZ toutes les méthodes de permissions
    

class OperationTVA(models.Model):
    TYPE_ENTREPRISE = [
        ('arn_logistique', 'ARN Logistique'),
        ('ars_distribution', 'ARS Distribution'),
    ]
    
    TYPE_OPERATION = [
        ('debit', 'Débit'),
        ('credit', 'Crédit'),
    ]
    
    # ⭐⭐ CORRECTION : AJOUTEZ TOUTES LES CATÉGORIES DU FRONTEND ⭐⭐
    CATEGORIE_OPERATION = [
        ('vente_client', 'Vente Client'),
        ('achat_fournisseur', 'Achat Fournisseur'),
        ('carburant', 'Carburant'),
        ('entretien_vehicule', 'Entretien Véhicule'),
        ('reparation_vehicule', 'Réparation Véhicule'),
        ('assurance_vehicule', 'Assurance Véhicule'),
        ('vignette_vehicule', 'Vignette Véhicule'),
        ('controle_technique', 'Contrôle Technique'),
        ('salaires', 'Salaires et Charges Sociales'),
        ('loyer_bureau', 'Loyer Bureau'),
        ('charges_locatives', 'Charges Locatives'),
        ('electricite_eau', 'Électricité et Eau'),
        ('telecom_internet', 'Télécommunications et Internet'),
        ('fournitures_bureau', 'Fournitures Bureau'),
        ('materiel_informatique', 'Matériel Informatique'),
        ('frais_bancaires', 'Frais Bancaires'),
        ('honoraires_comptable', 'Honoraires Comptable'),
        ('honoraires_avocat', 'Honoraires Avocat'),
        ('publicite_marketing', 'Publicité et Marketing'),
        ('voyage_deplacement', 'Voyage et Déplacement'),
        ('formation', 'Formation'),
        ('peage_autoroute', 'Péage Autoroute'),
        ('stationnement', 'Stationnement'),
        ('impot_taxe', 'Impôts et Taxes'),
        ('taxe_professionnelle', 'Taxe Professionnelle'),
        ('autres_charges', 'Autres Charges'),
        ('divers', 'Divers')
    ]

    entreprise = models.CharField(max_length=20, choices=TYPE_ENTREPRISE)
    type_operation = models.CharField(max_length=10, choices=TYPE_OPERATION)
    date_operation = models.DateField()
    date_valeur = models.DateField()
    libelle = models.CharField(max_length=255)
    montant_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=20.00)
    montant_tva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    montant_ttc = models.DecimalField(max_digits=12, decimal_places=2)
    categorie = models.CharField(max_length=50, choices=CATEGORIE_OPERATION)
    reference = models.CharField(max_length=100, blank=True)
    beneficiaire = models.CharField(max_length=200, blank=True)
    statut_tva = models.CharField(max_length=20, choices=[
        ('deductible', 'TVA Déductible'),
        ('collectee', 'TVA Collectée'),
        ('neutre', 'Neutre (Sans TVA)')
    ])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-date_operation', '-date_valeur']
        verbose_name = "Opération TVA"
        verbose_name_plural = "Opérations TVA"

    def save(self, *args, **kwargs):
        if not self.montant_tva and self.montant_ht:
            self.montant_tva = (self.montant_ht * self.taux_tva) / 100
        
        if not self.montant_ttc:
            self.montant_ttc = self.montant_ht + self.montant_tva
            
        if not self.statut_tva:
            if self.type_operation == 'credit':
                self.statut_tva = 'collectee'
            else:
                # ⭐⭐ MISE À JOUR DE LA LOGIQUE POUR LES NOUVELLES CATÉGORIES ⭐⭐
                if self.categorie in ['carburant', 'entretien_vehicule', 'reparation_vehicule', 
                                    'achat_fournisseur', 'fournitures_bureau', 'materiel_informatique',
                                    'frais_bancaires', 'honoraires_comptable', 'honoraires_avocat',
                                    'publicite_marketing', 'voyage_deplacement', 'formation',
                                    'peage_autoroute', 'stationnement']:
                    self.statut_tva = 'deductible'
                elif self.categorie in ['salaires', 'impot_taxe', 'taxe_professionnelle']:
                    self.statut_tva = 'neutre'
                elif self.categorie == 'vente_client':
                    self.statut_tva = 'collectee'
                else:
                    self.statut_tva = 'deductible'
                    
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.entreprise} - {self.libelle} - {self.montant_ttc} DH"

class DeclarationTVA(models.Model):
    entreprise = models.CharField(max_length=20, choices=OperationTVA.TYPE_ENTREPRISE)
    mois = models.IntegerField()
    annee = models.IntegerField()
    
    tva_collectee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tva_deductible = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tva_net_a_payer = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    total_credits_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_debits_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_credits_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_debits_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    statut = models.CharField(max_length=20, choices=[
        ('brouillon', 'Brouillon'),
        ('calculee', 'Calculée'),
        ('declaree', 'Déclarée'),
        ('payee', 'Payée')
    ], default='brouillon')
    
    date_declaration = models.DateField(null=True, blank=True)
    date_paiement = models.DateField(null=True, blank=True)
    reference_dgi = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['entreprise', 'mois', 'annee']
        ordering = ['-annee', '-mois']

    def calculer_tva(self):
        from django.db.models import Q, Sum
        
        operations = OperationTVA.objects.filter(
            entreprise=self.entreprise,
            date_operation__month=self.mois,
            date_operation__year=self.annee
        )
        
        tva_collectee = operations.filter(
            statut_tva='collectee'
        ).aggregate(total=models.Sum('montant_tva'))['total'] or 0
        
        tva_deductible = operations.filter(
            statut_tva='deductible'
        ).aggregate(total=models.Sum('montant_tva'))['total'] or 0
        
        credits = operations.filter(type_operation='credit')
        debits = operations.filter(type_operation='debit')
        
        self.tva_collectee = tva_collectee
        self.tva_deductible = tva_deductible
        self.tva_net_a_payer = tva_collectee - tva_deductible
        
        self.total_credits_ht = credits.aggregate(total=models.Sum('montant_ht'))['total'] or 0
        self.total_debits_ht = debits.aggregate(total=models.Sum('montant_ht'))['total'] or 0
        self.total_credits_ttc = credits.aggregate(total=models.Sum('montant_ttc'))['total'] or 0
        self.total_debits_ttc = debits.aggregate(total=models.Sum('montant_ttc'))['total'] or 0
        
        self.statut = 'calculee'
        self.save()

    def __str__(self):
        return f"TVA {self.entreprise} - {self.mois}/{self.annee} - {self.tva_net_a_payer} DH"