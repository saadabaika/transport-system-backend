import os
from pathlib import Path
from dotenv import load_dotenv

# ⭐ MODIFICATION IMPORTANTE ⭐
BASE_DIR = Path(__file__).resolve().parent.parent

# Charge le .env avec le chemin ABSOLU
env_path = BASE_DIR / '.env'
load_dotenv(env_path)

# ⭐ AJOUTEZ CES LIGNES POUR DÉBOGUER ⭐
#print(" SECRET_KEY chargée :", bool(os.getenv('SECRET_KEY')))
#print(" Chemin .env :", env_path)
#print(" Fichier .env existe :", os.path.exists(env_path))

SECRET_KEY = 'sEyqbNROphOD3VRSV9nxr6TObWuFL36X5MZ1ffS9MZycGQJb3ab-OKZxFEYz64nOS6M'

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
#ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '.ondigitalocean.app,localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',  # AJOUT
    'corsheaders',
    'gestion',
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
  #  'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
CSRF_USE_SESSIONS = False
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
CSRF_TRUSTED_ORIGINS = [
    'https://*.ondigitalocean.app',  # ⭐ AJOUTÉ
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:8000', 
    'http://127.0.0.1:8000',
]
ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
DATABASES = {
       'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'gestion_transport',      # Le nom que vous venez de créer
            'USER': 'postgres',               # Votre utilisateur PostgreSQL
            'PASSWORD': 'hh', # Mot de passe de PostgreSQL
            'HOST': 'localhost',
            'PORT': '5432',
       }
   }


 #DATABASES = {
     #'default': {
         #  'ENGINE': 'django.db.backends.sqlite3',
        #  'NAME': BASE_DIR / 'db.sqlite3',
     #  }
  #}

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Casablanca'
USE_I18N = True
USE_TZ = True
USE_L10N = True


STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "https://*.ondigitalocean.app",  # ⭐ AJOUTÉ
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_ALL_ORIGINS = False   # ← FALSE

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',  # PRINCIPAL
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
}

AUTH_USER_MODEL = 'gestion.User'
