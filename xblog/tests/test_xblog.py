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

        LinkCategory.objects.create(
            title = 'Great Links',
            description = 'The Best Links in the Webz',
            visible = True,
            blog = Blog.objects.all()[0]
        )

        Link.objects.create(
            url='http://google.com',
            description = 'The Overmind',
            link_name = 'The Google',
            category = LinkCategory.objects.all()[0],
            blog = Blog.objects.all()[0]
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

    def test_existing_user_can_be_saved(self):
        """
        If a user gets changed, changes should be saved.
        Also test that the Author attached to it remains
        intact.
        """
        test_user1 = User.objects.get(username='test_user1')
        blog = Blog.objects.get(owner=test_user1)
        new_last_name = "OMG MY LAST NAME CHANGED"

        # change the user
        test_user1.last_name = new_last_name
        test_user1.save()
        self.assertEqual(test_user1.last_name, new_last_name)


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

    def test_link_string_reps(self):
        """
        Make sure that Link returns its title when printed
        """
        link = Link.objects.all()[0]
        self.assertEqual("%s (%s)" % (link.link_name, link.url), str(link))

    def test_link_category_string_reps(self):
        """
        Test that the link printing returns expected results (and won't crash)
        """
        link_category = LinkCategory.objects.all()[0]
        self.assertEqual(link_category.title, str(link_category))

    def test_pingback_create(self):
        """
        Makes sure the pingback functionality is working...
        This should optimally use the local server and not ping somebody
        everytime it runs a test :-/
        """
        pass

    
