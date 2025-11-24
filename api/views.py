from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from gestion.models import *
from .serializers import *
from django.db.models import Sum
from django.contrib.auth import login, logout
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from gestion.models import User
from .serializers import UserSerializer, LoginSerializer
from .permissions import IsAdmin, IsAdminOrEmploye , IsAdminOrEmployeOrFacturation 

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from django.views.decorators.csrf import ensure_csrf_cookie

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes

class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Créer ou récupérer le token
            token, created = Token.objects.get_or_create(user=user)
            
            user_data = UserSerializer(user).data
            return Response({
                'user': user_data,
                'token': token.key,  # AJOUT DU TOKEN
                'message': 'Connexion réussie'
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        # Pour Token Auth, supprimer le token
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                request.user.auth_token.delete()
            except:
                pass
            return Response({'message': 'Déconnexion réussie'})
        return Response({'message': 'Déjà déconnecté'})
    
    @action(detail=False, methods=['get'])
    def current_user(self, request):
        if request.user.is_authenticated:
            serializer = UserSerializer(request.user)
            return Response(serializer.data)
        return Response({'error': 'Non authentifié'}, status=status.HTTP_401_UNAUTHORIZED)
    
from django.http import JsonResponse
from django.views import View

class LogoutView(View):
    def post(self, request):
        from django.contrib.auth import logout
        logout(request)
        return JsonResponse({'message': 'Déconnexion réussie'})
    
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    # AJOUTEZ cette méthode pour gérer la création
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Créer l'utilisateur avec le mot de passe
            user = User.objects.create_user(
                username=serializer.validated_data['username'],
                password=request.data.get('password'),
                email=serializer.validated_data.get('email', ''),
                role=serializer.validated_data.get('role', 'employe')
            )
            # Mettre à jour les autres champs
            for attr, value in serializer.validated_data.items():
                if attr not in ['password']:  # Le mot de passe est déjà géré
                    setattr(user, attr, value)
            user.save()
            
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class TransporteurExterneViewSet(viewsets.ModelViewSet):
    queryset = TransporteurExterne.objects.all()
    serializer_class = TransporteurExterneSerializer
    permission_classes = [IsAdminOrEmploye]

class CamionViewSet(viewsets.ModelViewSet):
    queryset = Camion.objects.all()
    serializer_class = CamionSerializer
    permission_classes = [IsAdminOrEmploye]

class EmployeViewSet(viewsets.ModelViewSet):
    queryset = Employe.objects.all()
    serializer_class = EmployeSerializer
    permission_classes = [IsAdminOrEmploye]

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAdminOrEmployeOrFacturation]  # ⭐ MISE À JOUR
    def destroy(self, request, *args, **kwargs):
        # Empêcher la suppression si c'est un agent de facturation
        if request.user.role == 'facturation':
            return Response(
                {'error': 'Vous n\'avez pas la permission de supprimer des clients.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
class DestinationViewSet(viewsets.ModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer
    permission_classes = [IsAdminOrEmploye]

class TrajetViewSet(viewsets.ModelViewSet):
    queryset = Trajet.objects.all()
    serializer_class = TrajetSerializer
    permission_classes = [IsAdminOrEmployeOrFacturation]  # ⭐ CHANGEMENT ICI (était IsAdminOrEmploye)

class PaiementSousTraitanceViewSet(viewsets.ModelViewSet):
    queryset = PaiementSousTraitance.objects.all()
    serializer_class = PaiementSousTraitanceSerializer
    permission_classes = [IsAdminOrEmploye]

# AJOUTER CES NOUVELLES VUES POUR LA FACTURATION
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum

class FactureViewSet(viewsets.ModelViewSet):
    queryset = Facture.objects.all().order_by('-date_facture', '-numero_facture')
    permission_classes = [IsAdminOrEmployeOrFacturation]  # ⭐ MISE À JOUR
   
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return FactureCreateSerializer
        return FactureSerializer

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role == 'facturation':
            return Response(
                {'error': 'Les agents de facturation ne peuvent pas supprimer des factures.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        if instance.statut == 'payee':
            return Response(
                {'error': 'Impossible de supprimer une facture payée'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def changer_statut(self, request, pk=None):
        facture = self.get_object()
        nouveau_statut = request.data.get('statut')
        
        if nouveau_statut in dict(Facture.STATUT_FACTURE):
            facture.statut = nouveau_statut
            facture.save()
            return Response({'statut': 'Statut mis à jour'})
        
        return Response({'error': 'Statut invalide'}, status=400)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        total_factures = Facture.objects.count()
        factures_payees = Facture.objects.filter(statut='payee').count()
        factures_brouillon = Facture.objects.filter(statut='brouillon').count()
        factures_envoyees = Facture.objects.filter(statut='envoyee').count()
        
        total_ca = Facture.objects.filter(statut='payee').aggregate(
            total=Sum('total_ttc')
        )['total'] or 0
        
        return Response({
            'total_factures': total_factures,
            'factures_payees': factures_payees,
            'factures_brouillon': factures_brouillon,
            'factures_envoyees': factures_envoyees,
            'chiffre_affaires': float(total_ca)
        })

class LigneFactureViewSet(viewsets.ModelViewSet):
    queryset = LigneFacture.objects.all()
    serializer_class = LigneFactureSerializer
    permission_classes = [IsAdminOrEmploye]

    def get_queryset(self):
        queryset = LigneFacture.objects.all()
        facture_id = self.request.query_params.get('facture_id')
        if facture_id:
            queryset = queryset.filter(facture_id=facture_id)
        return queryset
    
from django.db.models import Sum, Avg, Count
from django.db.models.functions import TruncMonth
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import datetime, timedelta

from django.db.models import Sum, Avg, Count
from django.db.models.functions import ExtractMonth
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import datetime
from gestion.models import *
from .serializers import *

class ChargeCamionViewSet(viewsets.ModelViewSet):
    queryset = ChargeCamion.objects.all()
    serializer_class = ChargeCamionSerializer
    permission_classes = [IsAdminOrEmploye]

    def get_queryset(self):
        queryset = ChargeCamion.objects.all()
        
        # Filtres
        camion_id = self.request.query_params.get('camion_id')
        type_charge = self.request.query_params.get('type_charge')
        categorie = self.request.query_params.get('categorie')
        annee = self.request.query_params.get('annee')
        mois = self.request.query_params.get('mois')
        
        if camion_id:
            queryset = queryset.filter(camion_id=camion_id)
        if type_charge:
            queryset = queryset.filter(type_charge=type_charge)
        if categorie:
            queryset = queryset.filter(categorie=categorie)
        if annee:
            queryset = queryset.filter(date_charge__year=annee)
        if mois:
            queryset = queryset.filter(date_charge__month=mois)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistiques_globales(self, request):
        """Statistiques globales avec tous les filtres"""
        camion_id = request.query_params.get('camion_id')
        annee = request.query_params.get('annee', datetime.now().year)
        mois = request.query_params.get('mois')
        type_charge = request.query_params.get('type_charge')
        categorie = request.query_params.get('categorie')
        
        queryset = ChargeCamion.objects.filter(date_charge__year=annee)
        
        # Appliquer les filtres
        if camion_id:
            queryset = queryset.filter(camion_id=camion_id)
        if mois:
            queryset = queryset.filter(date_charge__month=mois)
        if type_charge:
            queryset = queryset.filter(type_charge=type_charge)
        if categorie:
            queryset = queryset.filter(categorie=categorie)
        
        # Statistiques globales
        stats_globales = queryset.aggregate(
            total_montant=Sum('montant'),
            nombre_charges=Count('id'),
            moyenne_montant=Avg('montant')
        )
        
        # Statistiques par type de charge
        stats_par_type = queryset.values('type_charge').annotate(
            total=Sum('montant'),
            count=Count('id')
        ).order_by('type_charge')
        
        # Statistiques par catégorie
        stats_par_categorie = queryset.values('categorie').annotate(
            total=Sum('montant'),
            count=Count('id')
        ).order_by('categorie')
        
        # Statistiques par mois (pour l'année sélectionnée)
        stats_par_mois = queryset.annotate(
            mois=ExtractMonth('date_charge')
        ).values('mois').annotate(
            total=Sum('montant'),
            count=Count('id')
        ).order_by('mois')
        
        # Préparer les données pour tous les mois
        mois_data = []
        for mois_num in range(1, 13):
            mois_stat = next((stat for stat in stats_par_mois if stat['mois'] == mois_num), None)
            mois_data.append({
                'mois': mois_num,
                'mois_nom': self.get_mois_nom(mois_num),
                'total_montant': float(mois_stat['total']) if mois_stat else 0,
                'nombre_charges': mois_stat['count'] if mois_stat else 0,
            })
        
        # Dernières charges
        dernieres_charges = queryset.order_by('-date_charge', '-created_at')[:10]
        charges_serializer = ChargeCamionSerializer(dernieres_charges, many=True)
        
        return Response({
            'filtres_appliques': {
                'annee': annee,
                'mois': mois,
                'camion_id': camion_id,
                'type_charge': type_charge,
                'categorie': categorie
            },
            'stats_globales': {
                'total_montant': float(stats_globales['total_montant'] or 0),
                'nombre_charges': stats_globales['nombre_charges'] or 0,
                'moyenne_montant': float(stats_globales['moyenne_montant'] or 0)
            },
            'stats_par_type': list(stats_par_type),
            'stats_par_categorie': list(stats_par_categorie),
            'stats_par_mois': mois_data,
            'dernieres_charges': charges_serializer.data
        })
    
    def get_mois_nom(self, mois):
        mois_noms = {
            1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
            5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
            9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
        }
        return mois_noms.get(mois, '')
    
# AJOUTEZ CETTE FONCTION À LA FIN DU FICHIER
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

# ... (tout votre code existant)

# CES DEUX VUES DOIVENT ÊTRE À LA FIN
@api_view(['POST'])
@permission_classes([AllowAny])
def login_simple(request):
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({'error': 'Username et password requis'}, status=400)
    
    user = authenticate(username=username, password=password)
    
    if user:
        if user.is_active:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
                'role': user.role,
                'message': 'Connexion réussie'
            })
        else:
            return Response({'error': 'Compte désactivé'}, status=400)
    else:
        return Response({'error': 'Identifiants invalides'}, status=400)

# ⭐⭐ CETTE VUE DOIT EXISTER ⭐⭐
@api_view(['POST'])
@permission_classes([IsAdmin])
def create_user_simple(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '')
    role = request.data.get('role', 'employe')
    
    if not username or not password:
        return Response({'error': 'Username et password requis'}, status=400)
    
    try:
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            role=role
        )
        
        Token.objects.create(user=user)
        
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }, status=201)
        
    except Exception as e:
        return Response({'error': str(e)}, status=400)
    
from django.contrib.auth import update_session_auth_hash
from .serializers import UserCreateSerializer, UserUpdateSerializer, ChangePasswordSerializer, AdminChangePasswordSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'change_password', 'block_user', 'unblock_user', 'force_logout']:
            permission_classes = [IsAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    def create(self, request, *args, **kwargs):
         serializer = self.get_serializer(data=request.data)
         if serializer.is_valid():
            # Utiliser create_user pour bien hasher le mot de passe
            user = User.objects.create_user(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password'],
                email=serializer.validated_data.get('email', ''),
                first_name=serializer.validated_data.get('first_name', ''),
                last_name=serializer.validated_data.get('last_name', ''),
                role=serializer.validated_data.get('role', 'employe'),
                telephone=serializer.validated_data.get('telephone', ''),
                date_embauche=serializer.validated_data.get('date_embauche', None)
            )
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """Changer le mot de passe de son propre compte"""
        user = self.get_object()
        
        if user != request.user:
            return Response(
                {'error': 'Vous ne pouvez changer que votre propre mot de passe'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'old_password': 'Ancien mot de passe incorrect'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            update_session_auth_hash(request, user)
            
            return Response({'message': 'Mot de passe changé avec succès'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def admin_change_password(self, request, pk=None):
        """Admin change le mot de passe d'un utilisateur"""
        user = self.get_object()
        
        serializer = AdminChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({'message': f'Mot de passe de {user.username} changé avec succès'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def block_user(self, request, pk=None):
        """Bloquer un utilisateur"""
        user = self.get_object()
        
        if user == request.user:
            return Response(
                {'error': 'Vous ne pouvez pas bloquer votre propre compte'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.is_active = False
        user.statut = 'bloque'
        user.save()
        
        return Response({'message': f'Utilisateur {user.username} bloqué avec succès'})
    
    @action(detail=True, methods=['post'])
    def unblock_user(self, request, pk=None):
        """Débloquer un utilisateur"""
        user = self.get_object()
        
        user.is_active = True
        user.statut = 'actif'
        user.save()
        
        return Response({'message': f'Utilisateur {user.username} débloqué avec succès'})
    
    @action(detail=True, methods=['post'])
    def force_logout(self, request, pk=None):
        """Forcer la déconnexion d'un utilisateur (supprimer son token)"""
        user = self.get_object()
        
        if user == request.user:
            return Response(
                {'error': 'Vous ne pouvez pas vous déconnecter vous-même'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Supprimer le token d'authentification
            Token.objects.filter(user=user).delete()
        except:
            pass
        
        return Response({'message': f'Utilisateur {user.username} déconnecté avec succès'})

class MyAccountViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Récupérer les informations du compte connecté"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        """Modifier son profil"""
        user = request.user
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Profil mis à jour avec succès', 'user': serializer.data})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Changer son mot de passe"""
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'old_password': 'Ancien mot de passe incorrect'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            update_session_auth_hash(request, user)
            
            return Response({'message': 'Mot de passe changé avec succès'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime
from gestion.models import OperationTVA, DeclarationTVA
from .serializers import *

class OperationTVAViewSet(viewsets.ModelViewSet):
    queryset = OperationTVA.objects.all()
    permission_classes = [IsAdminOrEmploye]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return OperationTVACreateSerializer
        return OperationTVASerializer

    def get_queryset(self):
        queryset = OperationTVA.objects.all()
        
        # Filtres
        entreprise = self.request.query_params.get('entreprise')
        mois = self.request.query_params.get('mois')
        annee = self.request.query_params.get('annee')
        type_operation = self.request.query_params.get('type_operation')
        categorie = self.request.query_params.get('categorie')
        
        if entreprise and entreprise != 'tous':
            queryset = queryset.filter(entreprise=entreprise)
        if mois:
            queryset = queryset.filter(date_operation__month=mois)
        if annee:
            queryset = queryset.filter(date_operation__year=annee)
        if type_operation:
            queryset = queryset.filter(type_operation=type_operation)
        if categorie:
            queryset = queryset.filter(categorie=categorie)
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def statistiques_mensuelles(self, request):
        entreprise = request.query_params.get('entreprise')
        mois = request.query_params.get('mois', timezone.now().month)
        annee = request.query_params.get('annee', timezone.now().year)
        
        if not entreprise:
            return Response(
                {'error': 'Le paramètre entreprise est requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        operations = OperationTVA.objects.filter(
            entreprise=entreprise,
            date_operation__month=mois,
            date_operation__year=annee
        )
        
        stats = operations.aggregate(
            total_credits_ht=Sum('montant_ht', filter=Q(type_operation='credit')),
            total_debits_ht=Sum('montant_ht', filter=Q(type_operation='debit')),
            total_credits_ttc=Sum('montant_ttc', filter=Q(type_operation='credit')),
            total_debits_ttc=Sum('montant_ttc', filter=Q(type_operation='debit')),
            tva_collectee=Sum('montant_tva', filter=Q(statut_tva='collectee')),
            tva_deductible=Sum('montant_tva', filter=Q(statut_tva='deductible'))
        )
        
        # Calcul TVA nette
        tva_collectee = stats['tva_collectee'] or 0
        tva_deductible = stats['tva_deductible'] or 0
        tva_nette = tva_collectee - tva_deductible
        
        return Response({
            'entreprise': entreprise,
            'mois': mois,
            'annee': annee,
            'tva_collectee': float(tva_collectee),
            'tva_deductible': float(tva_deductible),
            'tva_nette': float(tva_nette),
            'total_credits_ht': float(stats['total_credits_ht'] or 0),
            'total_debits_ht': float(stats['total_debits_ht'] or 0),
            'total_credits_ttc': float(stats['total_credits_ttc'] or 0),
            'total_debits_ttc': float(stats['total_debits_ttc'] or 0),
            'solde_net': float((stats['total_credits_ttc'] or 0) - (stats['total_debits_ttc'] or 0))
        })

class DeclarationTVAViewSet(viewsets.ModelViewSet):
    queryset = DeclarationTVA.objects.all()
    serializer_class = DeclarationTVASerializer
    permission_classes = [IsAdminOrEmploye]

    def get_queryset(self):
        queryset = DeclarationTVA.objects.all()
        
        entreprise = self.request.query_params.get('entreprise')
        annee = self.request.query_params.get('annee')
        
        if entreprise and entreprise != 'tous':
            queryset = queryset.filter(entreprise=entreprise)
        if annee:
            queryset = queryset.filter(annee=annee)
            
        return queryset

    @action(detail=False, methods=['post'])
    def calculer_declaration(self, request):
        serializer = CalculDeclarationTVASerializer(data=request.data)
        if serializer.is_valid():
            entreprise = serializer.validated_data['entreprise']
            mois = serializer.validated_data['mois']
            annee = serializer.validated_data['annee']
            
            # Vérifier si déclaration existe déjà
            declaration, created = DeclarationTVA.objects.get_or_create(
                entreprise=entreprise,
                mois=mois,
                annee=annee,
                defaults={'statut': 'brouillon'}
            )
            
            # Calculer la TVA
            declaration.calculer_tva()
            
            return Response(DeclarationTVASerializer(declaration).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def declarer(self, request, pk=None):
        declaration = self.get_object()
        declaration.statut = 'declaree'
        declaration.date_declaration = timezone.now().date()
        declaration.reference_dgi = request.data.get('reference_dgi', '')
        declaration.save()
        
        return Response({'message': 'Déclaration marquée comme déclarée'})

    @action(detail=True, methods=['post'])
    def marquer_payee(self, request, pk=None):
        declaration = self.get_object()
        declaration.statut = 'payee'
        declaration.date_paiement = timezone.now().date()
        declaration.save()
        
        return Response({'message': 'Déclaration marquée comme payée'})
    
