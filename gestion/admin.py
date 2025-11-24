from django.contrib import admin
from .models import *

@admin.register(TransporteurExterne)
class TransporteurExterneAdmin(admin.ModelAdmin):
    list_display = ['nom', 'ice', 'telephone', 'statut']
    list_filter = ['statut']
    search_fields = ['nom', 'ice']

@admin.register(Camion)
class CamionAdmin(admin.ModelAdmin):
    list_display = ['immatriculation', 'marque', 'modele', 'type_propriete', 'transporteur_externe', 'statut']
    list_filter = ['type_propriete', 'statut', 'transporteur_externe']
    search_fields = ['immatriculation', 'marque']

@admin.register(Employe)
class EmployeAdmin(admin.ModelAdmin):
    list_display = ['nom', 'prenom', 'type_employe', 'salaire_base', 'statut']
    list_filter = ['type_employe', 'statut']

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['nom', 'ice', 'telephone', 'email']
    search_fields = ['nom', 'ice']

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ['ville', 'frais_deplacement']
    search_fields = ['ville']

@admin.register(Trajet)
class TrajetAdmin(admin.ModelAdmin):
    list_display = ['date', 'client', 'destination', 'type_sous_traitance', 'transporteur_externe', 'prix_trajet', 'prix_sous_traitance']
    list_filter = ['type_sous_traitance', 'type_service', 'type_trajet', 'date']
    search_fields = ['client__nom', 'destination__ville']
    readonly_fields = ['total_frais_supplementaires']

@admin.register(PaiementSousTraitance)
class PaiementSousTraitanceAdmin(admin.ModelAdmin):
    list_display = ['trajet', 'transporteur_externe', 'montant', 'date_echeance', 'statut']
    list_filter = ['statut', 'date_echeance']
    search_fields = ['transporteur_externe__nom', 'reference']
    
from django.contrib import admin
from gestion.models import *

class LigneFactureInline(admin.TabularInline):
    model = LigneFacture
    extra = 1
    # ⭐ SUPPRIMEZ 'destination' des fields ⭐
    fields = ['description', 'quantite', 'prix_unitaire', 'tva', 'montant_ht', 'montant_tva', 'montant_ttc']
    readonly_fields = ['montant_ht', 'montant_tva', 'montant_ttc']
    
    def montant_ht(self, obj):
        return f"{obj.montant_ht} DH" if obj.montant_ht else "0 DH"
    montant_ht.short_description = "Montant HT"
    
    def montant_tva(self, obj):
        return f"{obj.montant_tva} DH" if obj.montant_tva else "0 DH"
    montant_tva.short_description = "Montant TVA"
    
    def montant_ttc(self, obj):
        return f"{obj.montant_ttc} DH" if obj.montant_ttc else "0 DH"
    montant_ttc.short_description = "Montant TTC"

@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ['numero_facture', 'entreprise', 'client', 'date_facture', 'date_echeance', 'total_ttc', 'statut']
    list_filter = ['entreprise', 'statut', 'date_facture', 'date_echeance']
    search_fields = ['numero_facture', 'client__nom']
    # ⭐ SUPPRIMEZ 'tva' des readonly_fields ⭐
    readonly_fields = ['numero_facture', 'total_ht', 'montant_tva', 'total_ttc', 'created_at', 'updated_at']
    inlines = [LigneFactureInline]
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('numero_facture', 'entreprise', 'client', 'statut')
        }),
        ('Dates', {
            'fields': ('date_facture', 'date_echeance')
        }),
        ('Paramètres Financiers', {
            # ⭐ SUPPRIMEZ 'tva' des fields ⭐
            'fields': ('total_ht', 'montant_tva', 'total_ttc')
        }),
        ('Informations Supplémentaires', {
            'fields': ('conditions_paiement', 'notes')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        # Recalculer les totaux avant sauvegarde
        if obj.pk:
            obj.calculer_totaux()
        super().save_model(request, obj, form, change)
    
    def save_formset(self, request, form, formset, change):
        # Recalculer les totaux après sauvegarde des lignes
        instances = formset.save(commit=False)
        for instance in instances:
            instance.save()
        for obj in formset.deleted_objects:
            obj.delete()
        if change:
            form.instance.calculer_totaux()

@admin.register(LigneFacture)
class LigneFactureAdmin(admin.ModelAdmin):
    # ⭐ SUPPRIMEZ 'destination' de list_display et list_filter ⭐
    list_display = ['facture', 'description', 'quantite', 'prix_unitaire', 'tva', 'montant_ht', 'montant_tva', 'montant_ttc', 'ordre']
    list_filter = ['facture__entreprise', 'tva']
    search_fields = ['facture__numero_facture', 'description']
    readonly_fields = ['montant_ht', 'montant_tva', 'montant_ttc']
    
    def montant_ht(self, obj):
        return f"{obj.montant_ht} DH" if obj.montant_ht else "0 DH"
    montant_ht.short_description = "Montant HT"
    
    def montant_tva(self, obj):
        return f"{obj.montant_tva} DH" if obj.montant_tva else "0 DH"
    montant_tva.short_description = "Montant TVA"
    
    def montant_ttc(self, obj):
        return f"{obj.montant_ttc} DH" if obj.montant_ttc else "0 DH"
    montant_ttc.short_description = "Montant TTC"
    
    def get_queryset(self, request):
        # ⭐ SUPPRIMEZ 'destination' du select_related ⭐
        return super().get_queryset(request).select_related('facture')
    
@admin.register(ChargeCamion)
class ChargeCamionAdmin(admin.ModelAdmin):
    list_display = ['camion', 'type_charge', 'categorie', 'montant', 'date_charge', 'statut']
    list_filter = ['type_charge', 'categorie', 'statut', 'date_charge']
    search_fields = ['camion__immatriculation', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('camion', 'type_charge', 'categorie', 'description', 'montant', 'statut')
        }),
        ('Informations Gazoil', {
            'fields': ('litres', 'kilometrage'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('date_debut', 'date_fin', 'date_charge')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

from django.contrib import admin
from .models import OperationTVA, DeclarationTVA

@admin.register(OperationTVA)
class OperationTVAAdmin(admin.ModelAdmin):
    list_display = ['date_operation', 'entreprise', 'type_operation', 'libelle', 'montant_ht', 'montant_tva', 'montant_ttc', 'categorie', 'statut_tva']
    list_filter = ['entreprise', 'type_operation', 'categorie', 'statut_tva', 'date_operation']
    search_fields = ['libelle', 'reference', 'beneficiaire']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('entreprise', 'type_operation', 'date_operation', 'date_valeur')
        }),
        ('Détails Opération', {
            'fields': ('libelle', 'reference', 'beneficiaire', 'categorie')
        }),
        ('Aspects Financiers', {
            'fields': ('montant_ht', 'taux_tva', 'montant_tva', 'montant_ttc', 'statut_tva')
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(DeclarationTVA)
class DeclarationTVAAdmin(admin.ModelAdmin):
    list_display = ['entreprise', 'mois', 'annee', 'tva_collectee', 'tva_deductible', 'tva_net_a_payer', 'statut']
    list_filter = ['entreprise', 'statut', 'annee', 'mois']
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        return False  # Les déclarations sont créées automatiquement