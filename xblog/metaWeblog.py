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
except ImportError:  # Python 2
    from xmlrpclib import Fault
    from xmlrpclib import DateTime


# import config
# import xmlrpclib.DateTime

# I guess it's time to fix that upload issue...
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
# this is for getting the URL of xmlrpc endpoing
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
    return urlparse.urljoin(settings.SITE_URL, url)

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


def metaWeblog_getCategories(blogid, username, password):
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
    logger.debug("metaWeblog_getCategories entered")
    user = get_user(username, password)
    if not is_user_blog(user, blogid):
        raise Fault(PERMISSION_DENIED, 'Permission denied for %s on blogid %s' % (user, blogid))
    categories = Category.objects.all().filter(blog__id=blogid)
    res = []
    for c in categories:
        struct={}
        struct['categoryId'] = str(c.id)
        struct['parentId'] = ''
        struct['categoryName']= c.title
        struct['categoryDescription'] = c.description
        struct['description'] = c.title
        struct['htmlUrl'] = c.get_absolute_url(absolute=True)
        struct['rssUrl'] = c.get_absolute_url(absolute=True) + "feed/"
        res.append(struct)
    logger.debug(res)
    return res


def metaWeblog_newMediaObject(blogid, username, password, data):
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
    logger.debug( "metaWeblog_newMediaObject called")
    logger.debug("username: %s " % username)
    logger.debug("password: %s " % password)
    logger.debug("blogid: %s" % blogid)
    user = get_user(username, password)
    if not is_user_blog(user, blogid):
        raise Fault(PERMISSION_DENIED, 'Permission denied for %s on blogid %s' % (user, blogid))
    
    upload_dir = "blog_uploads/%s" % urllib.quote(user.username)
    bits       = data['bits']
    mime       = data['type']
    name       = data['name']    
    savename   = name
    logger.debug( "savename: %s" %  savename)
    save_path = os.path.join(upload_dir, savename)
    logger.debug("Saving to %s" % save_path)
    path = default_storage.save(save_path, ContentFile(bits))
    logger.debug("Path: %s" % path)
    res = {}
    res['url']= default_storage.url(path)
    res['id'] = ''
    res['file'] = savename
    res['type'] = mime
    logger.debug(res)
    return res


def metaWeblog_newPost(blogid, username, password, struct, publish="PUBLISH"):
    """ mt's newpost function..."""
    logger.debug( "metaWeblog.newPost called")
    logger.debug("username: %s" % username)
    logger.debug("blogid: %s" % blogid)
    logger.debug("struct: %s" % struct)
    logger.debug("publish: %s" % publish)
    body = struct['description']
    
    user = get_user(username, password)
    if not is_user_blog(user, blogid):
        raise Fault(PERMISSION_DENIED, 'Permission denied for %s on blogid %s' % (user, blogid))
    
    try:
        logger.info("Checking for passed blog parameter")
        print blogid
        blog = Blog.objects.get(pk=blogid)
    except ValueError:
        # probably expecting wp behavior
        logger.info("Specified blog not found, using default")
        blog = Blog.objects.filter(owner=user)[0]

    pub_date = datetime.datetime.now()
    
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
    logger.debug( "Saving")
    # need to save beffore setting many-to-many fields, silly django
    post.save()
    categories = struct.get("categories", [])
    # logger.debug("Setting categories: %s" % categories)
    logger.warn("Categories no longer supported")
    clist = []
    for category in categories:
         try:
             logger.info("Settings category %s" % category)
             c = Category.objects.filter(blog=blog, title=category)[0]
             logger.debug("Got %s" % c)
             clist.append(c)
         except Exception, e:
             logger.debug(20*'-')
             logger.warn(str(e))
    post.categories=clist
    post.save()
    logger.info("Post %s saved" % post)
    logger.info("Setting Tags")
    setTags(post, struct, key="mt_keywords")
    logger.debug("Handling Pings")
    logger.info("sending pings to host")
    send_pings(post)
    logger.debug("newPost finished")
    return post.id
    
