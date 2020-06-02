from __future__ import absolute_import
"""
Django settings for collector project.

Generated by 'django-admin startproject' using Django 1.11.9.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
import random
import string
from celery.schedules import crontab
from distutils.util import strtobool


def string_to_bool(string):
    return bool(strtobool(str(string)))


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    'DJANGO_SECRET',
    'c&1d9t^p_ssul^n=i9t+xr5bd&l2yx*q&v1i@rv!x9_j2zp&_l'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = string_to_bool(os.getenv('DEBUG', False))

DEV_MODE = string_to_bool(os.getenv('DEV_MODE', False))
BALENA = os.getenv('BALENA_DEVICE_UUID', False)
DISABLE_ANALYTICS = string_to_bool(os.getenv('DISABLE_ANALYTICS', False))
DISABLE_SCANNING = string_to_bool(os.getenv('DISABLE_SCANNING', False))

ALLOWED_HOSTS = []

if os.getenv('ALLOWED_HOSTS', False):
    ALLOWED_HOSTS += [os.getenv('ALLOWED_HOSTS')]

if DEV_MODE:
    ALLOWED_HOSTS += ['*']

ALLOWED_HOSTS += ['.resindevice.io', '.balena-devices.com']

# Application definition

INSTALLED_APPS = [
    'rest_framework',
    'chartit',
    'analytics.apps.AnalyticsConfig',
    'ble.apps.BleConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'collector.urls'

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
                'django.template.context_processors.static',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'collector.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases
DATABASE_PATH = '/data/collector'

if string_to_bool(os.getenv('USE_POSTGRES', False)):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.getenv('POSTGRES_DATABASE', 'sonar'),
            'USER': os.getenv('POSTGRES_USER', 'sonar'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
            'HOST': os.getenv('POSTGRES_HOST', 'postgres'),
            'PORT': int(os.getenv('POSTGRES_PORT', '5432')),
        }
    }
else:

    DATABASES = { 'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(DATABASE_PATH, 'db.sqlite3'),
            'OPTIONS': {
                'timeout': 60,  # in seconds
            }
        }
    }


DEVICE_IGNORE_THRESHOLD = int(os.getenv('DEVICE_IGNORE_THRESHOLD', 5000))


def GET_DEVICE_ID():
    """
    Return the device id. Use Balena device ID if available.
    """

    if string_to_bool(os.getenv('DEV_MODE', False)):
        return

    if os.getenv('BALENA_DEVICE_UUID', False):
        return os.getenv('BALENA_DEVICE_UUID')

    device_id_file = os.path.join(DATABASE_PATH, 'device_id')
    if not os.path.isfile(device_id_file):
        device_id = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(15))
        with open(device_id_file, 'w') as f:
            f.write(device_id)
    else:
        with open(device_id_file, 'r') as f:
            device_id = f.read()
    return device_id


DEVICE_ID = GET_DEVICE_ID()


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

MIXPANEL_TOKEN = 'bdf69de60cd0602dd2fd760df66b5cc7'

DEV_MODE = os.getenv('DEV_MODE', False)

# The celery container runs in "network_mode: host", so it needs
# different routing to redis
if os.getenv('CELERY') == '1':
    REDIS_HOST = 'localhost'
else:
    REDIS_HOST = 'redis'
REDIS_PORT = 6379
REDIS_DATABASE = 0

CELERY_BROKER_URL = 'redis://{}:{}/{}'.format(
    REDIS_HOST,
    str(REDIS_PORT),
    str(REDIS_DATABASE)
)

CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_IMPORTS = []
CELERY_BEAT_SCHEDULE = {}

if not DISABLE_SCANNING:
    CELERY_IMPORTS.append('ble.tasks')
    CELERY_BEAT_SCHEDULE['ble-scan'] = {
        'task': 'ble.tasks.scan',
        'schedule': crontab(minute='*/5'),
    }

if not DISABLE_ANALYTICS:
    CELERY_IMPORTS.append('analytics.tasks')
    CELERY_BEAT_SCHEDULE['generate-hourly-report'] = {
        'task': 'analytics.tasks.ble_generate_hourly_report',
        'schedule': crontab(minute=10),
    }

    CELERY_BEAT_SCHEDULE['generate-hourly-report-backlog'] = {
        'task': 'analytics.tasks.ble_fill_report_backlog',
        'schedule': crontab(minute='*/10'),
        'args': ('H',)
    }

    CELERY_BEAT_SCHEDULE['generate-daily-report'] = {
        'task': 'analytics.tasks.ble_generate_daily_report',
        'schedule': crontab(minute=5, hour=0),
    }

    CELERY_BEAT_SCHEDULE['generate-daily-report-backlog'] = {
        'task': 'analytics.tasks.ble_fill_report_backlog',
        'schedule': crontab(minute='15'),
        'args': ('D',)
    }

    CELERY_BEAT_SCHEDULE['generate-monthly-report'] = {
        'task': 'analytics.tasks.ble_generate_monthly_report',
        'schedule': crontab(minute=1, hour=3, day_of_month=1),
    }

    CELERY_BEAT_SCHEDULE['generate-monthly-report-backlog'] = {
        'task': 'analytics.tasks.ble_fill_report_backlog',
        'schedule': crontab(minute='25'),
        'args': ('M',)
    }


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
