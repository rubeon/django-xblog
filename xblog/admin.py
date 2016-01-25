from django.contrib import admin
from django.contrib.auth.models import User

from xblog.models import LinkCategory, Link, Pingback, Tag, Author, Post, Blog
from xblog.models import STATUS_CHOICES, FILTER_CHOICES
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class LinkCategoryAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ['title',]
admin.site.register(LinkCategory, LinkCategoryAdmin)

class LinkAdmin(admin.ModelAdmin):
    list_display = ('url', 'description')
admin.site.register(Link, LinkAdmin)

class PingbackAdmin(admin.ModelAdmin):
    # list_display = ('pub_date', 'title', 'source_url','target_url')
    search_fields = ('title','pub_date',)
    list_filter = ['pub_date', 'is_public']
admin.site.register(Pingback, PingbackAdmin)

class TagAdmin(admin.ModelAdmin):

    list_display = ('title',)
    search_fields = ('title',)
admin.site.register(Tag, TagAdmin)

class AuthorInline(admin.StackedInline):
    model = Author
    can_delete = False

class AuthorAdmin(BaseUserAdmin):
    inlines = (AuthorInline,)
  
  
admin.site.unregister(User)  
admin.site.register(User, AuthorAdmin)

# admin.site.register(Author, AuthorAdmin)

# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ('title','blog')
#     search_fields = ('title',)
# admin.site.register(Category, CategoryAdmin)
# 
class PostAdmin(admin.ModelAdmin):
    # list_display = ('title',)
    list_display = ('title','pub_date') #,'author','status')
    search_fields = ('title','body','slug')
    date_hierarchy = 'pub_date'
    list_filter = ['author','pub_date', 'status', 'tags', ]
    
    
    
    fieldsets = (
      (None, {'fields':('title','slug','guid')}),
      ('Date & Time',{'fields':("pub_date","update_date", "create_date")}),
      (None, {'fields':('text_filter','body',)}),
      ('Metadata', {'fields':(
                    'post_format',
                    'tags',
                    'blog',
                    'author',
                    'status',
                    'enable_comments')}),
    )
    
    prepopulated_fields = {"slug": ("title",)}
    radio_fields = {"status":admin.VERTICAL, 
                    "text_filter":admin.VERTICAL}
                    
    readonly_fields = ("update_date", "create_date")
admin.site.register(Post, PostAdmin)

class BlogAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)
admin.site.register(Blog, BlogAdmin)

