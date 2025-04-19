"""

Implementation of the WordPress XMLRPC API for XBlog.

Factored out of ../metaWeblog.py for reasons.

Being factored out of ../metaWeblog.py for reasons.

Currently a work in progress


"""
import logging
import datetime
import django.utils.timezone

import os
try:
    from xmlrpc.client import Fault
    from urllib.parse import urljoin
except ImportError:  # Python 2
    from xmlrpclib import Fault
    from urlparse import urljoin
import django

from django.urls import reverse
from django.core import exceptions
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.contrib.flatpages.models import FlatPage

from ..models import Blog
from ..models import Post
from ..models import Category
from ..models import Author
from ..models import Tag
from ..models import STATUS_CHOICES, FORMAT_CHOICES
from .utils import get_user

LOGGER = logging.getLogger("xblog.views.%s" % __name__)

LOGIN_ERROR = 801
PERMISSION_DENIED = 803

def wp_login(func):
    def wrapper(*args, **kwargs):
        blog_id = args[0]
        username = args[1]
        password = args[2]
        user = get_user(username, password)
        blog = Blog.objects.filter(owner=user)[int(blog_id)]
        return func(blog, user, *args[3:], **kwargs)
    return wrapper

def _setTags(post, struct, key="tags"):
    LOGGER.debug( "setTags entered")
    tags = struct.get(key, None)
    LOGGER.debug("Got tags %s", tags)

    if tags is None:
        LOGGER.info("No tags set")
        post.tags = []
    else:
        # post.categories = [Category.objects.get(title__iexact=name) for name in tags]
        LOGGER.info("Setting tags")
        for tag in tags:
            LOGGER.debug("setting tag '%s'", tag)
            if tag != '':
                LOGGER.debug("creating tag '%s'", tag)
                t, created = Tag.objects.get_or_create(title=tag.lower())
                if created:
                    LOGGER.info("Adding new tag: %s", t)
                else:
                    LOGGER.info("Using existing tag %s", t)
                t.save()
                post.tags.add(t)
                post.save()
            else:
                LOGGER.debug("Tag was blank, skipping...")
    LOGGER.debug("Post Tags: %s", str(post.tags))
    post.save()
    return True

def _get_default_blog(user):
    LOGGER.debug("_get_default_blog entered")
    blog = Post.objects.filter(author=user.author).order_by('-pub_date')[0].blog
    return blog

def check_perms(user, obj):
    LOGGER.debug("%s.check_perms entered", __name__)
    if isinstance(obj, Post):
        if obj.author.user != user and not user.is_superuser:
            raise Fault(PERMISSION_DENIED, 'Permission denied for %s on post %s' % (user, obj.id))
    elif isinstance(obj, Blog):
        if obj.owner != user and not user.is_superuser:
            raise Fault(PERMISSION_DENIED, 'Permission denied for %s on post %s' % (user, obj.id))
    else:
        raise Fault(PERMISSION_DENIED, 'Permission denied for %s unknown object %s' % (user, obj))
    LOGGER.debug("No permissions issues found")

def _term_taxonomy(term):
    """
    Determine term_taxonomy_id for a given object
    Based on contenttypes
    """
    LOGGER.debug("%s._term_taxonomy entered", __name__)
    # get the content type
    if term.__class__ == Tag:
        term_id = term.id
        name = "post_tag"
    else:
        ctype = ContentType.objects.get_for_model(term)
        term_id = term.id
        name = ctype.name


    res = {'id':term_id, 'name':name}
    LOGGER.debug("res: %s", res)

    return res


def _term_struct(term):
    LOGGER.debug("%s._term_struct entered", __name__)
    struct = {
        '_builtin': True,
        'description': getattr(term, 'description', ''),
        'filter': 'raw',
        'name': term.title,
        'parent': '0',
        'slug': getattr(term, 'slug', term.title),
        'taxonomy': _term_taxonomy(term)['name'],
        'term_group': '0',
        'term_id': term.id,
        # 'term_taxonomy_id': _term_taxonomy(term)['id'],
        'term_taxonomy_id': term.id,
    }
    LOGGER.debug("_term_struct: %s", str(struct.keys()))
    return struct


