#!/usr/bin/env python
# encoding: utf-8
"""
sitemap.py

Created by Eric Williams on 2007-04-03.
"""
from django.contrib.sitemaps import Sitemap
from xblog.models import Post

class BlogSitemap(Sitemap):
    """
    this creates the googleable part of the
    site-wide sitemap file...
    """
    changefreq = 'daily'
    def items(self):
        return Post.objects.filter(status='publish')
    
    def lastmod(self, obj):
        return obj.pub_date
        
    def location(self, obj):
        return obj.get_site_url()
