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

from .utils import get_user

def publishPost(postid, username, password):
    """
    sets post status with id=postid to 'publish'
    """
    logger.debug("%s.publishPost entered" % __name__)
    user = get_user(username, password)
    logger.debug("got user %s" % user)
    p = Post.objects.get(pk=postid)
    logger.debug("got post %s" % p)    
    if p.author.user != user and not user.is_superuser:
        raise Fault(PERMISSION_DENIED, 'publishPost: Permission denied for %s on post %s' % (user, postid))
    
    # set status to Published
    p.status = 'publish'
    p.save()
    return p.status=="publish"

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

def getPostCategories(postid, username, password):
    """
    returns a list of categories for postid *postid*
    """
    logger.debug( "%s.getPostCategories called..." % __name__ )
    user = get_user(username, password)
    post = Post.objects.get(pk=postid)
    # print "Processing", p.categories.all()
    res = []
    
    for c in post.categories.all():
        primary = False
        if post.primary_category_name == c:
            primary=True
        res.append(
            dict(categoryName=c.title, categoryId=str(c.id), isPrimary=primary)
        )
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
    logger.debug( "%s.setPostCategories called..." % __name__)
    logger.debug("Submitted with %s" % cats)
    user = get_user(username, password)
    post = Post.objects.get(pk=postid)
    if post.author.user != user:
        raise Fault(PERMISSION_DENIED, 'Permission denied for %s on post %s' % (user, post))
    logger.debug("Old cats: %s" % post.categories.all())
    post.categories.clear()
    catlist = []
    for cat in cats:
        category = Category.objects.get(pk=cat['categoryId'])
        # print "Got", category
        if 'isPrimary' in cat and cat['isPrimary']:
            logger.debug("Got primary category '%s'" % cat)
            post.primary_category_name = category
        post.categories.add(category)
    logger.debug("New cats: %s" % post.categories.all())
    post.save()
    logger.debug("%s.setPostCategories Done." % __name__)
    return True

