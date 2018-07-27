#!/usr/bin/env python
# encoding: utf-8
"""
feeds.py

Created by Eric Williams on 2007-02-23.
"""
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed
try:
    from django.urls import reverse_lazy
except ImportError: # django < 2
    from django.core.urlresolvers import reverse_lazy

# from django.core.exceptions import ObjectDoesNotExist

from .models import Post
# from .models import Blog



# from django.conf import settings
# import datetime
# import logging

# LOGGER = logging.getLogger(__name__)


# try:
#     from urllib import quote as urlquote
# except ImportError:
#     def urlquote(url):
#         """
#         No urlquote found, so just return the url as-is
#         """
#         return url

class LatestPostsFeed(Feed):
    """
    Feed for latests posts, by Site
    """
    title = "Latest Posts"
    link = reverse_lazy("site-overview")
    description = "Latests Posts"

    @staticmethod
    def items():
        """
        List of posts ordered by pub_date descending
        """
        return Post.objects.filter(status="publish").order_by("-pub_date")

    def item_title(self, item):
        """
        returns the title of the item
        """
        return item.title

    def item_description(self, item):
        """
        returns get_full_body output of the post
        """
        return item.get_full_body()

    def item_link(self, item):
        """
        returns the output of get_absolute_url of the item
        """
        return item.get_absolute_url()

    @staticmethod
    def item_author_name(item):
        """
        Returns the author's fullname
        """
        return item.author.fullname

class AtomLatestPostsFeed(LatestPostsFeed):
    """
    Atom version of the LatestPostsFeed
    """
    feed_type = Atom1Feed
    subtitle = LatestPostsFeed.description
