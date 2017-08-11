# -*- coding: utf-8 -*-

"""
admin.py

Created by Eric Williams on 2007-02-24.
"""

from django.contrib import admin
from xblog.models import LinkCategory, Link, Pingback, Tag, Author, Post, Blog, Category

class LinkCategoryAdmin(admin.ModelAdmin):
    """
    Admin class for LinkCategory
    """
    list_display = ('title',)
    search_fields = ['title',]
admin.site.register(LinkCategory, LinkCategoryAdmin)

class LinkAdmin(admin.ModelAdmin):
    """
    Admin class for Link
    """
    list_display = ('url', 'description')
admin.site.register(Link, LinkAdmin)

class PingbackAdmin(admin.ModelAdmin):
    """
    Admin class for Pingback
    """
    # list_display = ('pub_date', 'title', 'source_url','target_url')
    search_fields = ('title', 'pub_date',)
    list_filter = ['pub_date', 'is_public']
admin.site.register(Pingback, PingbackAdmin)

class TagAdmin(admin.ModelAdmin):
    """
    Admin class for Tag
    """
    list_display = ('title',)
    search_fields = ('title',)
admin.site.register(Tag, TagAdmin)

class AuthorAdmin(admin.ModelAdmin):
    """
    Admin class for Author
    """
    model = Author
    search_fields = ('fullname', 'user')
    list_display = ('user', 'fullname')
admin.site.register(Author, AuthorAdmin)

class PostAdmin(admin.ModelAdmin):
    """
    Admin class for Post
    """
    # list_display = ('title',)
    list_display = ('title', 'slug', 'pub_date') #,'author','status')
    search_fields = ('title', 'body', 'slug')
    date_hierarchy = 'pub_date'
    list_filter = ['author', 'pub_date', 'status', 'tags',]

    fieldsets = (
        (None, {'fields':('title', 'slug', 'guid')}),
        ('Date & Time', {'fields':('pub_date', 'update_date', 'create_date')}),
        (None, {'fields':('text_filter', 'body', 'categories')}),
        ('Metadata', {'fields':(
            'post_format',
            'tags',
            'blog',
            'author',
            'status',
            'enable_comments')}),
    )

    prepopulated_fields = {'slug': ('title',)}
    radio_fields = {'status':admin.VERTICAL,
                    'text_filter':admin.VERTICAL}
    readonly_fields = ('update_date', 'create_date')

admin.site.register(Post, PostAdmin)

class BlogAdmin(admin.ModelAdmin):
    """
    Admin class for Blog
    """
    list_display = ('title',)
    search_fields = ('title',)

admin.site.register(Blog, BlogAdmin)

class CategoryAdmin(admin.ModelAdmin):
    """
    Admin class for Category
    """
    list_display = ('title', 'blog')
    search_fields = ('title',)

admin.site.register(Category, CategoryAdmin)
