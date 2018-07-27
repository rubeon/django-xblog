"""

Implementation of the metaWeblog XMLRPC API for XBlog.

Factored out of ../metaWeblog.py for reasons.

"""

import sys, traceback

from django.conf import settings
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except ImportError:
    from django.contrib.auth.models import User

try:
    from xmlrpc.client import Fault
    from xmlrpc.client import DateTime
except ImportError:  # Python 2
    from xmlrpclib import Fault
    from xmlrpclib import DateTime

try:
    from urllib.parse import quote as urlquote
except ImportError:  # Python 2
    from urllib import quote as urlquote
LOGIN_ERROR = 801
PERMISSION_DENIED = 803

import django
import logging

from django.utils.timezone import now
from django.contrib.sites.models import Site

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# from django.contrib.comments.models import FreeComment
from django.conf import settings
from ..models import Tag, Post, Blog, Author, Category, FILTER_CHOICES
from ..ping_modes import send_pings

from .utils import get_user, is_user_blog, post_struct

LOGGER = logging.getLogger(__name__)

def getPost(post_id, username, password):
    """ returns an existing post """
    LOGGER.debug("metaWeblog.getPost called")
    user = get_user(username, password)

    post = Post.objects.get(pk=post_id)

    if post.author.user != user and not user.is_superuser:
        raise Fault(PERMISSION_DENIED, 'Permission denied for %s on post %s' % (user, post_id))

    # post.create_date = format_date(datetime.datetime.now())
    return post_struct(post)

def getRecentPosts(blogid, username, password, num_posts=50):
    """ returns a list of recent posts..."""
    LOGGER.debug("metaWeblog.getRecentPosts called...")
    LOGGER.debug("username %s, blogid %s, num_posts %s", username, blogid, num_posts)
    LOGGER.info("WordPress compatibility, ignoring blogid")
    user = get_user(username, password)
    # WP ignores 'blogid', and we're shooting for WP compatibility
    # if not is_user_blog(user, blogid):
    #     raise Fault(PERMISSION_DENIED, 'Permission denied for %s on blogid %s' % (user, blogid))
    #
    # # blog = Blog.objects.get(id=blogid)
    posts = user.author.post_set.order_by('-pub_date')[:num_posts]

    return [post_struct(post) for post in posts]

def newPost(blogid, username, password, struct, publish="PUBLISH"):
    """ mt's newpost function..."""
    LOGGER.debug( "metaWeblog.newPost called")
    LOGGER.debug("user: %s", username)
    LOGGER.debug("blogid: %s", blogid)
    LOGGER.debug("struct: %s", struct)
    LOGGER.debug("publish: %s", publish)
    body = struct['description']

    user = get_user(username, password)
    if not is_user_blog(user, blogid):
        # raise Fault(PERMISSION_DENIED, 'Permission denied for %s on blogid %s' % (user, blogid))
        raise Blog.DoesNotExist

    try:
        LOGGER.info("Checking for passed blog parameter")
        blog = Blog.objects.get(pk=blogid)
    except ValueError:
        # probably expecting wp behavior
        LOGGER.info("Specified blog not found, using default")
        blog = Blog.objects.filter(owner=user)[0]

    pub_date = now()

    post = Post(
        title=struct['title'],
        body = body,
        create_date = pub_date,
        update_date = pub_date,
        pub_date = pub_date,
        status = publish and 'publish' or 'draft',
        blog = blog,
        author =user.author
    )
    post.prepopulate()
    LOGGER.debug("Saving")
    # need to save beffore setting many-to-many fields, silly django
    post.save()
    categories = struct.get("categories", [])
    LOGGER.debug("Setting categories: %s", str(categories))
    clist = []
    for category in categories:
        try:
            c = Category.objects.get(blog=blog, title=category)
            LOGGER.debug("Got category %s", c)

        except Category.DoesNotExist:
            LOGGER.warn("Adding category '%s'", category )
            c = Category(blog=blog, title=category)
            c.save()
        clist.append(c)
    post.categories.set(clist)
    post.save()
    LOGGER.info("Post %s saved", post)
    LOGGER.info("Setting Tags")
    setTags(post, struct, key="mt_keywords")
    LOGGER.debug("Handling Pings")
    LOGGER.info("sending pings to host")
    try:
        send_pings(post)
    except Exception as e:
        LOGGER.warn('send_pings failed: %s', )
        traceback.print_exc(file=sys.stdout)
        raise Fault(500, str(e))
    LOGGER.debug("newPost finished")
    return post.id