def _post_struct(post):
    """
    creates a struct for calls:
    - getPost
    """
    LOGGER.debug("%s._post_struct entered",  __name__)
    status = post.status
    res = {}
    res['post_id'] = post.id
    res['post_title'] = post.title
    res['post_date'] = post.pub_date
    res['post_date_gmt'] = post.pub_date
    res['post_modified'] = post.update_date
    res['post_modified_gmt'] = post.update_date
    res['post_status'] = status
    res['post_type'] = post.post_type
    res['post_format'] = post.post_format
    res['post_name'] = post.slug
    res['post_author'] = str(post.author.id)
    res['post_password'] = ''
    res['post_excerpt'] = post.summary
    res['post_content'] = post.body
    res['post_parent'] = '0'
    res['post_mime_type'] = ''
    res['link'] = post.get_url()
    res['guid'] = post.guid
    res['menu_order'] = 0 # this might be implemented for flat pages at some point...
    res['comment_status'] = post.enable_comments and "open" or "closed"
    res['ping_status'] = post.enable_pings and "open" or "closed"
    res['sticky'] = post.sticky
    res['post_thumbnail'] = []
    res['terms'] = []
    # add the categories

    for cat in post.categories.all():
        count = cat.posts.count()
        term = _term_struct(cat)
        term['count'] = str(count)
        res['terms'].append(term)

    for tag in post.tags.all():
        count = tag.posts.count()
        term = _term_struct(tag)
        term['count'] = str(count)
        res['terms'].append(term)
    LOGGER.debug("_post_struct: %s", str(res.keys()))
    return res

def getPost(blog_id, username, password, post_id, fields=[]):
    """
    Parameters
    int blog_id
    string username
    string password
    int post_id
    array fields: Optional. List of field or meta-field names to include in response.
    """
    LOGGER.debug("%s.getPost entered")
    LOGGER.debug("fields: %s", str(fields))
    user = get_user(username, password)
    post = Post.objects.get(id=post_id)
    check_perms(user, post)
    return _post_struct(post)

def getPosts(blog_id, username, password, post_filter=None):
    """
    struct filter: Optional.
    string post_type
    string post_status
    int number
    int offset
    string orderby
    string order
    """
    LOGGER.debug("%s.getPosts entered", __name__)
    LOGGER.debug("post_filter: %s", str(post_filter))

    post_type = post_filter.get('post_type', 'post') if post_filter else 'post'
    user = get_user(username, password)

    # handle status?
    statuses = post_filter.get('post_status').split(',') if post_filter else []
    LOGGER.debug("statuses: %s", statuses)
    # handle future
    LOGGER.debug("XXXX: %s", statuses)


    if post_type == 'pageXXX':
        LOGGER.debug("got type page")
        res = []
        for page in FlatPage.objects.all().order_by('title'):
            LOGGER.debug("Got %s", page.title)
            res.append({
                'comment_status': page.enable_comments and 'open' or 'closed',
                'custom_fields': [],
                'guid': page.get_absolute_url(),
                'link': page.get_absolute_url(),
                'ping_status': 'closed',
                'post_author':  user.id,
                'post_content': page.content,
                'post_date': django.utils.timezone(),
                'post_date_gmt': django.utils.timezone(),
                'post_format': 'standard',
                'post_id': page.id,
                'post_modified': django.utils.timezone(),
                'post_modified_gmt': django.utils.timezone(),

                'post_name': page.url,
                'post_parent': '0',
                'post_status': page.registration_required and 'draft' or 'publish',
                'post_thumbnail': [],
                'post_title': page.title,
                'post_type': 'page',
                'sticky': False,
                'terms': [],
            })

        LOGGER.debug("Returning %d pages", len(res))
        return res

    if blog_id == 0:
        # no blog_id given, get the last one with posts by this
        # author
        LOGGER.debug("blog_id=0, looking for posts")
        try:
            blog = Post.objects.filter(author=user.author).order_by('-pub_date')[0].blog
        except Exception as e:
            LOGGER.debug(e.__class__)
            LOGGER.debug(e)
            return []

        LOGGER.debug("got blog %s", blog)
    else:
        blog = Blog.objects.get(id=blog_id)
    check_perms(user, blog)

    # get a list of this user's posts on this blog
    LOGGER.debug("Getting list of posts in blog: %s", blog)
    LOGGER.debug("author: %s", user.author)
    LOGGER.debug("post_type: %s", post_type)
    offset = int(post_filter.get('offset', 0)) if post_filter else 0
    if 'future' in statuses and post_filter.get('number'):
        LOGGER.debug("got future and number")
        limit = int(post_filter.get('number'))
        posts = Post.objects.filter(author=user.author,
                                    blog=blog,
                                    post_type=post_type,
                                    pub_date__gt=django.utils.timezone.now()
                                    ).order_by('-pub_date')[offset:offset+limit]
        LOGGER.debug("Got %s posts", len(posts))
    elif 'future' in statuses:
        LOGGER.debug("got future")
        posts = Post.objects.filter(author=user.author,
                                    blog=blog,
                                    post_type=post_type,
                                    pub_date__gt=django.utils.timezone.now()
                                    ).order_by('-pub_date')[offset:]
    elif post_filter and post_filter.get('number'):
        LOGGER.debug("got number")
        limit = int(post_filter.get('number'))
        posts = Post.objects.filter(author=user.author,
                                    blog=blog,
                                    post_type=post_type,
                                    pub_date__lt=django.utils.timezone.now(),
                                    status__in=statuses).order_by('-pub_date')[offset:offset+limit]
    else:
        posts = Post.objects.filter(author=user.author, 
                                    blog=blog,
                                    post_type=post_type,
                                    pub_date__lt=django.utils.timezone.now(),
                                    status__in=statuses).order_by('-pub_date')[offset:]
    res = []
    for post in posts:
        LOGGER.debug("Adding post %s", post)
        res.append(_post_struct(post))	
    LOGGER.debug("getPosts finished")
    LOGGER.debug(res)
    return res

