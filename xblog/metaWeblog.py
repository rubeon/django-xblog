#!/usr/bin/env python
# encoding: utf-8
"""
metaWeblog.py

Created by Eric Williams on 2007-02-22.
"""
import string
import xmlrpclib
import urllib
import re
import time
import datetime
import os
import urlparse
import sys
from django.conf import settings
try:
    from django.contrib.auth import get_user_model
    User = get_user_model() # settings.AUTH_USER_MODEL
except ImportError:
    from django.contrib.auth.models import User 

import django
# from django.contrib.comments.models import FreeComment
from django.conf import settings
from .models import Tag, Post, Blog, Author, Category, FILTER_CHOICES

import BeautifulSoup
from .ping_modes import send_pings

try:
    from xmlrpc.client import Fault
    from xmlrpc.client import DateTime
    from urllib.parse import urljoin
except ImportError:  # Python 2
    from xmlrpclib import Fault
    from xmlrpclib import DateTime
    from urlparse import urljoin


# import config
# import xmlrpclib.DateTime

# I guess it's time to fix that upload issue...
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
# this is for getting the URL of xmlrpc endpoing
try:
    from django.urls import reverse
except ImportError: # django < 2
    from django.core.urlresolvers import reverse

import logging
logger = logging.getLogger(__name__)

# Add these to your existing RPC methods in settings.py
# i.e.

LOGIN_ERROR = 801
PERMISSION_DENIED = 803


def authenticated(pos=1):
    # tells the method that the visitor is authenticated
    logger.debug("authenticated entered")
    def _decorate(func):
        def _wrapper(*args, **kwargs):
            username = args[pos+0]
            password = args[pos+1]
            args = args[0:pos]+args[pos+2:]
            try:
                logger.info("Username: %s" % username)
                user = User.objects.get(username__exact=username)
            except User.DoesNotExist:
                logger.debug("username %s, password %s, args %s" % (username, "password", args))
                logger.warn( "User.DoesNotExist")
                raise ValueError("Authentication Failure")
            if not user.check_password(password):
                logger.warn( "User.check_password")
                raise ValueError("Authentication Failure")
            if not user.is_superuser:
                logger.warn("user.is_superuser")
                raise ValueError("Authorization Failure")
            return func(user, *args, **kwargs)

        return _wrapper
    return _decorate

def full_url(url):
    return urljoin(settings.SITE_URL, url)

# @public
# @authenticated()

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

def is_user_blog(user, blogid):
    """
    checks if the blog in question belongs to the use
    """
    
    blog = Blog.objects.get(pk=blogid)
    
    if blog.owner==user:
        return True
    else:
        return False


def blogger_getRecentPosts(appkey, blogid, username, password, num_posts=50):
    """ returns a list of recent posts """
    logger.debug( "blogger.getRecentPosts called...")
    user = get_user(username,  password)
    if not is_user_blog(user, blogid):
        raise Fault(PERMISSION_DENIED, 'Permission denied for %s on blogid %s' % (user, blogid))
    
    blog = Blog.objects.get(id=blogid)
    posts = blog.post_set.order_by('-pub_date')[:num_posts]
    return [post_struct(post) for post in posts]



# @public

def blogger_getUserInfo(appkey, username, password):
    """ returns userinfo for particular user..."""
    logger.debug( "blogger.getUserInfo called")
    # author = user # Author.objects.get(user=user)
    user = get_user(username,  password)
    firstname = user.first_name
    lastname = user.last_name
    struct = {}
    struct['username']=user.username
    struct['firstname']=firstname
    struct['lastname']=lastname
    struct['nickname']= user.author.fullname
    struct['url'] = user.author.url
    struct['email'] = user.email
    struct['userid'] = str(user.id)
    return struct

# @public
# @authenticated()
def blogger_getUsersBlogs(appkey, username, password):
    """
    Parameters
    string appkey: Not applicable for WordPress, can be any value and will be ignored.
    string username
    string password
    Return Values
    array
        struct
            string blogid
            string url: Homepage URL for this blog.
            string blogName
            bool isAdmin
            string xmlrpc: URL endpoint to use for XML-RPC requests on this blog.
    """
    logger.debug( "blogger.getUsersBlogs called")
    user = get_user(username, password)
    # print "Got user", user
    usersblogs = Blog.objects.filter(owner=user)
    logger.debug( "%s blogs for %s" % (usersblogs, user))
    # return usersblogs
    res = [
    {
    'blogid':str(blog.id),
    'blogName': blog.title,
    'url': blog.get_url()
    } for blog in usersblogs
    ]
    logger.debug(res)
    return res

def mt_publishPost(postid, username, password):
    """
    lies that it publishes the thing, mostly for compatibility
    porpoises...
    """
    return True
    
# @public

def blogger_deletePost(appkey, post_id, username, password, publish=False):
    """ deletes the specified post..."""
    logger.debug("blogger.deletePost called")
    user = get_user(username, password)
    post = Post.objects.get(pk=post_id)
    if post.author.user != user:
            raise Fault(PERMISSION_DENIED, 'Permission denied for %s on post %s' % (user, postid))
    logger.warn("Deleting post %s by user %s" % (post.id, user))
    post.delete()
    return True

