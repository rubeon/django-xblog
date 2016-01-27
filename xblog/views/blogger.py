"""

Implementation of the Blogger XMLRPC API for XBlog.

Being factored out of ../metaWeblog.py for reasons.

Currently a work in progress

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

def getUserInfo(user, appkey):
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

def getUsersBlogs(user, appkey):
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
    
def deletePost(user, appkey, post_id, publish):
    """ deletes the specified post..."""
    logger.debug("blogger.deletePost called")
    #print "GOT APPKEY", appkey
    #print "GOT PUBLISH:",publish
    post = Post.objects.get(pk=post_id)
    #print "DELETING:",post
    post.delete()

    return True

