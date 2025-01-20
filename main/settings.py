"""
Django settings for main project.

Generated by 'django-admin startproject' using Django 4.2.17.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-qi)-dj-w(c)6o$841j&zjrn-v4x-a3^_rgynt1#=$eqmf6d@j7"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True




# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'channels',

    # Local apps
    'core.apps.CoreConfig',
    'menu.apps.MenuConfig',
    'orders.apps.OrdersConfig',
    'accounts.apps.AccountsConfig',
    'reservations.apps.ReservationsConfig',
    'restaurant_admin.apps.RestaurantAdminConfig',
    'giftcards.apps.GiftcardsConfig',
    'websockets.apps.WebsocketsConfig',
]

MIDDLEWARE = [

    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'reservations.middleware.ClearMessagesMiddleware',
    'restaurant_admin.middleware.StoreStatusMiddleware',
]

ROOT_URLCONF = "main.urls"

# Add to settings.py
TEMPLATE_CONTEXT_PROCESSORS = [
    'django.template.context_processors.debug',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # This line is important
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

WSGI_APPLICATION = "main.wsgi.application"

ASGI_APPLICATION = "main.asgi.application"
# WebSocket settings
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
        "CONFIG": {
            "capacity": 1500,  # Maximum number of messages that can be stored
        },
    },
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'websocket.log',
        },
    },
    'loggers': {
        'websockets': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}






# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/Chicago"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/



STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"





# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Add these settings for better error handling
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']


# settings.py
# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'jithendrakatta9999@gmail.com'
EMAIL_HOST_PASSWORD = 'ilff ejjh xbsu nrqq'
DEFAULT_FROM_EMAIL = 'jithendrakatta9999@gmail.com'  # Changed this to be a string directly
RESTAURANT_ORDER_EMAIL = 'jithendrakatta9999@gmail.com'


# Add these settings at the bottom of settings.py
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'core:home'


# Stripe Settings (Online Payments)
STRIPE_PUBLIC_KEY = 'pk_test_51QciW6BOuHJ2aMNu6NDdF9c32oVzEyOXUiKn7XBZrFJE9PgQkZ2etWWeJ6G5z8es221KuMYIBpV1vfhIR6ZmeW1Q00jbNBemb0'
STRIPE_SECRET_KEY = 'sk_test_51QciW6BOuHJ2aMNuSUkM73JrrRhkc2tDqF3cMZmZXRU9JqLkAJdma4Q7gwCjCzOlJAV1JoX92uYBoifU7fqFViXL0059Bdo727'
STRIPE_WEBHOOK_SECRET = None

# PayPal Settings
PAYPAL_CLIENT_ID = 'your_paypal_client_id'
PAYPAL_CLIENT_SECRET = 'your_paypal_client_secret'
PAYPAL_MODE = 'sandbox'  # Change to 'live' for production

# Apple Pay Settings
APPLE_PAY_MERCHANT_ID = 'your_merchant_id'
APPLE_PAY_DOMAIN = 'your_domain.com'

