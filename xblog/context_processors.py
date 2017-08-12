# -*- coding: utf8 -*-
"""
Context processors for XBlog
"""
import logging

from django.contrib.sites.models import Site
from django.conf import settings
# from xblog.models import Blog

# from xcomments.models import FreeComment
#
# def media_url(request):
#     # from django.conf import settings
#     # try:
#     #   blog = Blog.objects.all()[0] # default for now...
#     # except:
#     #   blog=""
#
#     # recent_comments = FreeComment.objects.order_by('-submit_date').filter(is_public=True)[:5]
#     return {
#         'media_url': settings.MEDIA_URL,
#         'site_url' : settings.SITE_URL,
#         'thisblog':blog,
#         'recent_comments': recent_comments
#     }
#

LOGGER = logging.getLogger(__name__)

def site(request):
    """
    Addes the `site` variable to template contexts.  Why oh why
    has Django not added that in as a default?
    """
    LOGGER.debug("%s.site entered", __name__)
    LOGGER.debug("%s request", str(request))
    this_site = Site.objects.get_current()
    try:
        disqus_identifier = settings.DISQUS_IDENTIFIER
    except AttributeError:
        disqus_identifier = None
    return {
        'site': this_site,
        'disqus_identifier': disqus_identifier
    }
