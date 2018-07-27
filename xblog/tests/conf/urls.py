from django.conf.urls import url, include
from django.contrib import admin
import xblog.urls
from django_xmlrpc.views import handle_xmlrpc


urlpatterns = [
    url(r'admin/', admin.site.urls),
    url(r'blog/', include(xblog.urls, namespace='xblog')),
    url(r'xmlrpc/', handle_xmlrpc, name='xmlrpc'),
]
