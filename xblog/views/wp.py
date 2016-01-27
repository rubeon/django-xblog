"""

Implementation of the WordPress XMLRPC API for XBlog.

Factored out of ../metaWeblog.py for reasons.

Being factored out of ../metaWeblog.py for reasons.

Currently a work in progress


"""
import django
import urlparse
from ..models import Blog
from ..models import Post
from ..models import Tag
from ..models import Category

def getUsersBlogs(user):
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

def getOptions(user, blog_id, struct={}):
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

def getTags(blog_id, user, password):
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
def newPost(user, blog_id, content):
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

def getCategories(user, blog_id):
    return []

