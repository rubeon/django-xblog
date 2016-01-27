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
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from .models import Post
from .views.blog import AuthorCreateView
from .views.blog import AuthorListView
from .views.blog import AuthorDetailView

from .views.blog import BlogCreateView
from .views.blog import BlogDetailView
from .views.blog import BlogUpdateView

from .views.blog import PostYearArchiveView
from .views.blog import PostMonthArchiveView
from .views.blog import PostDayArchiveView
from .views.blog import PostArchiveIndexView
from .views.blog import PostDateDetailView

from .views.post import PostCreateView
from .views.post import PostUpdateView
from .views.post import PostDeleteView




year_archive_pattern =r'^(?P<year>[0-9]{4})/$'
month_archive_pattern=r'^(?P<year>\d{4})/(?P<month>\w{3})/$'
day_archive_pattern  =r'^(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>\d{1,2})/$'
# date_detail_pattern=r'^(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>\d{2})/(?P<slug>[-\w]+)/$'
date_detail_pattern=r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w]+)/$'

post_update_pattern=r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w]+)/edit/$'
post_delete_pattern=r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w]+)/delete/$'
post_stats_pattern=r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w]+)/stats/$'
post_preview_pattern=r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w]+)/preview/$'
post_set_publish_pattern=r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w]+)/set_publish/$'

template_preview_pattern=r'^template_preview/(?P<template_file>[-/\w]+)$'

blog_detail_pattern = r'^blog_details/(?P<pk>\d)/$'
blog_update_pattern = r'^blog_update/(?P<pk>\d)/edit/$'

author_detail_pattern = r'^author_detail/(?P<username>\w+)/$'

PAGE_LENGTH=30

urlpatterns = [
    url(year_archive_pattern, PostYearArchiveView.as_view(paginate_by=PAGE_LENGTH), name="year-archive"),
    url(month_archive_pattern, PostMonthArchiveView.as_view(paginate_by=5), name="month-archive"),
    url(year_archive_pattern, PostYearArchiveView.as_view(paginate_by=PAGE_LENGTH), name="year-archive"),
    url(month_archive_pattern, PostMonthArchiveView.as_view(paginate_by=5), name="month-archive"),
    url(day_archive_pattern, PostDayArchiveView.as_view(paginate_by=PAGE_LENGTH), name="day-archive"),
    url(date_detail_pattern, PostDateDetailView.as_view(),name='post-detail'),

    url(post_stats_pattern, 'xblog.views.edit.stats',
        name="post-stats"), 
    url(post_preview_pattern, 'xblog.views.edit.preview_post', 
        name="post-preview"),
    url(post_set_publish_pattern, 'xblog.views.edit.set_publish', 
        name="post-set-publish"),

    url(r'add_post/$', login_required(PostCreateView.as_view()), name='post-add'),
    url(post_update_pattern, login_required(PostUpdateView.as_view()), name="post-edit" ),
    url(post_delete_pattern, login_required(PostDeleteView.as_view()), name="post-delete" ),

    url(r'add_blog/$', login_required(BlogCreateView.as_view()), name='blog-add'),
    url(blog_update_pattern, login_required(BlogUpdateView.as_view()), name='blog-update'),
    url(blog_detail_pattern, BlogDetailView.as_view(), name='blog-detail'),

    url(r'add_author/$', staff_member_required(AuthorCreateView.as_view()), name='author-add'),
    url(author_detail_pattern, AuthorDetailView.as_view(), name='author-detail'),
        
    url(r'content_list/$', 'xblog.views.edit.content_list', 
        name='content-list'),
    url(r'export_opml/$', 'xblog.views.blog.export_opml',
        name='export-opml'),
        
    url(template_preview_pattern, 'xblog.views.blog.template_preview', 
        name='template-preview'),
    
    # url(r'^$', ArchiveIndexView.as_view(model=Post, date_field="pub_date", 
    #     paginate_by=PAGE_LENGTH, 
    #     queryset=Post.objects.all().filter(status="publish").select_related('author')), 
    #     name='archive-index',  ),
    url(r'^(?P<owner>\w+)/(?P<year>[0-9]{4})/$', PostYearArchiveView.as_view(paginate_by=PAGE_LENGTH)),
    url(r'^$', PostArchiveIndexView.as_view(model=Post,
        date_field="pub_date",
        paginate_by=PAGE_LENGTH,
        queryset=Post.objects.filter(status="publish")),
        name='site-overview',
        ),
    
]

