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
from django.contrib.auth.models import User
import django
# from django.contrib.comments.models import FreeComment
from django.conf import settings
from xblog.models import Tag, Post, Blog, Author, FILTER_CHOICES
from views.xmlrpc_views import public
import BeautifulSoup
from ping_modes import send_pings

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
                # print "Password: ", password
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

@public
@authenticated()
def metaWeblog_getCategories(user, blogid, struct={}):
    """ takes the blogid, and returns a list of categories
    struct:
    string categoryId
    string parentId
    string categoryName
    string categoryDescription
    string description: Name of the category, equivalent to categoryName.
    string htmlUrl
    string rssUrl
    
    
    """
    logger.debug("metaWeblog_getCategories called")
    categories = Category.objects.all()
    res=[]
    logger.warn("Categories no longer supported")
    # for c in categories:
    #     struct={}
    #     struct['categoryId'] = str(c.id)
    #     # struct['parentId'] = str(0)
    #     struct['categoryName']= c.title
    #     struct['parentId'] = ''
    #     struct['title'] = c.title
    #     # if c.description == '':
    #     #     struct['categoryDescription'] = c.title
    #     # else:
    #     #     struct['categoryDescription'] = c.description
    #     # struct['description'] = struct['categoryDescription']
    #     struct['htmlUrl'] = "http://dev.ehw.io"
    #     res.append(struct)
    logger.debug(res)
    return res

@public
@authenticated()
def metaWeblog_newMediaObject(user, blogid, struct):
    """ returns struct with url..."""
    logger.debug( "metaWeblog_newMediaObject called")
    upload_dir = "blog_uploads/%s" % urllib.quote(user.username)
    bits       = struct['bits']
    mime       = struct['type']
    name       = struct['name']    
    savename   = name
    logger.debug( "savename: %s" %  savename)
    save_path = os.path.join(upload_dir, savename)
    logger.debug("Saving to %s" % save_path)
    path = default_storage.save(save_path, ContentFile(bits))
    logger.debug("Path: %s" % path)
    res = {}
    res['url']= default_storage.url(path)
    logger.debug(res)
    return res


 
@public
@authenticated()
def metaWeblog_newPost(user, blogid, struct, publish="PUBLISH"):
    """ mt's newpost function..."""
    logger.debug( "metaWeblog.newPost called")
    logger.debug("user: %s" % user)
    logger.debug("blogid: %s" % blogid)
    logger.debug("struct: %s" % struct)
    logger.debug("publish: %s" % publish)
    body = struct['description']
    try:
        logger.info("Checking for passed blog parameter")
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
    # clist = []
    # for category in categories:
    #     try:
    #         c = Category.objects.filter(blog=blog, title=category)[0]
    #         logger.debug("Got %s" % c)
    #         clist.append(c)
    #     except Exception, e:
    #         logger.warn(str(e))
    # post.categories=clist
    post.save()
    logger.info("Post %s saved" % post)
    logger.info("Setting Tags")
    setTags(post, struct, key="mt_keywords")
    logger.debug("Handling Pings")
    logger.info("sending pings to host")
    send_pings(post)
    logger.debug("newPost finished")
    return post.id
    
@public
@authenticated()
def metaWeblog_editPost(user, postid, struct, publish):
    logger.debug( "metaWeblog_editPost")
    post = Post.objects.get(id=postid)
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
        post.author = user 
    
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
@public
@authenticated()
def metaWeblog_getPost(user, postid):
    """ returns an existing post """
    logger.debug( "metaWeblog.getPost called ")
    post = Post.objects.get(pk=postid)
    # post.create_date = format_date(datetime.datetime.now())
    return post_struct(post)

@public
@authenticated(pos=2)
def blogger_getRecentPosts(user, appkey, blogid, num_posts=50):
    """ returns a list of recent posts """
    logger.debug( "blogger.getRecentPosts called...")
    blog = Blog.objects.get(id=blogid)
    posts = blog.post_set.order_by('-pub_date')[:num_posts]
    return [post_struct(post) for post in posts]

@public
@authenticated()
def metaWeblog_getRecentPosts(user, blogid, num_posts=50):
    """ returns a list of recent posts..."""
    logger.debug( "metaWeblog.getRecentPosts called...")
    logger.debug( "user %s, blogid %s, num_posts %s" % (user, blogid, num_posts))
    logger.info("WordPress compatibility, ignoring blogid")
    # blog = Blog.objects.get(id=blogid)
    posts = user.author.post_set.order_by('-pub_date')[:num_posts]
    return [post_struct(post) for post in posts]
    

@public
@authenticated()
def blogger_getUserInfo(user, appkey):
    """ returns userinfo for particular user..."""
    logger.debug( "blogger.getUserInfo called")
    # author = user # Author.objects.get(user=user)
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

@public
@authenticated()
def blogger_getUsersBlogs(user, appkey):
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

@public
@authenticated()
def metaWeblog_getUsersBlogs(user, appkey):
    # the original metaWeblog API didn't include this
    # it was added in 2003, once blogger jumped ship from using
    # the blogger API
    # http://www.xmlrpc.com/stories/storyReader$2460
    logger.debug( "metaWeblog.getUsersBlogs called")
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
    
@public
@authenticated()
def mt_publishPost(user, postid):
    """
    lies that it publishes the thing, mostly for compatibility
    porpoises...
    """
    return True
    
