"""
various utility functions for views

"""

from django.contrib.auth.models import User
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
    try:
        blog = Blog.objects.get(pk=blogid)
    except ValueError:
        # probably blank or something
        blog = Blog.objects.get(owner=user)
    if blog.owner==user:
        return True
    else:
        return False

def post_struct(post):
    """ returns the meta-blah equiv of a post """
    logger.debug("post_struct called")
    # link = full_url(post.get_absolute_url())
    link = post.get_absolute_url()
    categories = [c.title for c in post.categories.all()]
    # categories = []
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
            # struct['dateCreated'] = format_date(post.pub_date)
            struct['dateCreated'] = post.pub_date
    logger.debug("Returning from post_struct")
    logger.debug(struct)
    return struct