def newPost(blog_id, username, password, content):
    """
    creates a new post
    returns the post's id
    """
    LOGGER.debug("%s.newPost entered", __name__)
    LOGGER.debug("user: %s", str(username))
    LOGGER.debug("blog_id: %s", str(blog_id))
    LOGGER.debug("content:\n%s", str(content))

    user = get_user(username, password)
    try:
        blog = Blog.objects.get(id=blog_id)
        if blog.owner != user:
            raise Blog.DoesNotExist
    except Blog.DoesNotExist:
        LOGGER.debug("invalid blog id, looking for posts")
        blog = Blog.objects.filter(owner=user)[0]

    check_perms(user, blog)
    LOGGER.info("blog: %s", str(blog))
    pub_date = django.utils.timezone.now()

    LOGGER.info("blog: %s", str(blog))
    LOGGER.info("pub_date: %s", str(pub_date))
    post = Post(
        title=content['post_title'],
        body = content['post_content'],
        create_date = pub_date,
        update_date = pub_date,
        pub_date = pub_date,
        status = content.get('post_status', 'draft'),
        blog = blog,
        author =user.author,
        sticky = content.get('sticky', False),
        post_type = content.get('post_type', 'post')
    )

    post.save()
    LOGGER.info("Post %s saved", post)
    # LOGGER.info("Setting Tags")
    # setTags(post, struct)
    #LOGGER.debug("Handling Pings")
    #LOGGER.info("sending pings to host")
    # send_pings(post)
    # check for tags
    # terms:{name:[type.id]}

    terms = content.get('terms', None)
    if terms:
        struct = {}
        tags = []
        categories = []
        for term, ids in list(terms.items()):
            # tag?
            if ContentType.objects.get_for_model(Tag) in ids:
                print("Tag ID found")
                tags.append(term)
                struct['tags'] = tags

        _setTags(post, struct)
    LOGGER.debug("newPost finished")
    # set categories? Hmm... categories for posts seem to be legacy thinking
    # set tags
    return str(post.id)


def getUser(blog_id, username, password, user_id, fields=[]):
    """
    struct: Note that the exact fields returned depends on the fields parameter.
    string user_id
    string username1
    string first_name
    string last_name
    string bio
    string email1
    string nickname
    string nicename1
    string url
    string display_name1
    datetime registered1
    roles
    """
    LOGGER.debug("getUser entered")
    user = get_user(username, password)
    blog = Blog.objects.get(id=blog_id)
    User = get_user_model()
    target_user = User.objects.get(id=user_id)

    res = {
        'user_id': user_id,
        'username': target_user.username,
        'first_name': target_user.first_name,
        'last_name': target_user.last_name,
        'bio': target_user.author.about,
        'email': target_user.email,
        'nickname': target_user.username,
        'nicename': target_user.author.fullname,
        'url': blog.get_absolute_url(),
        'display_name': target_user.author.fullname,
        'registered': target_user.date_joined,
    }
    return res


