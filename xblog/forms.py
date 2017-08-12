"""

Custom forms for xblog models


"""
from django.forms import ModelForm
# from django.forms import CharField

# from .models import Author
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
        fields = ['title', 'body', 'categories', 'status', 'tags', 'text_filter', 'blog']

        # def __init__(self, *args, **kwargs):
        #     ModelForm.__init__(self, *args, **kwargs)
        #     self.fields['project'].queryset = Post.objects.filter(Project.status == 2)
