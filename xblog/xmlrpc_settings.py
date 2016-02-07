# auto-register file for django_xmlrpc

# from .views import wp
# import metaWeblog

XMLRPC_METHODS = (
    ('xblog.metaWeblog.blogger_deletePost', 'blogger.deletePost'),
    ('xblog.metaWeblog.blogger_getRecentPosts', 'blogger.getRecentPosts'),
    ('xblog.metaWeblog.blogger_getUserInfo', 'blogger.getUserInfo'),
    ('xblog.metaWeblog.blogger_getUsersBlogs', 'blogger.getUsersBlogs'),
    ('xblog.views.metaWeblog.deletePost', 'metaWeblog.deletePost'),
    ('xblog.views.metaWeblog.editPost', 'metaWeblog.editPost'),
    ('xblog.views.metaWeblog.getCategories', 'metaWeblog.getCategories'),
    ('xblog.views.metaWeblog.getRecentPosts', 'metaWeblog.getRecentPosts'),
    ('xblog.views.metaWeblog.getUsersBlogs', 'metaWeblog.getUsersBlogs'),
    ('xblog.views.metaWeblog.newMediaObject', 'metaWeblog.newMediaObject'),
    ('xblog.views.metaWeblog.newPost', 'metaWeblog.newPost'),
    ('xblog.views.metaWeblog.getPost', 'metaWeblog.getPost'),
    ('xblog.metaWeblog.mt_getCategoryList', 'mt.getCategoryList'),
    ('xblog.metaWeblog.mt_getPostCategories', 'mt.getPostCategories'),
    ('xblog.metaWeblog.mt_publishPost', 'mt.publishPost'),
    ('xblog.metaWeblog.mt_setPostCategories', 'mt.setPostCategories'),
    ('xblog.metaWeblog.mt_supportedMethods', 'mt.supportedMethods'),
    ('xblog.metaWeblog.mt_supportedTextFilters', 'mt.supportedTextFilters'),
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
    # ('xblog.views.wp.getOptions', 'wp.getOptions'),
    # ('xblog.views.wp.getPost', 'wp.getPost'),
    
    
)