def getProfile(blog_id, username, password, fields=[]):
    """
    Return Values
    struct: See #wp.getUser.
    """
    LOGGER.debug("getProfile entered...")
    user = get_user(username, password)
    blog_id = _get_default_blog(user).id

    return getUser(blog_id, username, password, user.id)

def getUsersBlogs(username, password):
    """
    wp.getUsersBlogs
    Retrieve the blogs of the users.

    Parameters
        string username
        string password
    Return Values
        array
            struct
                boolean isAdmin # whether user is admin or not
                string url # url of blog
                string blogid
                string blogName
                string xmlrpc
    """
    LOGGER.debug( "wp.getUsersBlogs called")
    user = get_user(username, password)
    # print "Got user", user
    usersblogs = Blog.objects.filter(owner=user)
    LOGGER.debug( "%s blogs for %s", usersblogs, user)
    # return usersblogs
    res = [
    {
        'isAdmin': True,
        'url': f"https://{blog.site.domain}/blog/{user.username}/",
        'blogid':str(blog.id),
        'blogName': blog.title,
        # 'xmlrpc': reverse("xmlrpc"),
        # non-ssl for debug
        'xmlrpc': f"https://{blog.site.domain}{reverse('xmlrpc')}"
    } for blog in usersblogs ]
    LOGGER.debug(res)
    return res

def getCategories(blog_id, username, password):
    """
    Parameters
        int blog_id
        string username
        string password
    Return Values
        array
            struct
                int categoryId
                int parentId
                string description
                string categoryName
                string htmlUrl
                string rssUrl
    example from wordpress.com
    [{'categoryDescription': '',
      'categoryId': 1356,
      'categoryName': 'Blogroll',
      'description': 'Blogroll',
      'htmlUrl': 'https://rubelongfellow.wordpress.com/category/blogroll/',
      'parentId': 0,
      'rssUrl': 'https://rubelongfellow.wordpress.com/category/blogroll/feed/'},
     {'categoryDescription': '',
      'categoryId': 42431,
      'categoryName': 'Gearhead',
      'description': 'Gearhead',
      'htmlUrl': 'https://rubelongfellow.wordpress.com/category/gearhead/',
      'parentId': 0,
      'rssUrl': 'https://rubelongfellow.wordpress.com/category/gearhead/feed/'},
     {'categoryDescription': '',
      'categoryId': 1,
      'categoryName': 'Uncategorized',
      'description': 'Uncategorized',
      'htmlUrl': 'https://rubelongfellow.wordpress.com/category/uncategorized/',
      'parentId': 0,
      'rssUrl': 'https://rubelongfellow.wordpress.com/category/uncategorized/feed/'}]
    """
    LOGGER.debug("%s.getCategories entered", __name__)
    res = []
    user = get_user(username, password)
    blog = Blog.objects.get(pk=blog_id)

    check_perms(user, blog)

    LOGGER.debug("getting categories for %s", blog)

    for cat in Category.objects.filter(blog=blog):
        res.append({
            'categoryDescription': cat.description,
            'categoryId': cat.id,
            'categoryName': cat.title,
            'description': cat.description,
            'htmlUrl': cat.blog.get_absolute_url(),
            'parentId': 0,
            'rssUrl': os.path.join(cat.blog.get_absolute_url(), "feed"),
        })

    return res

