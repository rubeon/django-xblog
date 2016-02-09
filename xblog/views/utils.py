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