@public
@authenticated(pos=2)
def blogger_deletePost(user, appkey, post_id, publish):
    """ deletes the specified post..."""
    logger.debug("blogger.deletePost called")
    #print "GOT APPKEY", appkey
    #print "GOT PUBLISH:",publish
    post = Post.objects.get(pk=post_id)
    #print "DELETING:",post
    post.delete()

    return True
@public
@authenticated()
def mt_getCategoryList(user, blogid):
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
    
def post_struct(post):
    """ returns the meta-blah equiv of a post """
    logger.debug("post_struct called")
    # link = full_url(post.get_absolute_url())
    link = post.get_absolute_url()
    # categories = post.categories.all()
    categories = []
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
    return struct
    
def format_date(d):
    logger.debug( "format_date called...")
    if not d: return None
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

@public
def mt_supportedMethods(*args):
    """ returns the xmlrpc-server's list of supported methods"""
    logger.debug( "mt.listSupportedMethods called...")
    # from blog import xmlrpc_views
    # return xmlrpc_views.list_public_methods(blog.metaWeblog)
    res = []
    for method in settings.XMLRPC_METHODS:
        res.append(method[1])
    return res

@public
@authenticated()
def mt_getPostCategories(user, postid):
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

@public
def mt_supportedTextFilters():
    """ 
    
    """
    logger.debug( "Called mt_supportedTextFilters")
    res = []
    for key, label in FILTER_CHOICES:
        # print "%s => %s" % (label, key)
        res.append(dict(label=label, key=key))

    return res

    
@public
@authenticated()
def mt_setPostCategories(user, postid, cats):
    """
    mt version of setpostcats
    takes a primary as argument
    """
    logger.debug( "mt_setPostCategories called...")
    logger.info("Submitted with %s" % cats)
    logger.warn("Categories no longer supported")
    # post = Post.objects.get(pk=postid)
    # logger.debug("Old cats: %s" % post.categories.all())
    # post.categories.clear()
    # catlist = []
    # for cat in cats:
    #     category = Category.objects.get(pk=cat['categoryId'])
    #     # print "Got", category
    #     if cat.has_key('isPrimary') and cat['isPrimary']:
    #         logger.debug("Got primary category '%s'" % cat)
    #         post.primary_category_name = category
    #     post.categories.add(category)
    # logger.debug("New cats: %s" % post.categories.all())
    # post.save()
    logger.debug(" mt_setPostCategories Done.")
    return True


@public
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

@authenticated(pos=0)
def wp_getUsersBlogs(user):
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
    logger.info( "wp.getUsersBlogs called")
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
    'xmlrpc': "https://%s/xmlrpc/" % blog.site.domain,

    } for blog in usersblogs
    ]
    logger.debug(res)
    return res

@authenticated(pos=1)
def wp_getOptions(user, blog_id, struct={}):
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
    logger.debug("user: %s" % user)
    logger.debug("blog_id: %s" % blog_id)
    logger.debug("struct: %s" % struct)
    blog = Blog.objects.get(pk=blog_id)
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

def wp_getTags(blog_id, user, password):
    """
    Get an array of users for the blog. [sic?]
    Parameters
        int blog_id
        string username
        string password
    Return Values
        array
            struct
                int tag_id
                string name
                int count
                string slug
                string html_url
                string rss_url
    
    [{
	  'count': '1',
	  'html_url': 'http://subcriticalorg.wordpress.com/tag/apocalypse/',
	  'name': 'apocalypse',
	  'rss_url': 'http://subcriticalorg.wordpress.com/tag/apocalypse/feed/',
	  'slug': 'apocalypse',
	  'tag_id': '135830'},
    }]
    """
    logger.debug("wp.getTags entered")
    ##FIXME check the user password...
    logger.debug("user: %s" % user)
    logger.debug("blog_id: %s" % blog_id)
    blog = Blog.objects.get(pk=blog_id)
    logger.debug(blog)
    ## FIXME: Tags are shared across blogs... :-/
    res = []
    for tag in Tag.objects.all():
        logger.debug("Processing %s" % tag)
        res.append({
        'count' : tag.post_set.count(),
        'html_url' : urlparse.urljoin(blog.get_url(),"%s/%s" % ("tag",tag.title)),
        'name' : tag.title,
        'rss_url': urlparse.urljoin(blog.get_url(),"%s/%s/%s" % ("tag",tag.title, 'feed')), 
        'slug':tag.title,
        'tag_id':tag.id,
        })
    
    logger.debug("res: %s" % res)
    return res

@authenticated(pos=1)
def wp_newPost(user, blog_id, content):
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
    logger.debug("wp.newPost entered")
    logger.debug("user: %s" % str(user))
    logger.debug("blog_id: %s" % str(blog_id))
    logger.debug("content:\n%s" % str(content))
    
    blog = Blog.objects.get(pk=blog_id)
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
        status = content['post_status'],
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
    struct = {
        'tags': content['terms_names']['post_tag'],
    }
    setTags(post, struct)
    logger.debug("newPost finished")
    # set categories? Hmm... categories for posts seem to be legacy thinking
    # set tags
    return str(post.id)

@authenticated(pos=1)
def wp_getCategories(user, blog_id):
    return []

