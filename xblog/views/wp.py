"""

Implementation of the WordPress XMLRPC API for XBlog.

Factored out of ../metaWeblog.py for reasons.

Being factored out of ../metaWeblog.py for reasons.

Currently a work in progress


"""
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
import django

from ..models import Blog
from ..models import Post
from ..models import Category
from ..models import Link
from ..models import LinkCategory
from ..models import Author
from ..models import Tag

try:
    from xmlrpc.client import Fault
    from xmlrpc.client import DateTime
except ImportError:  # Python 2
    from xmlrpclib import Fault
    from xmlrpclib import DateTime

import logging
import datetime
import urlparse
import os

logger = logging.getLogger(__name__)

# setup a translator for WP<->Xblog post types
type_map = {
    'standard':'post',
    'video':'video',
    'status':'aside'
}

LOGIN_ERROR = 801
PERMISSION_DENIED = 803

def _setTags(post, struct, key="tags"):
    logger.debug( "setTags entered")
    tags = struct.get(key, None)
    if tags is None:
        logger.info("No tags set")
        post.tags = []
    else:
        # post.categories = [Category.objects.get(title__iexact=name) for name in tags]
        logger.info("Setting tags")
        for tag in tags:
            logger.debug("setting tag '%s'" % tag)
            t, created = Tag.objects.get_or_create(title=tag.lower())
            if created:
                logger.info("Adding new tag: %s" % t)
            else:
                logger.info("Found tag: %s" % t)
            t.save()
            post.tags.add(t)
            post.save()
    logger.debug("Post Tags: %s" % str(post.tags))
    post.save()
    return True

def _get_default_blog(user):
    blog = Post.objects.filter(author=user.author).order_by('-pub_date')[0].blog
    return blog

def get_user(username, apikey, blogid=None):
    """
    checks if a user is authorized to make this call
    """
    logger.debug("%s.get_user entered" % __name__)
    logger.debug("user: %s" % username)
    logger.debug("apikey: %s" % apikey)
    try:
        user = User.objects.get(**{'username':username})
    except User.DoesNotExist:
        raise Fault(LOGIN_ERROR, 'Username is incorrect.')
    if not apikey == user.author.remote_access_key:
        raise Fault(LOGIN_ERROR, 'Password is invalid.')
    if not user.author.remote_access_enabled:
        raise Fault(PERMISSION_DENIED, 'Remote access not enabled for this user.')
    # if not author.is_staff or not author.is_active:
    #    raise Fault(PERMISSION_DENIED, _('User account unavailable.'))
    #        raise Fault(PERMISSION_DENIED, _('User cannot %s.') % permission)

    return user    

def check_perms(user, obj):
    logger.debug("%s.check_perms entered" % __name__)
    if isinstance(obj, Post):    
        if obj.author.user != user and not user.is_superuser:
                raise Fault(PERMISSION_DENIED, 'Permission denied for %s on post %s' % (user, obj.id))
    elif isinstance(obj, Blog):
        if obj.owner != user and not user.is_superuser:
            raise Fault(PERMISSION_DENIED, 'Permission denied for %s on post %s' % (user, obj.id))
    else:
            raise Fault(PERMISSION_DENIED, 'Permission denied for %s unknown object %s' % (user, obj))

def _term_taxonomy(term):
    """
    Determine term_taxonomy_id for a given object
    Based on contenttypes
    """
    logger.debug("%s._term_taxonomy entered" % __name__)
    # get the content type
    ctype = ContentType.objects.get_for_model(term)
    res = {'id':ctype.id, 'name':ctype.name}
    return res
    

def _term_struct(term):
    logger.debug("%s._term_struct entered" % __name__)
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
    'term_taxonomy_id': _term_taxonomy(term)['id'],
    }
    return struct
    

def _post_struct(post):
    """
    creates a struct for calls:
    - getPost
    """
    logger.debug("%s._post_struct entered" % __name__)
    res = {}
    res['post_id'] = post.id
    res['post_title'] = post.title
    res['post_date'] = post.pub_date
    res['post_date_gmt'] = post.pub_date
    res['post_modified'] = post.update_date
    res['post_modified_gmt'] = post.update_date
    res['post_status'] = post.status
    res['post_type'] = 'post'
    res['post_format'] = type_map.get(post.post_format, 'post') 
    res['post_name'] = post.slug
    res['post_author'] = str(post.author.id)
    res['post_password'] = '' # FIXME: passwords not supported
    res['post_excerpt'] = post.summary
    res['post_content'] = post.body
    res['post_parent'] = '0'
    res['post_mime_type'] = ''
    res['link'] = post.get_url()
    res['guid'] = post.guid
    res['menu_order'] = 0 # this might be implemented for flat pages at some point...
    res['comment_status'] = post.enable_comments and "open" or "closed"
    res['ping_status'] = post.enable_comments and "open" or "closed" # FIXME: add allow_trackbacks to Post at some point
    res['sticky'] = False # FIXME: Implement sticky on Post, could be useful
    res['post_thumbnail'] = [] # FIXME: Implement post_thumbnail finally
    res['terms'] = []
    # add the categories
    count = 0
    for cat in post.categories.all():
        count = count+1
        term = _term_struct(cat)
        term['count'] = str(count)
        res['terms'].append(term)

    for tag in post.tags.all():
        count = count+1
        term = _term_struct(tag)
        term['count'] = str(count)
        res['terms'].append(term)
    
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
    logger.debug("%s.getPost entered" % __name__)
    user = get_user(username, password)
    post = Post.objects.get(id=post_id)
    check_perms(user, post)
    return _post_struct(post)