# @public
def metaWeblog_editPost(postid, username, password, struct, publish):
    logger.debug( "metaWeblog_editPost entered")
    user = get_user(username, password)
    # figure out the post owner...
    post = Post.objects.get(id=postid)    
    # if not is_user_blog(user, blogid):
    #     raise Fault(PERMISSION_DENIED, 'Permission denied for %s on blogid %s' % (user, blogid))
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
    text_more      = struct.get('mt_text_more',None)
    
    if text_more:
      # has the extended entry stuff...
      body = string.join([body, text_more], "<!--more-->")
    
    post.enable_comments = bool(struct.get('mt_allow_comments',1)==1)
    post.text_filter    = struct.get('mt_convert_breaks','html').lower()
    
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
    post.update_date = datetime.datetime.now()
    post.save()
    # FIXME: do I really want trackbacks?
    send_pings(post)
    return True

# def metaWeblog_editPost(user, postid, struct, publish):
#     """ edit an existing post..."""
#     print "metaWeblog.editPost called"
#     p = Post.objects.get(pk=postid)
#     print "Got post:", p
#     # update the settings...
#     title = struct.get('title',None)
#     if title is not None:
#         p.title = title
#     body = struct.get('description', None)
#     if body is not None:
#         p.body = body
# 
#     p.status = publish and 'Published' or 'Draft'
#     setTags(p, struct)
#     p.save()
#     print "P saved"
#     return True
# 
# @public

def metaWeblog_getPost(postid, username, password):
    """ returns an existing post """
    logger.debug( "metaWeblog.getPost called ")
    user = get_user(username,  password)
    # if not is_user_blog(user, blogid):
    #    raise Fault(PERMISSION_DENIED, 'Permission denied for %s on blogid %s' % (user, blogid))
    post = Post.objects.get(pk=postid)
    if post.author.user != user:
       raise Fault(PERMISSION_DENIED, 'Permission denied for %s on postid %s' % (user, postid))
    # post.create_date = format_date(datetime.datetime.now())
    p = post_struct(post)
    logger.debug(p)
    return p


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

# @public

def metaWeblog_getUsersBlogs(appkey, username, password):
    # the original metaWeblog API didn't include this
    # it was added in 2003, once blogger jumped ship from using
    # the blogger API
    # http://www.xmlrpc.com/stories/storyReader$2460
    logger.debug( "metaWeblog.getUsersBlogs called")
    user = get_user(username, password)
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
    
# @public

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
        if cat.has_key('isPrimary') and cat['isPrimary']:
            logger.debug("Got primary category '%s'" % cat)
            post.primary_category_name = category
        post.categories.add(category)
    logger.debug("New cats: %s" % post.categories.all())
    post.save()
    logger.debug(" mt_setPostCategories Done.")
    return True


# @public
@authenticated()
def xblog_getIdList(user,blogid):
    # 
    """
    this function returns a (potentially very long)
    list of IDs of blog posts.
    """
    logger.debug( "xblog_getIdList called...")
    idlist = []
    logger.debug( "getting blog...")
    blog = Blog.objects.get(id=blogid)
    posts = blog.post_set.all()
    logger.debug( "got %d posts" % posts.count())
    for post in posts:
        idlist.append(post.id)
    
    return idlist




# def wp_getTags(blog_id, user, password):
#     """
#     Get an array of users for the blog. [sic?]
#     Parameters
#         int blog_id
#         string username
#         string password
#     Return Values
#         array
#             struct
#                 int tag_id
#                 string name
#                 int count
#                 string slug
#                 string html_url
#                 string rss_url
#
#     [{
#       'count': '1',
#       'html_url': 'http://subcriticalorg.wordpress.com/tag/apocalypse/',
#       'name': 'apocalypse',
#       'rss_url': 'http://subcriticalorg.wordpress.com/tag/apocalypse/feed/',
#       'slug': 'apocalypse',
#       'tag_id': '135830'},
#     }]
#     """
#     logger.debug("wp.getTags entered")
#     ##FIXME check the user password...
#     logger.debug("user: %s" % user)
#     logger.debug("blog_id: %s" % blog_id)
#     blog = Blog.objects.get(pk=blog_id)
#     logger.debug(blog)
#     ## FIXME: Tags are shared across blogs... :-/
#     res = []
#     for tag in Tag.objects.all():
#         logger.debug("Processing %s" % tag)
#         res.append({
#         'count' : tag.post_set.count(),
#         'html_url' : urlparse.urljoin(blog.get_url(),"%s/%s" % ("tag",tag.title)),
#         'name' : tag.title,
#         'rss_url': urlparse.urljoin(blog.get_url(),"%s/%s/%s" % ("tag",tag.title, 'feed')),
#         'slug':tag.title,
#         'tag_id':tag.id,
#         })
#
#     logger.debug("res: %s" % res)
#    return res

