XBlog
=====

This is a messy blogging system for Django.  It was originally designed to 
work tightly with a couple of related projects, XComments and XGallery.

It has some interesting features, including Blogging API support for:

- Metaweblog

- Wordpress

- MovableType

This project is intended to fix up that support, and modernize it for current
versions of Django.

Development
-----------

Setting up a developer environment is easy using pip and virtualenv:

    mkdir ~/code/xblog_dev
    cd  ~/code/xblog_dev
    virtualenv .
    . bin/activate
    pip install -r xblog/requirements.txt

Start a test project
    
    django-admin startproject xblog_dev
    cd xblog_dev
    
Get the xblog code:
    
    git clone git@github.com:rubeon/xblog.git
    
Settings
--------

Add xblog and it's dependencies to your list of applications:

    INSTALLED_APPS = (
        ...
        'django.contrib.sites', # dependency
        'markdown_deux', # dependency
        'bootstrap3', # dependency
        'xblog', # dependency
        )
    SITE_ID=1 # SITE_ID should be set up here.
Choose a path on your site for the blog, and update `urls.py` accordingly:
    
        url(r'^blog/', include('xblog.urls'), name='blog'),

Create your dev environment's database:

        ./manage.py syncdb
    
If you're going to be using xmlrpc API access, add the following settings to settings.py:

    XMLRPC_METHODS = (
        ('xblog.metaWeblog.blogger_deletePost', 'blogger.deletePost'),
        ('xblog.metaWeblog.blogger_getRecentPosts', 'blogger.getRecentPosts'),
        ('xblog.metaWeblog.blogger_getUserInfo', 'blogger.getUserInfo'),
        ('xblog.metaWeblog.blogger_getUsersBlogs', 'blogger.getUsersBlogs'),
        ('xblog.metaWeblog.wp_getUsersBlogs', 'wp.getUsersBlogs'),
        ('xblog.metaWeblog.wp_getOptions', 'wp.getOptions'),
        ('xblog.metaWeblog.metaWeblog_editPost', 'metaWeblog.editPost'),
        ('xblog.metaWeblog.metaWeblog_getCategories', 'metaWeblog.getCategories'),
        ('xblog.metaWeblog.metaWeblog_getPost', 'metaWeblog.getPost'),
        ('xblog.metaWeblog.metaWeblog_getRecentPosts', 'metaWeblog.getRecentPosts'),
        ('xblog.metaWeblog.metaWeblog_getUsersBlogs', 'metaWeblog.getUsersBlogs'),
        ('xblog.metaWeblog.metaWeblog_newMediaObject', 'metaWeblog.newMediaObject'),
        ('xblog.metaWeblog.metaWeblog_newPost', 'metaWeblog.newPost'),
        ('xblog.metaWeblog.mt_getCategoryList', 'mt.getCategoryList'),
        ('xblog.metaWeblog.mt_getPostCategories', 'mt.getPostCategories'),
        ('xblog.metaWeblog.mt_publishPost', 'mt.publishPost'),
        ('xblog.metaWeblog.mt_setPostCategories', 'mt.setPostCategories'),
        ('xblog.metaWeblog.mt_supportedMethods', 'mt.supportedMethods'),
        ('xblog.metaWeblog.mt_supportedTextFilters', 'mt.supportedTextFilters'),
        ('xblog.metaWeblog.wp_getUsersBlogs', 'wp.getUsersBlogs'),
        ('xblog.metaWeblog.wp_getOptions', 'wp.getOptions'),
        ('xblog.metaWeblog.wp_getTags', 'wp.getTags'),
        ('xblog.metaWeblog.wp_newPost', 'wp.newPost'),
    )
    
Templates
---------

Your base.html template should contain the following blocks for `xblog`:

* `{% block extrahead %}`: Contains meta tags and stylesheet information  

* {% block subpagetitle %}blog{% endblock %} - can be used to append to the pages `title` tag

* 


Installation
------------

On Ubuntu 12.04, this is fairly easy to install. 

    $ sudo apt-get install python-django git python-markdown python-beautifulsoup
    $ mkdir -p ~/dev/x/
    $ cd ~/dev/x/
    $ django-admin startproject mysite
    $ cd mysite
    $ git clone https://github.com/rubeon/xblog.git
    
Create a file in the project directory (e.g., ~/dev/x/mysite) called 
`settings_local.py` with the following settings:


    DEBUG=True
    TEMPLATE_DEBUG=True
    SITE_URL = "http://youbitch.rupert.subcritical.org/"
    INSTALLED_APPS = (
        'django.contrib.auth',
        'django.contrib.admin',
        'django.contrib.contenttypes',
        'django.contrib.flatpages',
        'django.contrib.markup',  
        'django.contrib.sessions',
        'django.contrib.sitemaps',
        'django.contrib.sites',
        'xblog',
        # 'common.xcomments',   
        # 'common.xgallery',
    )

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3', 
            'NAME': 'mysite.db',
        }
    }

    TIME_ZONE="Europe/London"
    ROOT_URLCONF='mysite.urls'    


Edit the urls.py so that /blog and /admin are defined:

    urlpatterns = patterns('',
        # Uncomment the next line to enable the admin:
        url(r'^admin/', include(admin.site.urls)),
        (r'^blog/',include('xblog.urls')),
     
    )

In the bottom of settings.py for your site, you can import this file's contents:

    from settings_local import *

Setup the database:

    PYTHONPATH=$PWD:$PWD/.. python manage.py syncdb



Next, create a script to run the server in local mode for debugging:

    #!/bin/bash

    PYTHONPATH=$PWD:$PWD/.. python manage.py runserver 0.0.0.0:9111

