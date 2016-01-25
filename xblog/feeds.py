#!/usr/bin/env python
# encoding: utf-8
"""
feeds.py

Created by Eric Williams on 2007-02-23.
"""
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed

from django.core.exceptions import ObjectDoesNotExist
from xblog.models import Post, Blog
from django.conf import settings
import datetime
import logging

logger = logging.getLogger(__name__)


try:
    from urllib import quote as urlquote
except ImportError:
    def urlquote(url):
        return url

#class Podcasts(Feed):
#    title = "Podcasts at xoffender.de"
#    link = "/blog/feeds/"
#    description = "Podcasts to be found at " + settings.SITE_URL
#    
#    def items(self):
#        # returns a list of all podcasts...
#        res = Podcast.objects.order_by('-pubdate')[:5]
#        return res
#
#    def get_object(self, bits):
#        if len(bits)!=1:
#            raise ObjectDoesNotExist
#        
#        return Podcast.get(slug__exact=bits[0])
#            
#    def item_author_name(self, item):
#        # print "Item author...", item.author
#        if item.author:
#            return item.author
#        else:
#            return "Unknown"
#        
#    
#    
#    
#    def item_link(self, item):
#        # returns the enclosure url
#        return self.item_enclosure_url(item)
#        
#    def item_enclosure_url(self, item):
#        # returns a quoted URL for the enclosure
#        # why django doesn't already quote URLs is beyond me...
#        url = "/".join([settings.MEDIA_URL, urlquote(item.enclosure)])
#        return url
#        
#    def item_enclosure_length(self, item):
#        return item.get_enclosure_length()
#        
#    def item_enclosure_mime_type(self, item):
#        return item.get_enclosure_mime_type()
#        
#    def item_pubdate(self,item):
#        return item.pubdate
#        
#        
#    def item_categories(self, item):
#        res = []
#        for cat in item.categories.all():
#            res.append(cat.title)
#        
#        return res
#
#class Posts(Feed):
#    title = "Blogs"
#    link = "/blog/feeds"
#    description = "blogs to be found at " + settings.SITE_URL
#    
#    def items(self, obj):
#        return Post.objects.order_by('-pub_date').filter(status='publish')[:10]
#        
#    def content(self, obj):
#        return obj.get_formatted_body()
    
    #def description(self, obj):
    #    if obj:
    #        return obj.get_formatted_body()
    #    else:
    #        return "Blogs to be found at xoffender.de"
    
    #def items(self):
    #    return Post.objects.order_by('-pub_date')[:]
    
    #def get_object(self, bits):
    #    return Beat.objects.get(slug__exact=bits[0])
    
    #def title(self, obj):
    #    return obj.title
    
    #def link(self, obj):
    #    return obj.get_absolute_url()
        

class Posts(Feed):
  """
  Yet another try to get my crappy, crappy feeds to work correctly.
  """
  feed_type = Atom1Feed
  title = "You Bitch! || Posts"  
  link = "/"
  description = "RSS Feed for YouBitch.org"
  # item_pubdate = datetime.datetime(2005, 5, 3)  
  def items(self):
    return Post.objects.order_by("-pub_date").filter(status="publish")[:10]
  
  def item_pubdate(self, item):
    """
    Takes an item, as returned by items(), and returns the item's
    pubdate.
    """
    logger.debug("entered item_pubdate") 
    return item.pub_date


  def author_name(self, obj):
      try:
          return obj.author.first_name
      except Exception, e:
          logger.debug("Doh! %s" % e)
          import sys, traceback
          logger.warn("Exception in user code:")
          logger.warn(str(type(obj)))
          return "Unknown"
    
    
if __name__ == '__main__':
    main()

