from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class IsAdminOrEmploye(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.role in ['admin', 'employe']:
            return True
        return False
    
    def has_object_permission(self, request, view, obj):
        if request.method == 'DELETE':
            return request.user.role == 'admin'
        return True

# ⭐ NOUVELLE PERMISSION POUR L'AGENT DE FACTURATION
class IsFacturation(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # L'agent de facturation a accès aux clients et factures
        if request.user.role == 'facturation':
            # Autoriser GET, POST, PUT, PATCH mais pas DELETE pour les clients
            if view.__class__.__name__ in ['ClientViewSet', 'FactureViewSet', 'LigneFactureViewSet']:
                if request.method == 'DELETE':
                    return False  # Pas de suppression pour les clients
                return True
        return False
    
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'facturation':
            # Empêcher la suppression des clients
            if view.__class__.__name__ == 'ClientViewSet' and request.method == 'DELETE':
                return False
            return True
        return False

# ⭐ PERMISSION COMBINÉE POUR ADMIN, EMPLOYÉ ET FACTURATION
# ⭐ PERMISSION COMBINÉE POUR ADMIN, EMPLOYÉ ET FACTURATION - CORRIGÉE
class IsAdminOrEmployeOrFacturation(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Admin a tous les droits
        if request.user.role == 'admin':
            return True
        
        # Employé a accès à presque tout
        if request.user.role == 'employe':
            return True
        
        # Agent de facturation - accès limité
        if request.user.role == 'facturation':
            # Autoriser l'accès aux clients et factures (sauf DELETE)
            if view.__class__.__name__ in ['ClientViewSet', 'FactureViewSet', 'LigneFactureViewSet']:
                if request.method == 'DELETE':
                    return False  # ⭐ AJOUT: Pas de suppression pour facturation
                return True
                        # ⭐⭐ NOUVEAU : AJOUT DE CETTE LIGNE ⭐⭐
            if view.__class__.__name__ == 'TrajetViewSet' and request.method in permissions.SAFE_METHODS:
                return True
            # ⭐⭐ FIN DE L'AJOUT ⭐⭐

            # Accès en lecture seule au dashboard et au compte
            if view.__class__.__name__ in ['DashboardView', 'MyAccountViewSet'] and request.method in permissions.SAFE_METHODS:
                return True
            return False
        
        return False
    
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        
        if request.user.role == 'employe':
            if request.method == 'DELETE':
                return False  # Les employés ne peuvent pas supprimer
            return True
        
        if request.user.role == 'facturation':
            # ⭐ CORRECTION: Empêcher la suppression pour TOUS les modules
            if request.method == 'DELETE':
                return False
            return True
        
        return False