"""
urls.py

Created by Eric Williams on 2007-02-27.
"""

# from django.conf.urls import url
from django.urls import include, re_path, path

from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from .models import Post, Tag
from .views.blog import AuthorCreateView
from .views.blog import AuthorDetailView

from .views.blog import BlogCreateView
from .views.blog import BlogDetailView
from .views.blog import BlogUpdateView

from .views.blog import PostYearArchiveView
from .views.blog import PostMonthArchiveView
from .views.blog import PostDayArchiveView
from .views.blog import PostArchiveIndexView
from .views.blog import PostDateDetailView
from .views.blog import CategoryDetailView
from .views.blog import export_opml
from .views.blog import template_preview
from .views.blog import TagListView
from .views.blog import TagDetailView

from .views.post import PostCreateView
from .views.post import PostUpdateView
from .views.post import PostDeleteView
from .views.post import xhr_tags

from .views.edit import stats
from .views.edit import preview_post
from .views.edit import set_publish
from .views.edit import content_list

from .feeds import LatestPostsFeed

YEAR_ARCHIVE_PATTERN = r'^(?P<year>\d{4})/$'
MONTH_ARCHIVE_PATTERN = r'^(?P<year>\d{4})/(?P<month>\w{3})/$'
DAY_ARCHIVE_PATTERN = r'^(?P<year>\d{4})/(?P<month>\w{3})/(?P<day>\d{1,2})/$'
DATE_DETAIL_PATTERN = \
    r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w]+)/$'
POST_UPDATE_PATTERN = \
    r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w]+)/edit/$'
POST_DELETE_PATTERN = \
    r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w]+)/delete/$'
POST_STATS_PATTERN = \
    r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w]+)/stats/$'
POST_PREVIEW_PATTERN = \
    r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w]+)/preview/$'
POST_SET_PUBLISH_PATTERN = \
    r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w]+)/set_publish/$'

TEMPLATE_PREVIEW_PATTERN = r'^template_preview/(?P<template_file>[-/\w]+)$'

BLOG_DETAIL_PATTERN = r'^space/(?P<slug>[-\w]+)/$'
BLOG_UPDATE_PATTERN = r'^space/(?P<slug>[-\w]+)/edit/$'

CATEGORY_DETAIL_PATTERN = r'^space/(?P<blog_slug>[-\w]+)/(?P<cat_slug>[-\w]+)/$'
CATEGORY_UPDATE_PATTERN = r'^space/(?P<blog_slug>[-\w]+)/(?P<cat_slug>[-\w]+)/$'

AUTHOR_DETAIL_PATTERN = r'^author/(?P<username>\w+)/$'

PAGE_LENGTH = 30

app_name = 'xblog'

urlpatterns = [
    re_path(YEAR_ARCHIVE_PATTERN, PostYearArchiveView.as_view(paginate_by=PAGE_LENGTH),
        name="year-archive"),
    re_path(MONTH_ARCHIVE_PATTERN, PostMonthArchiveView.as_view(paginate_by=5),
        name="month-archive"),
    re_path(DAY_ARCHIVE_PATTERN, PostDayArchiveView.as_view(paginate_by=PAGE_LENGTH),
        name="day-archive"),
    re_path(DATE_DETAIL_PATTERN, PostDateDetailView.as_view(),
        name='post-detail'),
    re_path(POST_STATS_PATTERN, stats,
        name="post-stats"),
    re_path(POST_PREVIEW_PATTERN, preview_post,
        name="post-preview"),
    re_path(POST_SET_PUBLISH_PATTERN, set_publish,
        name="post-set-publish"),
    re_path(r'add_post/$', login_required(PostCreateView.as_view()),
        name='post-add'),
    re_path(POST_UPDATE_PATTERN, login_required(PostUpdateView.as_view()),
        name='post-edit'),
    re_path(POST_DELETE_PATTERN, login_required(PostDeleteView.as_view()),
        name='post-delete'),
    re_path(r'add_blog/$', login_required(BlogCreateView.as_view()),
        name='blog-add'),
    re_path(BLOG_UPDATE_PATTERN, login_required(BlogUpdateView.as_view()),
        name='blog-update'),
    re_path(BLOG_DETAIL_PATTERN, BlogDetailView.as_view(),
        name='blog-detail'),
    re_path(CATEGORY_DETAIL_PATTERN, CategoryDetailView.as_view(paginate_by=PAGE_LENGTH),
        name='category-detail'),
    re_path(r'add_author/$', staff_member_required(AuthorCreateView.as_view()),
        name='author-add'),
    re_path(AUTHOR_DETAIL_PATTERN, AuthorDetailView.as_view(),
        name='author-detail'),
    re_path(r'content_list/$', content_list,
        name='content-list'),
    re_path(r'export_opml/$', export_opml,
        name='export-opml'),
    re_path(TEMPLATE_PREVIEW_PATTERN, template_preview,
        name='template-preview'),
    # # re_path(r'^$', ArchiveIndexView.as_view(model=Post, date_field="pub_date",
    #     paginate_by=PAGE_LENGTH,
    #     queryset=Post.objects.all().filter(status="publish").select_related('author')),
    #     name='archive-index',  ),
    re_path(r'^(?P<owner>\w+)/(?P<year>[0-9]{4})/$',
        PostYearArchiveView.as_view(paginate_by=PAGE_LENGTH)),
    path('tag/<slug:slug>/', TagDetailView.as_view(model=Tag), name='tag-detail'),
    path('tags/', TagListView.as_view(model=Tag), name='tag-overview'),
    # re_path(r'^tags/$', xhr_tags),
    re_path(r'^feed/$', LatestPostsFeed(), name="feed-posts"),
    re_path(r'^$', PostArchiveIndexView.as_view(model=Post,
                                            date_field="pub_date",
                                            paginate_by=PAGE_LENGTH,
                                            queryset=Post.objects.filter(status="publish")),
        name='site-overview',
       ),
]
