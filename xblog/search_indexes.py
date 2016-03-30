import datetime
from haystack import indexes
# from myapp.models import Note
from models import Blog, Post


# class NoteIndex(indexes.SearchIndex, indexes.Indexable):
#     text = indexes.CharField(document=True, use_template=True)
#     author = indexes.CharField(model_attr='user')
#     pub_date = indexes.DateTimeField(model_attr='pub_date')
#
#     def get_model(self):
#         return Note
#
#     def index_queryset(self, using=None):
#         """Used when the entire index for model is updated."""
#         return self.get_model().objects.filter(pub_date__lte=datetime.datetime.now())
#

class PostIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True, model_attr='full_body')
    author = indexes.CharField(model_attr='author')
    pub_date = indexes.DateTimeField(model_attr='pub_date')

    def get_model(self):
        return Post

    def index_queryset(self, using=None):
        return self.get_model().objects.filter(pub_date__lte=datetime.datetime.now()).filter(status="publish")
