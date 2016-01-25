#!/usr/bin/env python
# encoding: utf-8
"""
urls.py

Created by Eric Williams on 2007-02-27.
"""

# from django.conf.urls.defaults import *
# django.conf.urls.defaults will be removed. The functions 
# include(), patterns() and url() plus handler404, handler500, 
# are now available through django.conf.urls .

from django.conf.urls import include, patterns, url
from django.contrib.sites.models import Site
from django.contrib.sitemaps import GenericSitemap

from .models import Post
from .views.blog import AuthorListView
from .views.blog import PostYearArchiveView
from .views.blog import PostMonthArchiveView
from .views.blog import PostDayArchiveView
from .views.blog import PostArchiveIndexView
from .views.blog import PostDateDetailView

year_archive_pattern =r'^(?P<year>[0-9]{4})/$'
month_archive_pattern=r'^(?P<year>\d{4})/(?P<month>\w{3})/$'
day_archive_pattern  =r'^(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>\d{1,2})/$'
# date_detail_pattern=r'^(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>\d{2})/(?P<slug>[-\w]+)/$'
date_detail_pattern=r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w]+)/$'
post_edit_pattern=r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w]+)/edit/$'
post_stats_pattern=r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w]+)/stats/$'
post_preview_pattern=r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w]+)/preview/$'
post_set_publish_pattern=r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w]+)/set_publish/$'
template_preview_pattern=r'^template_preview/(?P<template_file>[-/\w]+)$'

PAGE_LENGTH=30

urlpatterns = patterns('',
    # remove xmlrpc view; use django_xmlprc instead
    # url(r'^xmlrpc/*','xblog.views.xmlrpc_views.call_xmlrpc', {'module':'xblog.metaWeblog'}),
#     url(r'^authors/$', AuthorListView.as_view(), 
#        name="author-list"),
    url(year_archive_pattern, PostYearArchiveView.as_view(paginate_by=PAGE_LENGTH), name="year-archive"),
    url(month_archive_pattern, PostMonthArchiveView.as_view(paginate_by=5), name="month-archive"),
    url(day_archive_pattern, PostDayArchiveView.as_view(paginate_by=PAGE_LENGTH), name="day-archive"),
    url(date_detail_pattern, PostDateDetailView.as_view(),name='post-detail'),
    url(post_edit_pattern, 'xblog.views.edit.edit_post',
        name="post-edit" ),
    url(post_stats_pattern, 'xblog.views.edit.stats',
        name="post-stats"), 
    url(post_preview_pattern, 'xblog.views.edit.preview_post', 
        name="post-preview"),
    url(post_set_publish_pattern, 'xblog.views.edit.set_publish', 
        name="post-set-publish"),
    url(r'add_post/$', 'xblog.views.edit.add_post', 
        name='post-add'),
    url(template_preview_pattern, 'xblog.views.blog.template_preview', 
        name='template-preview'),
    url(r'content_list/$', 'xblog.views.edit.content_list', 
        name='content-list'),
    url(r'export_opml/$', 'xblog.views.blog.export_opml',
        name='export-opml'),
    # url(r'^$', ArchiveIndexView.as_view(model=Post, date_field="pub_date", 
    #     paginate_by=PAGE_LENGTH, 
    #     queryset=Post.objects.all().filter(status="publish").select_related('author')), 
    #     name='archive-index',  ),
    url(r'^(?P<owner>\w+)/(?P<year>[0-9]{4})/$', PostYearArchiveView.as_view(paginate_by=PAGE_LENGTH)),
    url(r'^$', PostArchiveIndexView.as_view(model=Post,
        date_field="pub_date",
        paginate_by=PAGE_LENGTH,
        queryset=Post.objects.filter(status="publish")),
        name='site-overview'),
)