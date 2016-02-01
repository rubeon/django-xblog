# auto-register file for django_xmlrpc

# from .views import wp
# import metaWeblog

XMLRPC_METHODS = (
    ('xblog.metaWeblog.blogger_deletePost', 'blogger.deletePost'),
    ('xblog.metaWeblog.blogger_getRecentPosts', 'blogger.getRecentPosts'),
    ('xblog.metaWeblog.blogger_getUserInfo', 'blogger.getUserInfo'),
    ('xblog.metaWeblog.blogger_getUsersBlogs', 'blogger.getUsersBlogs'),
    ('xblog.metaWeblog.metaWeblog_deletePost', 'metaWeblog.deletePost'),
    ('xblog.metaWeblog.metaWeblog_editPost', 'metaWeblog.editPost'),
    ('xblog.metaWeblog.metaWeblog_getCategories', 'metaWeblog.getCategories'),
    ('xblog.metaWeblog.metaWeblog_getRecentPosts', 'metaWeblog.getRecentPosts'),
    ('xblog.metaWeblog.metaWeblog_getUsersBlogs', 'metaWeblog.getUsersBlogs'),
    ('xblog.metaWeblog.metaWeblog_newMediaObject', 'metaWeblog.newMediaObject'),
    ('xblog.metaWeblog.metaWeblog_newPost', 'metaWeblog.newPost'),
    ('xblog.metaWeblog.metaWeblog_getPost', 'metaWeblog.getPost'),
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
