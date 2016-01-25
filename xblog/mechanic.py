from django.conf.urls.defaults import *
from feeds import Posts

feeds = {
    # 'podcasts': Podcasts,
    'blogs': Posts,
}


urlpatterns = patterns('',
    # Example:
    # (r'^xoff/', include('xoff.foo.urls')),
    (r'gallery/main.php$', 'xgallery.galleryAPI.dispatcher'), 
    # (r'^gallery/$', 'blog.xmlrpc_views.call_xmlrpc', {'module':'gallery.galleryAPI'}),
    (r'^xmlrpc/$','xblog.views.xmlrpc_views.call_xmlrpc', {'module':'xblog.views.metaWeblog'}),
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed',{'feed_dict': feeds}),
    
    


)
