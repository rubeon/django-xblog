"""

Implementation of the metaWeblog XMLRPC API for XBlog.

Factored out of ../metaWeblog.py for reasons.

"""
try:
    from django.contrib.auth import get_user_model
    User = settings.AUTH_USER_MODEL
except ImportError:
    from django.contrib.auth.models import User 

import django
# from django.contrib.comments.models import FreeComment
from django.conf import settings
from ..models import Tag, Post, Blog, Author, Category, FILTER_CHOICES

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
    logger.debug("metaWeblog_getCategories entered")
    user = get_user(username, password)
    if not is_user_blog(user, blogid):
        raise Fault(PERMISSION_DENIED, 'Permission denied for %s on blogid %s' % (user, blogid))
    categories = Category.objects.all().filter(blog__id=blogid)
    logger.warn("Categories are deprecated")
    for c in categories:
        struct={}
        struct['categoryId'] = str(c.id)
        # struct['parentId'] = str(0)
        struct['categoryName']= c.title
        struct['parentId'] = ''
        struct['title'] = c.title
        # if c.description == '':
        #     struct['categoryDescription'] = c.title
        # else:
        #     struct['categoryDescription'] = c.description
        # struct['description'] = struct['categoryDescription']
        struct['htmlUrl'] = "http://dev.ehw.io"
        res.append(struct)
    logger.debug(res)
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
    logger.debug( "metaWeblog_newMediaObject called")
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

def newPost(blogid, username, password, struct, publish="PUBLISH"):
    """ mt's newpost function..."""
    logger.debug( "metaWeblog.newPost called")
    logger.debug("user: %s" % user)
    logger.debug("blogid: %s" % blogid)
    logger.debug("struct: %s" % struct)
    logger.debug("publish: %s" % publish)
    body = struct['description']
    
    user = get_user(username, password)
    if not is_user_blog(user, blogid):
        raise Fault(PERMISSION_DENIED, 'Permission denied for %s on blogid %s' % (user, blogid))
    
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
    
def editPost(user, postid, struct, publish):
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

def getPost(user, postid):
    """ returns an existing post """
    logger.debug( "metaWeblog.getPost called ")
    post = Post.objects.get(pk=postid)
    # post.create_date = format_date(datetime.datetime.now())
    return post_struct(post)

def getUsersBlogs(user, appkey):
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
