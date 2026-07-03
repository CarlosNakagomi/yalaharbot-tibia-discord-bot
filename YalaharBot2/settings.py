import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def require_env(name):
    value = os.getenv(name)
    if value is None or value == '':
        raise RuntimeError(f'Missing required environment variable: {name}')
    return value


def env_bool(name):
    value = require_env(name).lower()
    if value in {'true', '1', 'yes'}:
        return True
    if value in {'false', '0', 'no'}:
        return False
    raise RuntimeError(f'{name} must be true or false')


SECRET_KEY = require_env('DJANGO_SECRET_KEY')
DEBUG = env_bool('DJANGO_DEBUG')
ALLOWED_HOSTS = [host.strip() for host in require_env('DJANGO_ALLOWED_HOSTS').split(',') if host.strip()]
if not ALLOWED_HOSTS:
    raise RuntimeError('DJANGO_ALLOWED_HOSTS must contain at least one host')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'bot',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'YalaharBot2.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'frontend' / 'build'],
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

WSGI_APPLICATION = 'YalaharBot2.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

db_engine = require_env('DB_ENGINE')
if db_engine == 'django.db.backends.sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': db_engine,
            'NAME': BASE_DIR / require_env('DB_NAME'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': db_engine,
            'NAME': require_env('DB_NAME'),
            'USER': require_env('DB_USER'),
            'PASSWORD': require_env('DB_PASSWORD'),
            'HOST': require_env('DB_HOST'),
            'PORT': require_env('DB_PORT'),
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


STATIC_URL = '/static/'

frontend_static = BASE_DIR / 'frontend' / 'build' / 'static'
STATICFILES_DIRS = [frontend_static] if frontend_static.exists() else []

STATIC_ROOT = BASE_DIR / 'staticfiles'