def mt_getCategoryList(blogid, username, password):
    """ takes the blogid, and returns a list of categories"""
    logger.debug( "mt_getCategoryList called")
    
    logger.warn("Categories no longer supported")
    user = get_user(username, password)
    categories = Category.objects.filter(blog__owner=user.id)
    res=[]
    for c in categories:
         struct={}
         struct['categoryId']= str(c.id)
         struct['categoryName']= c.title
         res.append(struct)
    return res
    
def post_struct(post):
    """ returns the meta-blah equiv of a post """
    logger.debug("post_struct called")
    # link = full_url(post.get_absolute_url())
    link = post.get_absolute_url()
    categories = [c.title for c in post.categories.all()]
    # categories = []
    # check to see if there's a more tag...
    if post.body.find('<!--more-->') > -1:
      description, mt_text_more = post.body.split('<!--more-->')
    else:
      description = post.body
      mt_text_more = ""
    
    if post.enable_comments:
      mt_allow_comments = 1
    else:
      mt_allow_comments = 2
    
    struct = {
        'postid': post.id,
        'title':post.title,
        'permaLink':link,
        'description':description,
        'mt_text_more':mt_text_more,
        'mt_convert_breaks':post.text_filter,
        'categories': categories,
        'userid': post.author.id,
        'mt_allow_comments':str(mt_allow_comments)
    }
    
    if post.pub_date:
            struct['dateCreated'] = format_date(post.pub_date)
    logger.debug("Returning from post_struct")
    logger.debug(struct)
    return struct
    
def format_date(d):
    logger.debug( "format_date called...")
    logger.debug("date passed: %s" % str(d))
    # if not d: return None
    #print 80*"x",fd    
    # return xmlrpclib.DateTime(d.isoformat())
    return xmlrpclib.DateTime(d.isoformat())

def setTags(post, struct, key="tags"):
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
        logger.debug(tags)
    logger.debug("Post Tags: %s" % str(post.tags))
    post.save()
    return True

# @public
def mt_supportedMethods(*args):
    """ returns the xmlrpc-server's list of supported methods"""
    logger.debug( "mt.listSupportedMethods called...")
    # from blog import xmlrpc_views
    # return xmlrpc_views.list_public_methods(blog.metaWeblog)
    res = []
    for method in settings.XMLRPC_METHODS:
        res.append(method[1])
    return res

# @public
def mt_getPostCategories(postid, username, password):
    """
    returns a list of categories for postid *postid*
    """
    logger.debug( "mt_getPostCategories called...")
    logger.warn("Categories no longer supported")
    user = get_user(username, password)
    # if not is_user_blog(user, blogid):
    #    raise Fault(PERMISSION_DENIED, 'Permission denied for %s on blogid %s' % (user, blogid))
    if post.author.user != user:
        raise Fault(PERMISSION_DENIED, 'Permission denied for %s on post %s' % (user, postid))
    

    
    res = []
    try:
         p = Post.objects.get(pk=postid)
         # print "Processing", p.categories.all()
         counter = 0
         res = []
     
         
         for c in p.categories.all():
             # print "Got post category:", c
             primary = False
             if p.primary_category_name == c:
                 # print "%s is the primary category" % c
                 primary=True
             res.append(
                 dict(categoryName=c.title, categoryId=str(c.id), isPrimary=primary)
             )
    except:
         import traceback
         traceback.print_exc(sys.stderr)
         res = None
     
    return res

# @public
def mt_supportedTextFilters():
    """ 
    
    """
    logger.debug( "Called mt_supportedTextFilters")
    res = []
    for key, label in FILTER_CHOICES:
        # print "%s => %s" % (label, key)
        res.append(dict(label=label, key=key))

    return res

    
# @public

def mt_setPostCategories(postid, username, password, cats):
    """
    mt version of setpostcats
    takes a primary as argument
    """
    logger.debug( "mt_setPostCategories called...")
    logger.info("Submitted with %s" % cats)

    user = get_user(username, password)
    post = Post.objects.get(pk=postid)
    if post.author.user != user:
        raise Fault(PERMISSION_DENIED, 'Permission denied for %s on post %s' % (user, postid))
    

    logger.debug("Old cats: %s" % post.categories.all())
    post.categories.clear()
    catlist = []
    for cat in cats:
        category = Category.objects.get(pk=cat['categoryId'])
        logger.debug("Got %s" % category)
        if 'isPrimary' in cat and cat['isPrimary']:
        # if cat.has_key('isPrimary') and cat['isPrimary']:
            logger.debug("Got primary category '%s'" % cat)
            post.primary_category_name = category
        post.categories.add(category)
    logger.debug("New cats: %s" % post.categories.all())
    post.save()
    logger.debug(" mt_setPostCategories Done.")
    return True
