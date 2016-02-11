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