def getOptions(blog_id, username, password, options=None):
    """
    int blog_id
    string username
    string password
    struct
        string option
    return:
        array
        struct
            string desc
            string readonly
            string option
    """
    LOGGER.debug("wp.getOptions entered")
    LOGGER.debug("user: %s", username)
    LOGGER.debug("blog_id: %s", blog_id)
    LOGGER.debug("struct: %s", options)
    user = get_user(username, password)
    try:
        blog = Blog.objects.get(pk=blog_id)
    except exceptions.ObjectDoesNotExist as e:
        LOGGER.debug("Blog with id %s not found, trying other methods...", blog_id)
        blog = Blog.objects.filter(owner=user)[int(blog_id)] # *shrug*
    if blog.owner != user:
        # seems to be a misbehavior in DeskPM
        # get the user's own blog
        LOGGER.warn("Incorrect blog id passed, finding user's blog")
        blog = Blog.objects.filter(owner=user)[0]
        LOGGER.debug("Using blog with id %s", str(blog.id))
    check_perms(user, blog)
    admin_url = {
        'value': urljoin(blog.get_url(), "admin"),
        'desc': "The URL to the admin area",
        'readonly': True,
    }



    res = {
        'admin_url':admin_url,
        'blog_tagline' : {'desc': 'Site Tagline', 'readonly': False, 'value': blog.description },
        'blog_title': {'desc': 'Site title', 'readonly': False, 'value': blog.title },
        'blog_url' : { 'desc': 'Blog Address (URL)', 'readonly': True, 'value': blog.get_absolute_url() },
        # 'date_format': {'desc': 'Date Format', 'readonly':False, 'value': 'F j, Y'},
        'default_comment_status': { 'desc': 'Allow people to submit comments on new posts', 
                                    'readonly': False, 
                                    'value': 'open' if blog.default_comments_status else 'closed'},
        'default_ping_status': {'desc': 'Allow link notifications from other blogs (pingbacks and trackbacks) on new posts', 
                                'readonly': False, 
                                'value': 'open' if blog.default_ping_status else 'closed'},
        'home_url': {'desc': 'Site address URL', 
                     'readonly': True, 
                     'value': f"https://{blog.site.domain}/"}
        # 'image_default_align': {'desc': 'Image default align', 'readonly': True, 'value': ''},
        # 'image_default_link_type': {'desc': 'Image default link type', 'readonly': True, 'value': 'file'},
        # 'image_default_size': {'desc': 'Image default size', 'readonly': True, 'value': ''},
        # 'large_size_h': {'desc': 'Large size image height', 'readonly': False, 'value': '1024'},
        # 'large_size_w': {'desc': 'Large size image width', 'readonly': False, 'value': '1024'},
        # 'login_url' : {'desc': 'Login Address (URL)', 'readonly': True, 'value': admin_url},
        # 'medium_large_size_h': {'desc': 'Medium-Large size image height', 'readonly': False, 'value': '0'},
        # 'medium_large_size_w': {'desc': 'Medium-Large size image width', 'readonly': False, 'value': '768'},
        # 'medium_size_h': {'desc': 'Medium size image height', 'readonly': False, 'value': '300'},
        # 'medium_size_w': {'desc': 'Medium size image width', 'readonly': False, 'value': '300'},
        # 'post_thumbnail': {'desc': 'Post Thumbnail', 'readonly': True, 'value': True},
        # 'software_name': {'desc': 'Software Name', 'readonly': True, 'value': 'XBlog'},
        # 'software_version': {'desc': 'Software Version', 'readonly': True, 'value': '4.2.2'},
        # 'stylesheet': {'desc': 'Stylesheet', 'readonly': True, 'value': 'django-bootstrap3'},
        # 'template': {'desc': 'Template', 'readonly': True, 'value': 'ehwio'},
        # 'thumbnail_crop': {'desc': 'Crop thumbnail to exact dimensions', 'readonly': False, 'value': '1'},
        # 'thumbnail_size_h': {'desc': 'Thumbnail Height', 'readonly': False, 'value': '150'},
        # 'thumbnail_size_w': {'desc': 'Thumbnail Width', 'readonly': False, 'value': '150'},
        # 'time_format': {'desc': 'Time Format', 'readonly': False, 'value': 'g:i a'},
        # 'time_zone': {'desc': 'Time Zone', 'readonly': False, 'value': '0'},
        # 'users_can_register': {'desc': 'Allow new users to sign up', 'readonly': False, 'value': True},
    }

    # debug
    LOGGER.debug("res: %s", res)
    LOGGER.info("Finished wp.getOptions")
    return res

def newTerm(blog_id, username, password, struct):
    """
    wp.newTerm
    Parameters
        int blog_id
        string username
        string password
        struct content
            string name
            string taxonomy
            string slug: Optional.
            string description: Optional.
            int parent: Optional.
    Return Values
        string term_id
    """
    LOGGER.debug("newTerm entered")
    LOGGER.debug(struct)
    user = get_user(username, password)
    blog = Blog.objects.filter(owner=user)[int(blog_id)]
    check_perms(user, blog)
    new_struct = {
        "name": struct['name'],
    }
    if struct.get('slug'):
        new_struct['slug'] = struct['slug']

    new_struct['description'] = struct.get('description') or ''
    return newCategory(blog.id, username, password, new_struct)

