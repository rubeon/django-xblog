# django-xblog
Blogging application for your Django site

## Installation

```bash
    mkdir blog_project
    cd blog_project
    virtualenv .
    . bin/activate
    git clone git@github.com:rubeon/django-xblog.git
    cd django-xblog
    python setup install
```


This will install xblog and its requirements.

## Creating a Site

After the above, go through the usual process:

django-admin startproject mysite
cd mysite
vi mysite/settings

```python

    INSTALLED_APPS = [
        ...
        'django.contrib.staticfiles',
        # following are for xblog
        'django.contrib.sites',
        'markdown_deux',
        'xblog',
    ]
    # Define a site, if not done already!
    SITE_ID=1
_

```

## URL Setup

Add a place to your site's root `urls.py` reach your blog:

```python
    import xblog.urls
    
    urlpatterns = [
        url(r'^admin/', admin.site.urls),
        url(r'^blog/', xblog.urls),
    ]
```