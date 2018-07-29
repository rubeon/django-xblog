"""
Test settings for xblog unit tests
"""
import os
import logging

from xblog.xmlrpc_settings import XMLRPC_METHODS

LOGGER = logging.getLogger(__name__)
SECRET_KEY = 'fake-key'
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'xblog',
    'markdown_deux',
    'django_xmlrpc'
]
DEBUG=False
SITE_ID=1
ROOT_URLCONF = 'xblog.tests.conf.urls'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


DATABASES = {
    'default': {
        'NAME': 'xblog.db',
        'ENGINE': 'django.db.backends.sqlite3'
    }
}

TEMPLATES = [
    {
        'APP_DIRS': True,
        'DIRS': [os.path.join(BASE_DIR,'templates')],
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'xblog.context_processors.site',

            ],

        }
    }
]

XBLOG_STATUS_CATEGORY_NAME="tweets"

LOGGING = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '[%(levelname)-7s][ %(module)-10s] %(message)s'
        },
        'simple': {
            'format': '[%(levelname)-7s][%(module)-10s] %(message)s'
        },
        'testing': {
            'format': '[%(levelname)-7s][%(module)-10s] %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
            },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'test_output.log'),
            'formatter': 'simple'
            },
        },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'xblog': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        
    }
}

for mymodule in ['xblog', 'xblog.models', 'xblog.views.metaWeblog']:
    LOGGING['loggers'][mymodule] = {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
    }


# if DEBUG:
#     # make all loggers use the console.
#     for logger in LOGGING['loggers']:
#         LOGGING['loggers'][logger]['handlers'] = ['console']
