"""

Custom forms for xblog models


"""
from django.forms import ModelForm
from .models import Post

class PostCreateForm(ModelForm):
    """
    Defines the create form for Post objects
    """
    class Meta:
        """
        Meta class for admin
        """
        model = Post
        fields = ['title', 'body', 'categories', 'status', 'tags', 'text_filter', 'blog', 'sticky', 'post_format', 'post_type', 'sticky']

