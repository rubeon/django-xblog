from xblog.models import Blog
from xcomments.models import FreeComment

def media_url(request):
    # from django.conf import settings
    # try:
    #   blog = Blog.objects.all()[0] # default for now...
    # except:
    #   blog=""

    # recent_comments = FreeComment.objects.order_by('-submit_date').filter(is_public=True)[:5]
    return {
        'media_url': settings.MEDIA_URL,
        'site_url' : settings.SITE_URL,
        'thisblog':blog,
        'recent_comments': recent_comments
    }
    
    