def editPost(postid, username, password, struct, publish):
    LOGGER.debug( "%s.editPost entered", __name__)
    user = get_user(username, password)
    post = Post.objects.get(id=postid)

    if post.author.user != user and not user.is_superuser:
        raise Fault(PERMISSION_DENIED, 'Permission denied for %s on post %s' % (user, postid))

    title = struct.get('title', None)
    if title is not None:
        post.title = title

    body           = struct.get('description', None)
    text_more      = struct.get('mt_text_more', '')
    allow_pings    = struct.get('mt_allow_pings',1)

    description    = struct.get('description','')
    keywords       = struct.get('mt_keywords',[])

    # check for string or array
    if type(keywords) == type(""):
        # it's been passed as a string.  Damn you, ecto
        struct['mt_keywords'] = keywords.split(",")

    text_more = struct.get('mt_text_more',None)

    if text_more:
      # has the extended entry stuff...
      body = "<!--more-->".join([body, text_more])

    post.enable_comments = bool(struct.get('mt_allow_comments',1)==1)
    post.text_filter    = struct.get('mt_convert_breaks','html').lower()

    if title:
        post.title = title

    if body is not None:
        post.body = body
        # todo - parse out technorati tags
    if user:
        post.author = user.author

    if publish:
        post.status = "publish"
    else:
        post.status = "draft"

    setTags(post, struct, key="mt_keywords")

    post.update_date = now()
    post.save()
    LOGGER.debug("--")
    LOGGER.debug(post)
    LOGGER.debug(post.tags.all())

    # FIXME: do I really want trackbacks?
    send_pings(post)
    return True

def deletePost(appkey, postid, username, password, publish=False):
    """
    Parameters
        string appkey: Not applicable for WordPress, can be any value and will be ignored.
        int postid
        string username
        string password
        bool publish: Will be ignored (WP compat.)
    Return Values
        bool true
    Errors
    401
        If the user does not have permission to delete this post.
    404
        If no post with that postid exists.
    """
    LOGGER.debug("metaWeblog_deletePost called")
    user = get_user(username, password)
    post = Post.objects.get(pk=postid)
    if post.author.user != user and not user.is_superuser:
        raise Fault(PERMISSION_DENIED, 'Permission denied for %s on post %s' % (user, postid))
    LOGGER.warn("Deleting post %s by user %s", post.id, user)
    post.delete()
    return True

def getCategories(blogid, username, password):
    """
    takes the blogid, and returns a list of categories

    Parameters
        int blogid
        string username
        string password
    Return Values
        array
        struct
        string categoryId
        string parentId
        string categoryName
        string categoryDescription
        string description: Name of the category, equivalent to categoryName.
        string htmlUrl
        string rssUrl
    """
    LOGGER.debug("metaWeblog_getCategories entered")
    user = get_user(username, password)
    if not is_user_blog(user, blogid):
        raise Fault(PERMISSION_DENIED, 'Permission denied for %s on blogid %s' % (user, blogid))
    categories = Category.objects.all().filter(blog__id=blogid)
    LOGGER.warn("Categories are deprecated")
    res = []
    for c in categories:
        struct={}
        struct['categoryId'] = str(c.id)
        # struct['parentId'] = str(0)
        struct['categoryName']= c.title
        struct['parentId'] = ''
        struct['title'] = c.title
        if c.description == '':
            struct['categoryDescription'] = c.title
        else:
            struct['categoryDescription'] = c.description
        struct['description'] = struct['categoryDescription']
        LOGGER.warn('STRUCT: %s', str(struct))
        struct['htmlUrl'] = "http://%s/%s" % (Site.objects.get_current().domain, c.get_absolute_url())
        struct['rssUrl'] = "http://%s/%sfeed/" % (Site.objects.get_current().domain, c.get_absolute_url())
        res.append(struct)
    LOGGER.debug(res)
    return res

