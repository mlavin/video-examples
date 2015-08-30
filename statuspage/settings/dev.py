"""Settings for local development and testing."""
import sys

from .base import *  # noqa

DEBUG = True

SECRET_KEY = 'f@$t8g67yc0%npk4t69kfaky7cl@4*1*d37y2!56%uhl6z1_hh'

INTERNAL_IPS = ('127.0.0.1', )

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

if 'test' in sys.argv:
    # Special settings for running the tests
    PASSWORD_HASHERS = (
        'django.contrib.auth.hashers.SHA1PasswordHasher',
        'django.contrib.auth.hashers.MD5PasswordHasher',
    )
