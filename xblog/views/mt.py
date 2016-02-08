"""

Implementation of the MovableType XMLRPC API for XBlog.

Being factored out of ../metaWeblog.py for reasons.

Currently a work in progress


"""
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
except ImportError:
    from django.contrib.auth.models import User 

import django
# from django.contrib.comments.models import FreeComment
from django.conf import settings
from ..models import Tag, Post, Blog, Author, Category, FILTER_CHOICES

try:
    from xmlrpc.client import Fault
    from xmlrpc.client import DateTime
except ImportError:  # Python 2
    from xmlrpclib import Fault
    from xmlrpclib import DateTime

import logging
logger = logging.getLogger(__name__)

LOGIN_ERROR = 801
PERMISSION_DENIED = 803

def publishPost(user, postid):
    """
    lies that it publishes the thing, mostly for compatibility
    porpoises...
    """
    return True

def getCategoryList(user, blogid):
    """ takes the blogid, and returns a list of categories"""
    logger.debug( "mt_getCategoryList called")
    # categories = Category.objects.all()
    logger.warn("Categories no longer supported")
    res=[]
    # for c in categories:
    #     struct={}
    #     struct['categoryId']= str(c.id)
    #     struct['categoryName']= c.title
    #     res.append(struct)
    return res

def getPostCategories(user, postid):
    """
    returns a list of categories for postid *postid*
    """
    logger.debug( "mt_getPostCategories called...")
    logger.warn("Categories no longer supported")
    res = []
    # try:
    #     p = Post.objects.get(pk=postid)
    #     # print "Processing", p.categories.all()
    #     counter = 0
    #     res = []
    # 
    #     
    #     for c in p.categories.all():
    #         # print "Got post category:", c
    #         primary = False
    #         if p.primary_category_name == c:
    #             # print "%s is the primary category" % c
    #             primary=True
    #         res.append(
    #             dict(categoryName=c.title, categoryId=str(c.id), isPrimary=primary)
    #         )
    # except:
    #     import traceback
    #     traceback.print_exc(sys.stderr)
    #     res = None
    # 
    return res

def supportedMethods(*args):
    """ returns the xmlrpc-server's list of supported methods"""
    logger.debug( "mt.listSupportedMethods called...")
    # from blog import xmlrpc_views
    # return xmlrpc_views.list_public_methods(blog.metaWeblog)
    res = []
    for method in settings.XMLRPC_METHODS:
        res.append(method[1])
    return res

def supportedTextFilters():
    """ 
    
    """
    logger.debug( "Called mt_supportedTextFilters")
    res = []
    for key, label in FILTER_CHOICES:
        # print "%s => %s" % (label, key)
        res.append(dict(label=label, key=key))

    return res

def setPostCategories(postid, username, password, cats=[]):
    """
    mt version of setpostcats
    takes a primary as argument
    """
    logger.debug( "mt_setPostCategories called...")
    logger.info("Submitted with %s" % cats)
    user = get_user(username, password)
    post = Post.objects.get(pk=postid)
    if post.author.user != user:
        raise Fault(PERMISSION_DENIED, 'Permission denied for %s on post %s' % (user, post_id))
        
    logger.debug("Old cats: %s" % post.categories.all())
    post.categories.clear()
    catlist = []
    for cat in cats:
        category = Category.objects.get(pk=cat['categoryId'])
        # print "Got", category
        if cat.has_key('isPrimary') and cat['isPrimary']:
            logger.debug("Got primary category '%s'" % cat)
            post.primary_category_name = category
        post.categories.add(category)
    logger.debug("New cats: %s" % post.categories.all())
    post.save()
    logger.debug(" mt_setPostCategories Done.")
    return True

def get_user(username, apikey, blogid=None):
    """
    checks if a user is authorized to make this call
    """
    logger.debug("%s.get_user entered" % __name__)
    logger.debug("user: %s" % username)
    logger.debug("apikey: %s" % apikey)
    try:
        user = User.objects.get(**{'username':username})
        print 20*"---"
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
