#!/usr/bin/env python
# encoding: utf-8
"""
urls.py

Created by Eric Williams on 2007-02-24.
"""

from django.conf.urls.defaults import *
from models import Post

info_dict = {
    'queryset':Post.objects.all(),
    'date_field':'pub_date'
}

urlpatterns = patterns('django.views.generic.date_based',
      (r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w]+)/$', 'object_detail', dict(info_dict, slug_field='slug')),
      (r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/$',               'archive_day',   dict(info_dict,month_format="%b")),
      (r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/$',                                'archive_month', info_dict),
      (r'^(?P<year>\d{4})/$',                                                    'archive_year',  dict(info_dict, make_object_list=True)),
      (r'^/?$',                                                                  'archive_index', dict(info_dict)),
    

)