def newCategory(blog_id, username, password, struct):
    """

    """
    LOGGER.debug("newCategory entered...")
    user = get_user(username, password)
    blog = Blog.objects.get(id=blog_id)
    check_perms(user, blog)

    c = Category(
            title=struct['name'],
            description=struct['description'],
            blog=blog
        )
    c.save()
    return c.id

def getTerm(blog_id, username, password, taxonomy, term_id):
    """
    Parameters
        int blog_id
        string username
        string password
        string taxonomy
        int term_id
    Return Values
        struct: See get_term.
        string term_id
        string name
        string slug
        string term_group
        string term_taxonomy_id
        string taxonomy
        string description
        string parent
        int count

    struct:


    """
    LOGGER.debug("getTerm entered")
    LOGGER.debug("blog_id %s", blog_id)
    LOGGER.debug("username: %s", username)
    LOGGER.debug("taxonomy: %s", taxonomy)
    LOGGER.debug("term_id: %s", term_id)

# def getTerms(*args, **kwargs):

@wp_login
def getTerms(blog, user, taxonomy, term_filter=None):
    """
    Parameters
        int blog_id
        string username
        string password
        string taxonomy
        int term_id
        struct filter: Optional.
           int number
           int offset
           string orderby
           string order
           bool hide_empty: Whether to return terms with count=0.
           string search: Restrict to terms with names that contain (case-insensitive) this value.
    Return Values
        struct: See get_term.
        string term_id
        string name
        string slug
        string term_group
        string term_taxonomy_id
        string taxonomy
        string description
        string parent
        int count

    number:

    """
    LOGGER.debug("getTerms entered...")
    LOGGER.debug("got user %s", user)
    if term_filter:
        LOGGER.debug("Got term_filter: %s", term_filter)
    res = []
    if taxonomy == 'category':
        LOGGER.debug("Asked for categories!")
        category_list = Category.objects.filter(blog=blog)
        res = []
        for cat in category_list:
            LOGGER.debug("Processing %s", cat)
            res.append({
                'count': cat.posts.count(),
                'custom_fields': [],
                'description': cat.description,
                'filter': 'raw',
                'name': cat.title,
                'parent': 0,
                'slug': cat.slug,
                'taxonomy': 'category',
                'term_group': 0,
                'term_id': cat.id,
                'term_taxonomy_id': cat.id,
            })
        LOGGER.debug(res)
    elif taxonomy == 'post_tag':
        res = []
        LOGGER.debug("Asked for tags!")
        tag_list = Tag.objects.all()
        for tag in tag_list:
            LOGGER.debug("Adding tag %s", tag)
            res.append({
                'count': tag.posts.count(),
                'custom_fields': [],
                'description': tag.title,
                'filter': 'raw',
                'name': tag.title,
                'slug': tag.slug,
                'taxonomy': 'post_tag',
                'term_group': 0,
                'term_id': tag.id,
                'term_taxonomy_id': tag.id,
            })
        LOGGER.debug(res)
    return res

@wp_login
def getTaxonomies(blog, user):
    """
    Retrn Values
      string name
      string label
      bool hierarchical
      bool public
      bool show_ui
      bool _builtin
      struct labels1
      struct cap2
      array object_type3
    """
    LOGGER.debug("getTaxonomies entered...")
    # if blog_id == '0':
    #   blog = Blog.objects.filter(owner=user)[int(blog_id)]
    # get the Categories
    res = []
    res.append({
                 '_builtin': True,
                 'cap': {'assign_terms': 'assign_categories',
                        'delete_terms': 'delete_categories',
                        'edit_terms': 'edit_categories',
                        'manage_terms': 'manage_categories'},
                 'hierarchical': False,
                 'label': 'Categories',
                 'labels': {'add_new_item': 'Add New Category',
                 'add_or_remove_items': '',
                 'all_items': 'All Categories',
                 'back_to_items': '&larr; Go to Categories',
                 'choose_from_most_used': '',
                 'desc_field_description': 'The description is not prominent by '
                                           'default; however, some themes may show '
                                           'it.',
                 'edit_item': 'Edit Category',
                 'filter_by_item': 'Filter by category',
                 'item_link': 'Category Link',
                 'item_link_description': 'A link to a category.',
                 'items_list': 'Categories list',
                 'items_list_navigation': 'Categories list navigation',
                 'menu_name': 'Categories',
                 'most_used': 'Most Used',
                 'name': 'Categories',
                 'name_admin_bar': 'category',
                 'name_field_description': 'The name is how it appears on your '
                                           'site.',
                 'new_item_name': 'New Category Name',
                 'no_terms': 'No categories',
                 'not_found': 'No categories found.',
                 'parent_field_description': 'Assign a parent term to create a '
                                             'hierarchy. The term Jazz, for '
                                             'example, would be the parent of '
                                             'Bebop and Big Band.',
                 'parent_item': 'Parent Category',
                 'parent_item_colon': 'Parent Category:',
                 'popular_items': '',
                 'search_items': 'Search Categories',
                 'separate_items_with_commas': '',
                 'singular_name': 'Category',
                 'slug_field_description': 'The &#8220;slug&#8221; is the '
                                           'URL-friendly version of the name. It '
                                           'is usually all lowercase and contains '
                                           'only letters, numbers, and hyphens.',
                 'update_item': 'Update Category',
                 'view_item': 'View Category'},
                 'name': 'category',
                'object_type': ['post'],
                'public': True,
                'show_ui': True
            })

    return res

