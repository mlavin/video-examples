"""Settings for live deployed environments: stating, qa, production, etc."""
from .base import *  # noqa

DEBUG = False

SECRET_KEY = os.environ['SECRET_KEY']

ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS'].split(';')

STATIC_ROOT = os.path.join(BASE_DIR, 'public', 'static')

MEDIA_ROOT = os.path.join(BASE_DIR, 'public', 'media')

# Security settings

SSL_ENABLED = not os.environ.get('SSL_DISABLED', False)

SECURE_SSL_REDIRECT = SSL_ENABLED

SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365 if SSL_ENABLED else 0

SECURE_BROWSER_XSS_FILTER = True

SECURE_CONTENT_TYPE_NOSNIFF = True

SESSION_COOKIE_SECURE = SSL_ENABLED

SESSION_COOKIE_HTTPONLY = True

CSRF_COOKIE_SECURE = SSL_ENABLED

CSRF_COOKIE_HTTPONLY = True

X_FRAME_OPTIONS = 'DENY'
