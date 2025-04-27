# django-xblog
Blogging application for your Django site

## Build Status

[![Run Python Tests](https://github.com/rubeon/django-xblog/actions/workflows/ci.yml/badge.svg)](https://github.com/rubeon/django-xblog/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/django-xblog)](https://pypi.org/project/django-xblog/)

## Installation

Install from PyPi:

```bash

    pip install django-xblog

```

Using git:

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

```bash

django-admin startproject mysite
cd mysite/
vi mysite/settings

```
Add the dependencies to `INSTALLED_APPS`:
```python

    INSTALLED_APPS = [
        ...
        # following are for xblog
        'django.contrib.sites',
        'markdown_deux',
        'xblog',
	'django_xmlrpc_dx',
    ]
    # Define a site, if not done already!
    SITE_ID=1
    MIDDLEWARE = [
        # add sites middleware
        # ...
        'django.contrib.sites.middleware.CurrentSiteMiddleware',
    ]

```

```bash

./manage.py migrate
./manage.py createsuperuser --username=admin --email=admin@example.com
Password:
Password (again):
Superuser created successfully.
./manage.py runserver 
```

## URL Setup

Add a place to your site's root `urls.py` reach your blog, and don't forget to
add the `xblog` namespace:

```python
    from django.urls import path, include
    import xblog.urls

    urlpatterns = [
        path('admin/', admin.site.urls),
        path('blog/', include(xblog.urls, namespace="xblog"),
    ]
```

## Creating users

XBlog uses the Django authentication framework to keep track of users.  `Users`
are linked to `Authors`, which can serve as the User profile model.

Author profiles are created automatically in the `User` model's `post_save`
signal. See `xblog/models.py:create_profile` for reference.

## Adding to your templates

XBlog defines the following content blocks:

* `maincontent` - the main Blog content with archives, posts, etc.

* `rightnav` - Blog roll, archive links, etc.

* `leftnav` - navigation block including ...(FIXME: whut?)

* `extrahead` - adds meta tags depending on the content being shown:

```html
<title>subcritical.org::{% block subpagetitle %}top{% endblock %}</title>
{% block extrahead %}{% endblock %}
```

* `subpagetitle` - returns title of article or archive

```html
<title>subcritical.org::{% block subpagetitle %}top{% endblock %}</title>
```

* `pagestyle` - can be placed in `body` tag for CSS styling:

```html
<body class="{% block pagestyle}{% endblock %}">
```

* `blogheaders` - Returns metadata about blog, such as EditURI, author, etc., for you HTML `<head>` section

	<title>subcritical.org::{% block subpagetitle %}top{% endblock %}</title>
	{% block extrahead %}{% endblock %}

* `navigation` - Can be pulled into your navigation block to allow blog-specific navigation elements:

```html

<nav>
	<ul>
	  <li>Top</li>
    	{% block navigation %}{% endblock %}
	</ul>
</nav>

```
