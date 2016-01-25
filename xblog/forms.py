from django.forms import ModelForm, CharField
from models import Author, Blog

class EditAuthorForm(ModelForm):

    class Meta:
        model = Author
        exclude = ('user',)
        
class EditBlogForm(ModelForm):

    class Meta:
        model = Blog
        exclude = ('owner',)
        