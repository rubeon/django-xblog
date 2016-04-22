# django-xblog
Blogging application for your Django site

## Installation

From github: 

```bash

    pip install https://github.com/rubeon/django-xblog/archive/master.zip

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
cd mysite
vi mysite/settings

```

```python

    INSTALLED_APPS = [
        ...
        'django.contrib.staticfiles',
        # following are for xblog
        'django.contrib.sites',
        'bootstrap3',
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

## Creating users

XBlog uses the Django authentication framework to keep track of users.  Users are linked to Authors, which can serve as the User profile model.

```bash



````


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