def getPosts(blog_id, username, password, filter={}):
    """
    struct filter: Optional.
    string post_type
    string post_status
    int number
    int offset
    string orderby
    string order
    """
    logger.debug("%s.getPosts entered" % __name__)
    user = get_user(username, password)
    if blog_id == 0:
        # no blog_id given, get the last one with posts by this 
        # author
        logger.debug("blog_id=0, lookding for posts")
        blog = Post.objects.filter(author=user.author).order_by('-pub_date')[0].blog
    else:
        blog = Blog.objects.get(id=blog_id)
    check_perms(user, blog)
    
    # get a list of this user's posts on this blog
    posts = Post.objects.filter(author=user.author, blog=blog)
    res = []
    for post in posts:
        res.append(_post_struct(post))
    return res

def newPost(blog_id, username, password, content):
    """
    Parameters
    int blog_id
    string username
    string password
    struct content
        string post_type
        string post_status
        string post_title
        int post_author
        string post_excerpt
        string post_content
        datetime post_date_gmt | post_date
        string post_format
        string post_name: Encoded URL (slug)
        string post_password
        string comment_status
        string ping_status
        int sticky
        int post_thumbnail
        int post_parent
        array custom_fields
            struct
            string key
            string value
    struct terms: Taxonomy names as keys, array of term IDs as values.
    struct terms_names: Taxonomy names as keys, array of term names as values.
    struct enclosure
        string url
        int length
        string type
    any other fields supported by wp_insert_post    
    
    ## EXAMPLE FROM DeskPM 
    
    { 'post_format': 'text', 
      'post_title': 'Test Post for desktop clients', 
      'post_status': 'publish', 
      'post_thumbnail': 0, 
      'sticky': False, 
      'post_content': '<p>This is a test post. </p><p>Go forth, and publish my good man...</p>', 
      'terms_names': {'post_tag': []}, 
      'comment_status': 'open'
    }
    
    ## Full-Featured Example
    
    {   'post_format': 'text', 
        'post_title': 'Full-featured Posts', 
        'post_status': 'publish', 
        'post_thumbnail': 0, 
        'sticky': False, 
        'post_content': "Fully Featured, With Pics & Stuff.\n\nMy, aren't **we** fancypants.", 
        'terms_names': {'post_tag': ['tag']}, 
        'comment_status': 'open'}
    Return Values
    string post_id
    Errors
    401
    - If the user does not have the edit_posts cap for this post type.
    - If user does not have permission to create post of the specified post_status.
    - If post_author is different than the user's ID and the user does not have the edit_others_posts cap for this post type.
    - If sticky is passed and user does not have permission to make the post sticky, regardless if sticky is set to 0, 1, false or true.
    - If a taxonomy in terms or terms_names is not supported by this post type.
    - If terms or terms_names is set but user does not have assign_terms cap.
    - If an ambiguous term name is used in terms_names.
    403
    - If invalid post_type is specified.
    - If an invalid term ID is specified in terms.
    404
    - If no author with that post_author ID exists.
    - If no attachment with that post_thumbnail ID exists.
    
    """
    
    logger.debug("%s.newPost entered" % __name__)
    logger.debug("user: %s" % str(username))
    logger.debug("blog_id: %s" % str(blog_id))
    logger.debug("content:\n%s" % str(content))
    
    user = get_user(username, password)
    if blog_id == 0:
        # no blog_id given, get the last one with posts by this 
        # author
        logger.debug("blog_id=0, lookding for posts")
        blog = Post.objects.filter(author=user.author).order_by('-pub_date')[0].blog
    else:
        blog = Blog.objects.get(pk=blog_id)
    
    check_perms(user, blog)
    logger.info("blog: %s" % str(blog))    
    pub_date = datetime.datetime.now()
    
    logger.info("blog: %s" % str(blog))
    logger.info("pub_date: %s" % str(pub_date))
    post = Post(
        title=content['post_title'],
        body = content['post_content'],
        create_date = pub_date,
        update_date = pub_date,
        pub_date = pub_date,
        status = content.get('post_status', 'draft'),
        blog = blog,
        author =user.author
    )
    
    post.save()
    logger.info("Post %s saved" % post)
    # logger.info("Setting Tags")
    # setTags(post, struct)
    #logger.debug("Handling Pings")
    #logger.info("sending pings to host")
    # send_pings(post)
    # check for tags
    # terms:{name:[type.id]} 

    terms = content.get('terms', None)
    if terms:
        struct = {}
        tags = []
        categories = []
        for term, ids in terms.items():
            # tag?
            if ContentType.objects.get_for_model(Tag) in ids:
                print "Tag ID found"
                tags.append(term)
                struct['tags'] = tags 
    
        _setTags(post, struct)
    logger.debug("newPost finished")
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
    user = get_user(username, password)
    blog = Blog.objects.get(id=blog_id)
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
    logger.debug( "wp.getUsersBlogs called")
    user = get_user(username, password)
    # print "Got user", user
    usersblogs = Blog.objects.filter(owner=user)
    logger.debug( "%s blogs for %s" % (usersblogs, user))
    # return usersblogs
    res = [
    {
    'isAdmin': True,
    'url': "http://%s/blog/%s/" % (blog.site.domain, user.username),
    'blogid':str(blog.id),
    'blogName': blog.title,
    # 'xmlrpc': reverse("xmlrpc"),
    # non-ssl for debug
    'xmlrpc': settings.DEBUG and "http://%s/xmlrpc/" % blog.site.domain or "https://%s/xmlrpc/" % blog.site.domain,
    } for blog in usersblogs ]
    logger.debug(res)
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
    logger.debug("%s.getCategories entered" % __name__)
    res = []
    user = get_user(username, password)
    blog = Blog.objects.get(pk=blog_id)

    check_perms(user, blog)
    
    logger.debug("getting categories for %s" % blog)

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

