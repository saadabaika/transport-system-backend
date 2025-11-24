from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import  LogoutView , login_simple , create_user_simple # AJOUT create_user_simple


router = DefaultRouter()
router.register(r'auth', views.AuthViewSet, basename='auth')
router.register(r'users', views.UserViewSet)
router.register(r'my-account', views.MyAccountViewSet, basename='my-account')
router.register(r'transporteurs-externes', views.TransporteurExterneViewSet)
router.register(r'camions', views.CamionViewSet)
router.register(r'employes', views.EmployeViewSet)
router.register(r'clients', views.ClientViewSet)
router.register(r'destinations', views.DestinationViewSet)
router.register(r'trajets', views.TrajetViewSet)
router.register(r'paiements-sous-traitance', views.PaiementSousTraitanceViewSet)
router.register(r'factures', views.FactureViewSet)
router.register(r'lignes-facture', views.LigneFactureViewSet)
router.register(r'charges-camion', views.ChargeCamionViewSet)
router.register(r'operations-tva', views.OperationTVAViewSet)
router.register(r'declarations-tva', views.DeclarationTVAViewSet)

urlpatterns = [
    path('auth/logout-simple/', LogoutView.as_view(), name='logout-simple'),
    path('auth/login-simple/', login_simple, name='login-simple'),  # AJOUT
    path('users/create-simple/', create_user_simple, name='user-create-simple'),
    path('', include(router.urls)),


]