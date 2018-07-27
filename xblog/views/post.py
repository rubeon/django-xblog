from django.contrib.messages.views import SuccessMessageMixin
try:
    from django.urls import reverse_lazy
except ImportError: # django < 2
    from django.core.urlresolvers import reverse_lazy


from django.views.generic.edit import UpdateView
from django.views.generic.edit import DeleteView
from django.views.generic.edit import CreateView
from django.core import serializers

from django.views.generic.detail import DetailView

from django.http import Http404, HttpResponse

from ..models import Post
from ..models import Blog
from ..models import Tag
from ..forms import PostCreateForm

from django.contrib.sites.models import Site
import logging
logger = logging.getLogger('xblog')

def xhr_tags(request): 
    logger.debug("%s.xhr_tags entered" % __name__)
    res = []
    for tag in Tag.objects.all():
        res.append(tag)
    if request.is_ajax() or True:
        data = serializers.serialize('json', res)
        return HttpResponse(data,'json')

class PostCreateView(SuccessMessageMixin, CreateView):
    """
    View for adding a post
    """
    # model = Post
    # fields = ['title', 'body', 'status', 'tags', 'text_filter', 'post_format', 'blog', 'categories']
    form_class = PostCreateForm
    success_url = reverse_lazy("xblog:site-overview")
    success_message = "Post '%(title)s created!"
    template_name = "xblog/post_form.html"
    
    def get_initial(self):
        """
        - sets the blog to be the most recently updated one
        """
        logger.debug("%s.get_initial entered" % self)
        recent_posts = Post.objects.filter(author=self.request.user.author).order_by("-pub_date")
        if recent_posts:
            blog = recent_posts[0].blog
            text_filter = recent_posts[0].text_filter
        else:
            blog = None
            text_filter = None
        return {'blog':blog, 'text_filter': text_filter, 'status': 'draft'}
    
    def form_valid(self, form):
        form.instance.author = self.request.user.author
        form.instance.site = Site.objects.get_current()
        # form.instance.blog = Blog.objects.filter(owner=self.request.user)
        return super(PostCreateView, self).form_valid(form)
        
    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data)
        
    def get_success_url(self):
        return reverse_lazy("xblog:site-overview")
    
    
class PostUpdateView(SuccessMessageMixin, UpdateView):
    """
    View for editing an existing post
    """
    success_message = "Post '%(title)s' saved!" 
    model = Post
    fields = ['title', 'body', 'status', 'categories', 'tags', 'text_filter', 'post_format']
    
    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data)
        
    def get_success_url(self):
        return reverse_lazy("xblog:site-overview")
    
class PostDeleteView(SuccessMessageMixin, DeleteView):
    model = Post
    success_url = reverse_lazy("xblog:site-overview")
    success_message = "Post '%(title)s deleted!"

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data)
    
    def get_object(self, queryset=None):
           """ Hook to ensure object is owned by request.user. """
           obj = super(PostDeleteView, self).get_object()
           if not obj.author.user == self.request.user:
               raise Http404
           return obj
           