# def wp_newPost(blog_id, username, password, content):
#     """
#     Parameters
#     int blog_id
#     string username
#     string password
#     struct content
#         string post_type
#         string post_status
#         string post_title
#         int post_author
#         string post_excerpt
#         string post_content
#         datetime post_date_gmt | post_date
#         string post_format
#         string post_name: Encoded URL (slug)
#         string post_password
#         string comment_status
#         string ping_status
#         int sticky
#         int post_thumbnail
#         int post_parent
#         array custom_fields
#             struct
#             string key
#             string value
#     struct terms: Taxonomy names as keys, array of term IDs as values.
#     struct terms_names: Taxonomy names as keys, array of term names as values.
#     struct enclosure
#         string url
#         int length
#         string type
#     any other fields supported by wp_insert_post
#
#     ## EXAMPLE FROM DeskPM
#
#     { 'post_format': 'text',
#       'post_title': 'Test Post for desktop clients',
#       'post_status': 'publish',
#       'post_thumbnail': 0,
#       'sticky': False,
#       'post_content': '<p>This is a test post. </p><p>Go forth, and publish my good man...</p>',
#       'terms_names': {'post_tag': []},
#       'comment_status': 'open'
#     }
#
#     ## Full-Featured Example
#
#     {   'post_format': 'text',
#         'post_title': 'Full-featured Posts',
#         'post_status': 'publish',
#         'post_thumbnail': 0,
#         'sticky': False,
#         'post_content': "Fully Featured, With Pics & Stuff.\n\nMy, aren't **we** fancypants.",
#         'terms_names': {'post_tag': ['tag']},
#         'comment_status': 'open'}
#     Return Values
#     string post_id
#     Errors
#     401
#     - If the user does not have the edit_posts cap for this post type.
#     - If user does not have permission to create post of the specified post_status.
#     - If post_author is different than the user's ID and the user does not have the edit_others_posts cap for this post type.
#     - If sticky is passed and user does not have permission to make the post sticky, regardless if sticky is set to 0, 1, false or true.
#     - If a taxonomy in terms or terms_names is not supported by this post type.
#     - If terms or terms_names is set but user does not have assign_terms cap.
#     - If an ambiguous term name is used in terms_names.
#     403
#     - If invalid post_type is specified.
#     - If an invalid term ID is specified in terms.
#     404
#     - If no author with that post_author ID exists.
#     - If no attachment with that post_thumbnail ID exists.
#
#     """
#     logger.debug("wp.newPost entered")
#     logger.debug("user: %s" % str(username))
#     logger.debug("blog_id: %s" % str(blog_id))
#     logger.debug("content:\n%s" % str(content))
#
#     user = get_user(username, password)
#     if not is_user_blog(user, blog_id):
#         raise Fault(PERMISSION_DENIED, 'Permission denied for %s on blogid %s' % (user, blog_id))
#
#     blog = Blog.objects.get(pk=blog_id)
#     logger.info("blog: %s" % str(blog))
#     pub_date = datetime.datetime.now()
#
#     logger.info("blog: %s" % str(blog))
#     logger.info("pub_date: %s" % str(pub_date))
#     post = Post(
#         title=content['post_title'],
#         body = content['post_content'],
#         create_date = pub_date,
#         update_date = pub_date,
#         pub_date = pub_date,
#         status = content['post_status'],
#         blog = blog,
#         author =user.author
#     )
#
#     post.save()
#     logger.info("Post %s saved" % post)
#     # logger.info("Setting Tags")
#     # setTags(post, struct)
#     #logger.debug("Handling Pings")
#     #logger.info("sending pings to host")
#     # send_pings(post)
#     struct = {
#         'tags': content['terms_names']['post_tag'],
#     }
#     setTags(post, struct)
#     logger.debug("newPost finished")
#     # set categories? Hmm... categories for posts seem to be legacy thinking
#     # set tags
#     return str(post.id)
#