def getOptions(blog_id, username, password, options=[]):
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
    logger.debug("wp.getOptions entered")
    logger.debug("user: %s" % username)
    logger.debug("blog_id: %s" % blog_id)
    logger.debug("struct: %s" % options)
    user = get_user(username, password)
    blog = Blog.objects.get(pk=blog_id)
    check_perms(user, blog)
    admin_url = {
        'value': urlparse.urljoin(blog.get_url(), "admin"),
        'desc': "The URL to the admin area",
        'readonly': True,
    }



    res = {
        'admin_url':admin_url,
        'blog_id': { 'desc':'Blog ID', 'readonly':True, 'value': str(blog.id) },
        'blog_public' : {'desc': 'Privacy access', 'readonly': True, 'value': '1' },
        'blog_tagline' : {'desc': 'Site Tagline', 'readonly': False, 'value': blog.description },
        'blog_title': {'desc': 'Site title', 'readonly': False, 'value': blog.title },
        'blog_url' : { 'desc': 'Blog Address (URL)', 'readonly': True, 'value': blog.get_url() },
        'date_format': {'desc': 'Date Format', 'readonly':False, 'value': 'F j, Y'},
        'default_comment_status': { 'desc': 'Allow people to post comments on new articles', 'readonly': False, 'value': 'open'},
        'default_ping_status': {'desc': 'Allow link notifications from other blogs (pingbacks and trackbacks) on new articles', 'readonly': False, 'value': 'open'},
        'home_url': {'desc': 'Site address URL', 'readonly': True, 'value': blog.get_url()},
        'image_default_align': {'desc': 'Image default align', 'readonly': True, 'value': ''},
        'image_default_link_type': {'desc': 'Image default link type', 'readonly': True, 'value': 'file'},
        'image_default_size': {'desc': 'Image default size', 'readonly': True, 'value': ''},
        'large_size_h': {'desc': 'Large size image height', 'readonly': True, 'value': ''},
        'large_size_w': {'desc': 'Large size image width', 'readonly': True, 'value': ''},
        'login_url' : {'desc': 'Login Address (URL)', 'readonly': False, 'value': admin_url},
        'medium_large_size_h': {'desc': 'Medium-Large size image height', 'readonly': True, 'value': ''},
        'medium_large_size_w': {'desc': 'Medium-Large size image width', 'readonly': True, 'value': ''},
        'medium_size_h': {'desc': 'Medium size image height', 'readonly': True, 'value': ''},
        'medium_size_w': {'desc': 'Medium size image width', 'readonly': True, 'value': ''},
        'post_thumbnail': {'desc': 'Post Thumbnail', 'readonly': True, 'value': True},
        'software_name': {'desc': 'Software Name', 'readonly': True, 'value': 'XBlog'},
        'software_version': {'desc': 'Software Version', 'readonly': True, 'value': django.VERSION},
        'stylesheet': {'desc': 'Stylesheet', 'readonly': True, 'value': 'django-bootstrap3'},
        'template': {'desc': 'Template', 'readonly': True, 'value': 'ehwio'},
        'thumbnail_crop': {'desc': 'Crop thumbnail to exact dimensions', 'readonly': False, 'value': False},
        'thumbnail_size_h': {'desc': 'Thumbnail Height', 'readonly': False, 'value': 150},
        'thumbnail_size_w': {'desc': 'Thumbnail Width', 'readonly': False, 'value': 150},
        'time_format': {'desc': 'Time Format', 'readonly': False, 'value': 'g:i a'},
        'time_zone': {'desc': 'Time Zone', 'readonly': False, 'value': '0'},
        'users_can_register': {'desc': 'Allow new users to sign up', 'readonly': False, 'value': True},
        'wordpress.com': {'desc': 'This is a wordpress.com blog','readonly': True, 'value': False},
    }

    logger.debug("res: %s" % res)
    logger.info("Finished wp.getOptions")
    return res
