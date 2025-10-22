# cargodb/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Загружаем общие секреты (SECRET_KEY, OPENAI_API_KEY)
load_dotenv(BASE_DIR.parent / ".env.secrets")

# Определяем окружение (по умолчанию development)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Загружаем окружение (dev или prod)
if ENVIRONMENT == "production":
    load_dotenv(BASE_DIR.parent / ".env.prod")
else:
    load_dotenv(BASE_DIR.parent / ".env.dev")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# DEBUG setting
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# ALLOWED_HOSTS
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',') + [
    'bonablog.ru', 'www.bonablog.ru', 'localhost', '127.0.0.1', '185.169.54.164'
]

CSRF_TRUSTED_ORIGINS = [
    "https://bonablog.ru",
    "https://www.bonablog.ru",
    "https://185.169.54.164",
    "http://bonablog.ru",
    "http://www.bonablog.ru",
    "http://185.169.54.164",
]


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'accounts',
    'home',
    'cargo_acc',
    'chatgpt_ui',
]

AUTH_USER_MODEL = 'accounts.CustomUser'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cargodb.urls'
WSGI_APPLICATION = 'cargodb.wsgi.application'

# DATABASES
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('IP_POSTGRES'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'client_encoding': 'UTF8',
        }
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'ru'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'web/templates')],
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

# Static & Media
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'web/static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging
LOG_DIR = os.path.join(BASE_DIR, 'logging')
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {'format': '{asctime} | {levelname} | {name} | {module}:{funcName}:{lineno} | {message}', 'style': '{'},
        'simple': {'format': '{asctime} - {levelname} - {message}', 'style': '{'},
    },
    'handlers': {
        'file': {'level': 'DEBUG', 'class': 'logging.FileHandler', 'filename': os.path.join(LOG_DIR, 'debug.log'), 'formatter': 'simple'},
        'police_file': {'level': 'DEBUG', 'class': 'logging.FileHandler', 'filename': os.path.join(LOG_DIR, 'police.log'), 'formatter': 'detailed'},
    },
    'loggers': {
        'django': {'handlers': ['file'], 'level': 'INFO', 'propagate': True},
        'pol': {'handlers': ['police_file'], 'level': 'DEBUG', 'propagate': False},
    },
}

LOGIN_REDIRECT_URL = 'profile'
LOGOUT_REDIRECT_URL = '/'

# Serve static in dev mode
if DEBUG:
    STATICFILES_DIRS = [os.path.join(BASE_DIR, 'web/static')]
