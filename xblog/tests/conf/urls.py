from django.urls import include, re_path, path

from django.contrib import admin
import xblog.urls
from django_xmlrpc_dx.views import handle_xmlrpc


urlpatterns = [
    path(r'admin/', admin.site.urls),
    path(r'blog/', include(xblog.urls, namespace='xblog')),
    path(r'xmlrpc/', handle_xmlrpc, name='xmlrpc'),
]