def newMediaObject(blogid, username, password, data):
    """
    Parameters
        int blogid
        string username
        string password
        struct data
        string name: Filename.
        string type: File MIME type.
        string bits: base64-encoded binary data.
        bool overwrite: Optional. Overwrite an existing attachment of the same name. (Added in WordPress 2.2)
    Return Values
        struct
            string id (Added in WordPress 3.4)
            string file: Filename.
            string url
            string type
    """
    LOGGER.debug( "metaWeblog_newMediaObject called")
    user = get_user(username, password)
    if not is_user_blog(user, blogid):
        raise Fault(PERMISSION_DENIED, 'Permission denied for %s on blogid %s' % (user, blogid))

    upload_dir = "blog_uploads/%s" % urlquote(user.username)
    bits       = data['bits']
    mime       = data['type']
    name       = data['name']
    savename   = name
    LOGGER.debug("savename: %s", savename)
    save_path = os.path.join(upload_dir, savename)
    LOGGER.debug("Saving to %s", save_path)
    path = default_storage.save(save_path, ContentFile(bits))
    LOGGER.debug("Path: %s", path)
    res = {}
    res['url']= default_storage.url(path)
    res['id'] = ''
    res['file'] = savename
    res['type'] = mime
    LOGGER.debug(res)
    return res


def getUsersBlogs(appkey, username, password):
    # the original metaWeblog API didn't include this
    # it was added in 2003, once blogger jumped ship from using
    # the blogger API
    # http://www.xmlrpc.com/stories/storyReader$2460
    LOGGER.debug( "metaWeblog.getUsersBlogs called")
    user = get_user(username, password)
    usersblogs = Blog.objects.filter(owner=user)
    LOGGER.debug( "%s blogs for %s", usersblogs, user)
    # return usersblogs
    res = [
      {
        'blogid':str(blog.id),
        'blogName': blog.title,
        'url': blog.get_url()
      } for blog in usersblogs
      ]
    LOGGER.debug(res)
    return res

def setTags(post, struct, key="tags"):
    LOGGER.debug( "%s.setTags entered", __name__)
    tags = struct.get(key, None)
    if tags is None:
        LOGGER.info("No tags set")
        post.tags = []
    else:
        # post.categories = [Category.objects.get(title__iexact=name) for name in tags]
        LOGGER.info("Setting tags")
        for tag in tags:
            LOGGER.debug("setting tag '%s'", tag)
            t, created = Tag.objects.get_or_create(title=tag.lower())
            if created:
                LOGGER.info("Adding new tag: %s", t)
            else:
                LOGGER.info("Found tag: %s", t)
            t.save()
            post.tags.add(t)
            post.save()
        # LOGGER.debug("TAGS: %s" % str(tags))
    # LOGGER.debug("Post Tags: %s", str(post.tags.all()))
    post.save()
    return True

# def post_struct(post):
#     """ returns the meta-blah equiv of a post """
#     LOGGER.debug("post_struct called")
#     # link = full_url(post.get_absolute_url())
#     link = post.get_absolute_url()
#     categories = [c.title for c in post.categories.all()]
#     # categories = []
#     # check to see if there's a more tag...
#     if post.body.find('<!--more-->') > -1:
#       description, mt_text_more = post.body.split('<!--more-->')
#     else:
#       description = post.body
#       mt_text_more = ""
#
#     if post.enable_comments:
#       mt_allow_comments = 1
#     else:
#       mt_allow_comments = 2
#
#     struct = {
#         'postid': post.id,
#         'title':post.title,
#         'permaLink':link,
#         'description':description,
#         'mt_text_more':mt_text_more,
#         'mt_convert_breaks':post.text_filter,
#         'categories': categories,
#         'userid': post.author.id,
#         'mt_allow_comments':str(mt_allow_comments)
#     }
#
#     if post.pub_date:
#             # struct['dateCreated'] = format_date(post.pub_date)
#             struct['dateCreated'] = post.pub_date
#     LOGGER.debug("Returning from post_struct")
#     LOGGER.debug(struct)
#     return struct