@wp_login
def getTaxonomy(blog, user, taxonomy):
    """
    """
    LOGGER.debug("getTaxonomy entered...")
    LOGGER.debug("taxonomy: %s", taxonomy)
    return {}

@wp_login
def getUsers(blog, user, struct):
    """
    """
    LOGGER.debug("getUsers entered...")
    LOGGER.debug("struct: %s", struct)
    """
    [{'bio': '',
    'display_name': 'eric',
    'email': 'eric@subcritical.org',
    'first_name': '',
    'last_name': '',
    'nicename': 'eric',
    'nickname': 'eric',
    'registered': <DateTime '20230518T22:40:42' at 0x104678eb0>,
    'roles': ['administrator'],
    'url': 'https://subcritical.org',
    'user_id': '1',
    'username': 'eric'}]
    """
    res = []
    count = 0 # dummy id
    offset = struct.get('offset')
    for author in Author.objects.all().order_by('fullname'):

        count = count + 1
        if offset and offset > count:
            continue
        res.append({'bio': author.about,
                    'display_name': author.fullname,
                    'email': author.user.email,
                    'first_name': author.user.first_name,
                    'last_name': author.user.last_name,
                    'nicename': author.fullname,
                    'nickname': author.user.username,
                    'registered': author.user.date_joined,
                    'roles': ['administrator'],
                    'url': author.url,
                    'user_id': count,
                    'username': author.user.username})
    LOGGER.debug(res)
    return res

@wp_login
def getComments(*args, **kwargs):
    """
    meh.
    """
    return []
@wp_login
def getPostFormats(blog, user, format_filter=None):
    """
    """
    LOGGER.debug("getPostFormats entered...")
    LOGGER.debug("user: %s", user)
    LOGGER.debug("format_filter: %s", str(format_filter))
    all_filters = {}
    for k, v in FORMAT_CHOICES:
        all_filters[k] = v

    if format_filter and format_filter.get('show-supported'):
        res = {
            'all': all_filters,
            'supported': list(all_filters.keys())
        }

    else:
        res = all_filters
    LOGGER.debug(res)
    return res

@wp_login
def getPostStatusList(blog, user):
    """
    array(
      'draft'   => 'Draft',
      'pending' => 'Pending Review',
      'private' => 'Private',
      'publish' => 'Published'
    );

    """
    LOGGER.debug("getPostStatusList entered")
    LOGGER.debug("user: %s", user)
    LOGGER.debug("blog: %s", blog)
    res = {}
    for k, v in STATUS_CHOICES:
        res[k] = v

    return res

@wp_login
def deletePost(blog, user, post_id):
    """
    parameters:
    blog
    user
    post_id
    
    Delete an existing post of any registered post type.

    See wp_delete_post for exact behavior based on post type.
    
    """
    LOGGER.debug("deletePost entered")
    LOGGER.debug("post_id: %s", post_id)
    post = Post.objects.get(id=int(post_id))
    check_perms(user, post)
    if post.status == 'trash':
        LOGGER.info("Post already in trash, deleting...")
        post.delete()
    else:
        LOGGER.info("Moving post %s to trash", post)
        post.status = 'trash'
        post.save()
    return True
    