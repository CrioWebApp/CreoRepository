from pathlib import Path

from environs import Env


env = Env()
env.read_env()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = env('SECRET_KEY')

DEBUG = env.bool('DEBUG', False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', ['127.0.0.1', 'localhost'])

CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', ['https://127.0.0.1'])

SECURE_SSL_REDIRECT = \
    env.str('SECURE_SSL_REDIRECT', '0').lower() in ['true', 't', '1']
if SECURE_SSL_REDIRECT:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

STATIC_ROOT = BASE_DIR / 'staticfiles'

AUTH_USER_MODEL = "accounts.CustomUser"

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'import_export',
    'api',
    'accounts',
    'rest_framework',
    'rest_framework.authtoken',
    'djoser',
    'drf_ip_restrictions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'web.urls'

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

WSGI_APPLICATION = 'web.wsgi.application'

GROUP_MANAGEMENT = False

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     },
# }

DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': env.str('DEBTHOR_DB_NAME'),
        'USER': env.str('DEBTHOR_DB_USER'),
        'PASSWORD': env.str('DEBTHOR_DB_PASSWORD'),
        'HOST': env.str('DEBTHOR_DB_HOST'),
        'PORT': env.str('DEBTHOR_DB_PORT'),
    },
    'ezhik.database.windows.net': {
        'ENGINE': 'mssql',
        'NAME': env.str('DEBTHOR_DB_NAME'),
        'USER': env.str('DEBTHOR_DB_USER'),
        'PASSWORD': env.str('DEBTHOR_DB_PASSWORD'),
        'HOST': env.str('EZHIK_DB_HOST', 'ezhik.database.windows.net'),
        'PORT': env.str('DEBTHOR_DB_PORT'),
    },
    'ezhik-ph.database.windows.net': {
        'ENGINE': 'mssql',
        'NAME': env.str('DEBTHOR_DB_NAME'),
        'USER': env.str('DEBTHOR_DB_USER'),
        'PASSWORD': env.str('DEBTHOR_DB_PASSWORD'),
        'HOST': env.str('EZHIK_PH_DB_HOST', 'ezhik-ph.database.windows.net'),
        'PORT': env.str('DEBTHOR_DB_PORT'),
    },
}

DATABASE_CONNECTION_POOLING = False

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

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
        'drf_ip_restrictions.permissions.AllowedIpList',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'accounts.authentication.BearerAuthentication',
    ],
}

DJOSER = {
    'SERIALIZERS': {
        'token': 'accounts.serializers.TokenSerializer',
        'token_create': 'accounts.serializers.CustomTokenCreateSerializer',
    },
    'PERMISSIONS': {
        'token_create': ['drf_ip_restrictions.permissions.AllowedIpList'],
    }
}

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

DEFAULT_FILE_STORAGE = 'web.azure_storage.AzureMediaStorage'
STATICFILES_STORAGE = 'web.azure_storage.AzureStaticStorage'

AZURE_ACCOUNT_NAME = env.str('AZURE_ACCOUNT_NAME', '')
AZURE_ACCOUNT_KEY = env.str('AZURE_ACCOUNT_KEY', '')
AZURE_CUSTOM_DOMAIN = f'{AZURE_ACCOUNT_NAME}.blob.core.windows.net'

STATIC_URL = f'https://{AZURE_CUSTOM_DOMAIN}/static/'

STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SQL_PROCEDURE = env.str('SQL_PROCEDURE', 'spap_req_verif')

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "verbose",
            "filename":  BASE_DIR / "debug.log"
        }
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "api": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}

DRF_IP_RESTRICTION_SETTINGS = {
    "ALLOWED_IP_LIST": env.list('ALLOWED_IP_LIST', [])
}
