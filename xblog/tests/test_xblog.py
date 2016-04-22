# -*- coding: utf8 -*-
from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

from xblog.models import Post
from xblog.models import Blog
from xblog.models import Author
from xblog.models import Category
from xblog.models import Link
from xblog.models import LinkCategory
from xblog.models import FILTERS

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class PostTestCase(TestCase):
    def setUp(self):
        """
        Create the test objects
        """

        # create our test user
        User.objects.create(
            username="test_user1",
            first_name="Test",
            last_name="User2",
            email="testuser@example.com",
            password="MyTestPass1",
            is_staff=False,
            is_superuser=False
        )

        #
        User.objects.create(
            username="test_user2",
            first_name="Test",
            last_name="User2",
            email="testuser2@example.com",
            password="MyTestPass1",
            is_staff=False,
            is_superuser=False
        )
        User.objects.create(
            username="admin",
            first_name="Admin",
            last_name="User",
            email="admin@example.com",
            password="MyAdminPass1",
            is_staff=True,
            is_superuser=True
        )

        Blog.objects.create(
            title="Test User 1's Space",
            description="A blog for Test User 1.  Slippery when wet!",
            owner = User.objects.get(username="test_user1"),
            site = Site.objects.get_current()
        )

    def test_create_posts_own_blog(self):
        test_user1 = User.objects.get(username='test_user1')
        Post.objects.create(
            title = "Test User 1 Post",
            body = "This is some stuff.\n\nSome stuff, you know.",
            blog = Blog.objects.get(owner=test_user1),
            author = test_user1.author
        )

        # Post.objects.create(
        #     title = "Test User 2 Post",
        #     body = "This is some stuff.\n\nSome stuff, you know.",
        #     blog = Blog.objects.get(owner=test_user2),
        #     author = test_user1.author
        # )

    def test_create_posts_other_dudes_blog(self):
        # this should fail
        test_user1 = User.objects.get(username='test_user1')
        test_user2 = User.objects.get(username='test_user2')
        with self.assertRaises(PermissionDenied):
            Post.objects.create(
                title = "Test User 1 Post",
                body = "This is some stuff.\n\nSome stuff, you know.",
                blog = Blog.objects.get(owner=test_user1),
                author = test_user2.author
            )

    def test_new_user_gets_author(self):
        """
        New users should automatically get authors.
        Shows that signal connection in xblog.models is working.
        """
        test_user1 = User.objects.get(username='test_user1')
        # get user's blog
        blog = Blog.objects.get(owner=test_user1)
        self.assertEqual(test_user1.author, blog.owner.author)


    def test_post_with_utf8(self):
        test_user1 = User.objects.get(username='test_user1')
        Post.objects.create(
            title = u"Für großes Gerecht!",
            body = u"This is some stuff.\n\nSome stuff, you know.",
            blog = Blog.objects.get(owner=test_user1),
            author = test_user1.author
        )

    def test_post_text_filter_smoketest(self):
        # makes sure the FILTERS are all 'working'
        source_file = os.path.join(BASE_DIR, "resources/test_post.html")
        test_user1 = User.objects.get(username='test_user1')
        body = open(source_file).read()
        for filter in FILTERS.keys():
            p = Post.objects.create(
                title = "Test Text",
                body = body,
                blog = Blog.objects.get(owner=test_user1),
                author = test_user1.author,
                text_filter = filter
            )
            self.assertEquals(p.get_full_body(), FILTERS[filter](body))

    def test_post_text_filter_html(self):
        """
        HTML filter should return the raw text, more or less
        """
        test_user1 = User.objects.get(username='test_user1')
        source_file = os.path.join(BASE_DIR, "resources/test_post.html")
        body = open(source_file).read()
        p = Post.objects.create(
            title = "Test Text",
            body = open(source_file).read(),
            blog = Blog.objects.get(owner=test_user1),
            author = test_user1.author,
            text_filter = 'html'
        )
        self.assertEquals(body, p.get_full_body())


    def test_post_text_filter_markdown(self):
        """
        HTML filter should return the raw text, more or less
        """
        test_user1 = User.objects.get(username='test_user1')
        source_file = os.path.join(BASE_DIR, "resources/test_post.md")
        body = open(source_file).read()
        p = Post.objects.create(
            title = "Test Text",
            body = open(source_file).read(),
            blog = Blog.objects.get(owner=test_user1),
            author = test_user1.author,
            text_filter = 'markdown'
        )
        # make sure link is working
        self.assertIn("<a href=\"http://www.example.com/\">Link text</a>", p.get_full_body())

        # check for footnotes
        self.assertIn('footnoteBackLink', p.get_full_body())
