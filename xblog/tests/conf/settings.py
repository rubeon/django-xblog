"""
Test settings for xblog unit tests
"""
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
    'bootstrap3',
    'markdown_deux',
    'django_xmlrpc'
]
DEBUG=True
SITE_ID=1
ROOT_URLCONF = 'xblog.tests.conf.urls'

from xblog.xmlrpc_settings import XMLRPC_METHODS

DATABASES = {
    'default': {
        'NAME': 'xblog.db',
        'ENGINE': 'django.db.backends.sqlite3'
    }
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
            ],
            'loaders': [
                ['django.template.loaders.cached.Loader', [
                    'django.template.loaders.app_directories.Loader']
                 ]
            ]
        }
    }
]

XBLOG_STATUS_CATEGORY_NAME="tweets"

LOGGING = {
    'version': 1,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
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
            'filename': 'file.log',
            'formatter': 'simple'
            },
        },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'WARN',
            'propagate': True,
            },
        'xblog': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propogate': True,
        }
        }
    }

if DEBUG:
    # make all loggers use the console.
    for logger in LOGGING['loggers']:
        LOGGING['loggers'][logger]['handlers'] = ['console']
