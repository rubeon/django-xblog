from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse_lazy

from django.views.generic.edit import UpdateView
from django.views.generic.edit import DeleteView
from django.views.generic.edit import CreateView

from django.views.generic.detail import DetailView

from django.http import Http404

from ..models import Post
from ..models import Blog

from django.contrib.sites.models import Site


# @login_required

class PostCreateView(SuccessMessageMixin, CreateView):
    """
    View for adding a post
    """
    model = Post
    fields = ['title', 'body', 'status', 'tags', 'text_filter', 'post_format']
    success_url = reverse_lazy("site-overview")
    success_message = "Post '%(title)s created!"
    
    def form_valid(self, form):
        form.instance.author = self.request.user.author
        form.instance.site = Site.objects.get_current()
        form.instance.blog = Blog.objects.filter(owner=self.request.user)[0]
        return super(PostCreateView, self).form_valid(form)
        
    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data)
        
    def get_success_url(self):
        return reverse_lazy("site-overview")
    
    
class PostUpdateView(SuccessMessageMixin, UpdateView):
    """
    View for editing an existing post
    """
    success_message = "Post '%(title)s' saved!" 
    model = Post
    fields = ['title', 'body', 'status', 'tags', 'text_filter', 'post_format']
    
    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data)
        
    def get_success_url(self):
        return reverse_lazy("site-overview")
    
class PostDeleteView(SuccessMessageMixin, DeleteView):
    model = Post
    success_url = reverse_lazy("site-overview")
    success_message = "Post '%(title)s deleted!"

    def get_success_message(self, cleaned_data):
        return self.success_message % dict(cleaned_data)
    
    def get_object(self, queryset=None):
           """ Hook to ensure object is owned by request.user. """
           obj = super(PostDeleteView, self).get_object()
           if not obj.author.user == self.request.user:
               raise Http404
           return obj
           
