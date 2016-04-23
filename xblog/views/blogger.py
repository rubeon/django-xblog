"""

Implementation of the BLOGGER XMLRPC API for XBlog.

Being factored out of ../metaWeblog.py for reasons.

Currently a work in progress

"""

import logging
import django

# from django.contrib.comments.models import FreeComment
from django.conf import settings
from django.utils.timezone import now

from ..models import Tag, Post, Blog, Author, Category, FILTER_CHOICES
from .utils import get_user, post_struct

LOGGER=logging.getLogger(__name__)

def getUserInfo(appkey, username, password):
    """ returns userinfo for particular user..."""
    LOGGER.debug( "blogger.getUserInfo called")
    # author = user # Author.objects.get(user=user)
    user = get_user(username, password)
    firstname = user.first_name
    lastname = user.last_name
    struct = {
        'firstname': firstname,
        'lastname': lastname,
        'nickname': user.username,
        'url': user.author.url,
        'email': user.email,
        'userid': user.id,
    }
    return struct

def getUsersBlogs(appkey, username, password):
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
    LOGGER.debug("blogger.getUsersBlogs called")
    user = get_user(username, password)
    users_blogs = Blog.objects.filter(owner=user)
    LOGGER.debug( "%s blogs for %s",  users_blogs, user)
    # return usersblogs
    res = [{'blogid' : str(blog.id),
            'blogName': blog.title,
            'url' : blog.get_url()
            } for blog in users_blogs]
    LOGGER.debug(res)
    return res

def deletePost(appkey, postid, username, password, publish=False):
    """
    string appkey: Not applicable for WordPress, can be any value and will be ignored.
    int postid
    string username
    string password
    bool publish: Will be ignored.

    Return Values
    bool true
    """
    LOGGER.debug("blogger.deletePost called")
    user = get_user(username, password)
    post = Post.objects.get(pk=post_id)
    if post.author.user != user and not user.is_superuser:
        raise Fault(PERMISSION_DENIED, 'Permission denied for %s on post %s' % (user, postid))
    post.delete()
    return True

def getRecentPosts(appkey, blogId, username, password, numberOfPosts=10):
    """
    Retrieve list of recent posts.

    Parameters
    string appkey: Not applicable for WordPress, can be any value and will be ignored.
    int blogId: Not applicable for WordPress, can be any value and will be ignored.
    string username
    string password
    int numberOfPosts: Optional.
    Return Values
    array
    struct (see #blogger.getPost)
    """
    LOGGER.debug("blogger.getRecentPosts entered")
    user = get_user(username, password)
    posts = user.author.post_set.order_by('-pub_date')[:num_posts]
    return [post_struct(post) for post in posts]

def newPost(appkey, blogid, username, password, content, publish=True):
    """
    blogger.newPost
    Create a new post.

    Parameters
        string appkey: Not applicable for WordPress, can be any value and will be ignored.
        int blogid: Not applicable for WordPress, can be any value and will be ignored.
        string username
        string password
        string content
        bool publish: Whether to publish the post upon creation or leave it as a draft.
    Return Values
        int postid
    Errors
        401
            If publish is false and the user lacks the edit_posts cap.
            If publish is true and the user lacks the publish_posts cap.
    """
    LOGGER.debug("blogger.newPost entered")
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

    pub_date = now()
    post = Post(
        title='',
        body=content,
        create_date=pub_date,
        update_date=pub_date,
        status=publish and 'publish' or 'draft',
        blog=blog,
        author=user.author
    )
    post.prepopulate()
    LOGGER.debug("Saving")
    post.save()
    # Blogger meh, so set a default category
    cats = [Category.objects.get(blog=blog)[0]]
    post.categories = cats
    post.save()
    logger.info("Post %s saved", str(post))
    return post.id
