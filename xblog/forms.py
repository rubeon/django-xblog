from django.forms import ModelForm, CharField

from .models import Author
from .models import Post

class PostCreateForm(ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'body','categories','status', 'tags', 'text_filter', 'blog']
        
        def __init__(self, *args, **kwargs):
            super(WorklogCreateForm, self).__init__(self, *args, **kwargs)
            self.fields['project'].queryset = Post.objects.filter(Project.status == 2)


