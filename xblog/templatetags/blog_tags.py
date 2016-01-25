#!/usr/bin/env python
# encoding: utf-8
"""
templatetags.py

Created by Eric Williams on 2007-03-10.
"""
import logging
logger = logging.getLogger(__name__)
from xblog.models import LinkCategory, Link, Post
from django.template import Library, Node
register = Library()



def get_blogroll(parser, token):
    """
    {% get_blogroll %}
    """
    return BlogRoll()
    
def get_blog_months(parser, token):
    """{% get_blog_months %}"""
    return MonthMenuObject()
    
class MonthMenuObject(Node):
    def render(self, context):
        context['blog_months'] = Post.objects.datetimes("pub_date", "month")
        return ''

class BlogRoll(Node):
    """A Blogroll object...."""
    def render(self, context):
        context['blogroll_categories'] = LinkCategory.objects.all()
        return ''
        
        
logging.info( "Registering 'get_blogroll'")
register.tag('get_blogroll', get_blogroll)
logging.info( "Registering 'get_blog_months'")
register.tag('get_blog_months', get_blog_months)