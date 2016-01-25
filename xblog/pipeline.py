import logging
from django.core.files.base import ContentFile
from django.contrib.sites.models import Site

from django.conf import settings
from social.backends.twitter import TwitterOAuth
from social.backends.facebook import FacebookOAuth2
from urllib import urlopen

from xblog.models import Blog

logger = logging.getLogger("xblog")
# mostly cribbed from
# http://blog.vero4ka.info/blog/2015/03/02/django-python-social-auth-configuration-and-pipeline-to-get-users-information/


def debug(strategy, *args, **kwargs):
    """
    inline debugging stop
    """
    logger.debug("%s.debug entered" % __name__)
    if settings.DEBUG:
        logger.debug("%s.debug entered" % __name__)
        logger.debug("strategy:\n%s" % strategy)
        logger.debug("kwargs:\n%s" % kwargs)

    
def create_user_blog(strategy, *args, **kwargs):
    """
    creates a blog for new users.
    This doesn't give them any permissions to post, however.
    """
    logger.debug("%s.create_user_blog entered" % __name__)
    if not kwargs['is_new']:
        logger.info('Existing user, returning')
        return
    user = kwargs['user']
    if user.author.fullname == '':
        fullname = "Some guy"
    else:
        fullname = user.author.fullname
    site = Site.objects.get(pk=settings.SITE_ID)
    struct = {
        'title': "%s's Space" % fullname,
        'description': 'Thoughts, articles, notes',
        'site': site,
        'owner': user
    }
    logger.info("Creating blog for '%s'" % user)
    blog = Blog(**struct)
    logger.debug("created %s" % str(blog))
    blog.save()

def update_user_social_data(strategy, *args, **kwargs):
    """
    Adds upstream avatar and other info during authentication
    """
    logger.debug("update_user_social_data entered")
    logger.debug( "update_user_social_data  %s" % strategy)
    if not kwargs['is_new']:
        # this could be an opportunity to update information
        # skipping for now
        logger.info("existing user, so not requesting info")
        return
    # everything after here is what happens for new user logins at the
    # end of the auth pipeline

    full_name = ''
    backend = kwargs['backend']
    user = kwargs['user']
    
    logger.info("Processing user '%s' from auth backend '%s'" % (user, backend))
    
    # get the user's full name
    if isinstance(backend, TwitterOAuth):
        logger.info("Using twitter credentials")
        if kwargs.get('details'):
            logger.debug(kwargs.get('details'))
            full_name = kwargs['details'].get('fullname')
        logger.info("Setting fullname to '%s'" % full_name)
        user.author.fullname = full_name

        if kwargs['response'].get('profile_image_url'):
            logger.info("Received profile image: %s" % kwargs['response'].get('profile_image_url'))
            image_name = 'tw_avatar_%s.jpg' % full_name
            image_url = kwargs['response'].get('profile_image_url')
            
            image_stream = urlopen(image_url)
            logger.info("Grabbing '%s'" % image_url)
            user.author.avatar.save(
                image_name,
                ContentFile(image_stream.read()),
            )
    if  isinstance(backend, FacebookOAuth2):
        # Facebook Auth
        logger.info("Using Facebook authentication")
        full_name = kwargs['response'].get('name')

    user.full_name = full_name
    user.save()