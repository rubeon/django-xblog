# auto-register file for django_xmlrpc

# from .views import wp
# import metaWeblog

"""
This file defines XMLRPC methods for use
by XBlog. Works with django-xmlrpc
"""

XMLRPC_METHODS = (
    ('xblog.views.blogger.deletePost', 'blogger.deletePost'),
    ('xblog.views.blogger.getRecentPosts', 'blogger.getRecentPosts'),
    ('xblog.views.blogger.getUserInfo', 'blogger.getUserInfo'),
    ('xblog.views.blogger.getUsersBlogs', 'blogger.getUsersBlogs'),
    ('xblog.views.metaWeblog.deletePost', 'metaWeblog.deletePost'),
    ('xblog.views.metaWeblog.editPost', 'metaWeblog.editPost'),
    ('xblog.views.metaWeblog.getCategories', 'metaWeblog.getCategories'),
    ('xblog.views.metaWeblog.getRecentPosts', 'metaWeblog.getRecentPosts'),
    ('xblog.views.metaWeblog.getUsersBlogs', 'metaWeblog.getUsersBlogs'),
    ('xblog.views.metaWeblog.newMediaObject', 'metaWeblog.newMediaObject'),
    ('xblog.views.metaWeblog.newPost', 'metaWeblog.newPost'),
    ('xblog.views.metaWeblog.getPost', 'metaWeblog.getPost'),
    ('xblog.views.mt.getCategoryList', 'mt.getCategoryList'),
    ('xblog.views.mt.getPostCategories', 'mt.getPostCategories'),
    ('xblog.views.mt.publishPost', 'mt.publishPost'),
    ('xblog.views.mt.setPostCategories', 'mt.setPostCategories'),
    ('xblog.views.mt.supportedMethods', 'mt.supportedMethods'),
    ('xblog.views.mt.supportedTextFilters', 'mt.supportedTextFilters'),
    # ('xblog.views.wp.getUsersBlogs', 'wp.getUsersBlogs'),
    ('xblog.views.wp.getOptions', 'wp.getOptions'),
    ('xblog.views.wp.getCategories', 'wp.getCategories'),
    ('xblog.views.wp.getPosts', 'wp.getPosts'),
    ('xblog.views.wp.getPost', 'wp.getPost'),
    ('xblog.views.wp.newPost', 'wp.newPost'),
    ('xblog.views.wp.getUser', 'wp.getUser'),
    ('xblog.views.wp.getProfile', 'wp.getProfile'),

    # ('xblog.views.wp.getTags', 'wp.getTags'),

    ('xblog.views.wp.getUsersBlogs', 'wp.getUsersBlogs'),
    ('xblog.views.wp.newCategory', 'wp.newCategory'),
    ('xblog.views.wp.getOptions', 'wp.getOptions'),
    # ('xblog.views.wp.getPost', 'wp.getPost'),


)
