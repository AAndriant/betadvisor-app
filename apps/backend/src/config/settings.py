import os
from pathlib import Path
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environ
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR.parent, '.env'))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-me-in-prod')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=True)

_ALLOWED_HOSTS_DEFAULT = ['localhost', '127.0.0.1'] if DEBUG else []
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=_ALLOWED_HOSTS_DEFAULT)

# PRODUCTION SAFETY — checks effectués APRÈS que DEBUG et ALLOWED_HOSTS soient définis
if not DEBUG and SECRET_KEY.startswith('django-insecure-'):
    raise RuntimeError(
        "[SECURITY] SECRET_KEY is insecure in production. "
        "Set a proper random SECRET_KEY via environment variable."
    )

if not DEBUG and ('*' in ALLOWED_HOSTS or not ALLOWED_HOSTS):
    raise RuntimeError(
        "[SECURITY] ALLOWED_HOSTS must be explicitly set in production. "
        "Set ALLOWED_HOSTS env var (e.g. 'api.betadvisor.app')."
    )


# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8081',
    'http://127.0.0.1:8081',
    'http://localhost:8082',
    'http://127.0.0.1:8082',
    'http://localhost:8083',
    'http://127.0.0.1:8083',
]
CORS_ALLOW_CREDENTIALS = True


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',

    # Local Apps
    'core',
    'users',
    'finance',
    'bets',
    'sports',
    'tickets',
    'gamification',
    'social',
    'api',
    'connect',
    'subscriptions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': env.db('DATABASE_URL', default='postgres://betadvisor:betadvisor@db:5432/betadvisor')
}

# ─────────────────────────────────────────────────────────────
# STRIPE CONFIGURATION
# ─────────────────────────────────────────────────────────────

# Clés Stripe — utiliser STRIPE_LIVE_SECRET_KEY en production
# Si STRIPE_LIVE_SECRET_KEY est présent, il a la priorité sur STRIPE_SECRET_KEY
_stripe_secret = env('STRIPE_LIVE_SECRET_KEY', default='') or env('STRIPE_SECRET_KEY', default='')
if not _stripe_secret:
    raise RuntimeError(
        "[STRIPE] STRIPE_LIVE_SECRET_KEY ou STRIPE_SECRET_KEY requis au démarrage."
    )
STRIPE_SECRET_KEY = _stripe_secret
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY', default='')

# Webhook secret — fail fast si absent et DEBUG=False
_webhook_secret = env('STRIPE_LIVE_WEBHOOK_SECRET', default='') or env('STRIPE_WEBHOOK_SECRET', default='')
if not DEBUG and not _webhook_secret:
    raise RuntimeError(
        "[STRIPE] STRIPE_LIVE_WEBHOOK_SECRET requis en production."
    )
STRIPE_WEBHOOK_SECRET = _webhook_secret or 'whsec_placeholder_dev_only'

# Platform Stripe Account
STRIPE_PLATFORM_ACCOUNT_ID = env('STRIPE_PLATFORM_ACCOUNT_ID', default='')

# ─────────────────────────────────────────────────────────────
# PLATFORM FEE — CONSTANTE 20%
# ─────────────────────────────────────────────────────────────
# CRITIQUE : cette valeur est redondante avec la constante dans services.py.
# Le service Stripe utilise TOUJOURS application_fee_percent=20 en dur.
# Cette variable est ici pour documentation et vérification au boot.
STRIPE_PLATFORM_FEE_PERCENT = env.int('STRIPE_PLATFORM_FEE_PERCENT', default=20)
if STRIPE_PLATFORM_FEE_PERCENT != 20:
    import warnings
    warnings.warn(
        f"[FEE] STRIPE_PLATFORM_FEE_PERCENT={STRIPE_PLATFORM_FEE_PERCENT} (attendu: 20). "
        "Le service utilise la constante 20 — vérifier la cohérence.",
        RuntimeWarning
    )

# OBSOLETE — ne pas utiliser dans le code Connect (valeur par défaut = 10 = INCORRECTE)
# Conservé uniquement pour rétrocompatibilité avec l'app finance/ existante
PLATFORM_FEE_PERCENT = env.float('PLATFORM_FEE_PERCENT', default=10.0)

# ─────────────────────────────────────────────────────────────
# CHECKOUT DEEP LINKS (Expo betadvisor://)
# ─────────────────────────────────────────────────────────────
# {CHECKOUT_SESSION_ID} est substitué par Stripe automatiquement
CHECKOUT_SUCCESS_URL = env(
    'CHECKOUT_SUCCESS_URL',
    default='betadvisor://checkout/success?session_id={CHECKOUT_SESSION_ID}'
)
CHECKOUT_CANCEL_URL = env(
    'CHECKOUT_CANCEL_URL',
    default='betadvisor://checkout/cancel'
)
EXPO_APP_SCHEME = env('EXPO_APP_SCHEME', default='betadvisor')

# ─────────────────────────────────────────────────────────────
# URLs
# ─────────────────────────────────────────────────────────────
SITE_URL = env('SITE_URL', default='http://localhost:8000')
APP_BASE_URL = env('APP_BASE_URL', default=SITE_URL)


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR.parent, 'media')


# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.CustomUser'

# Django Rest Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # Pour le panel admin
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

# SimpleJWT Settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

