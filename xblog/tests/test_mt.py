"""
test case for mt. xmlrpc methods
"""

from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test.utils import override_settings
from django.test.client import Client
from django.conf import settings

from xblog.models import Post
from xblog.models import Blog
from xblog.models import Author
from xblog.models import Category
from xblog.models import Link
from xblog.models import Tag
from xblog.models import LinkCategory
from xblog.models import FILTERS

from datetime import datetime

try:
    from xmlrpc.client import Binary
    from xmlrpc.client import Fault
    from xmlrpc.client import ServerProxy
except ImportError:  # Python 2
    from xmlrpclib import Binary
    from xmlrpclib import Fault
    from xmlrpclib import ServerProxy

from .utils import TestTransport

post_content = {
    'title':'This is a test title',
    'description': "<p>This is the post content.  Hey-ooooo!</p>",
    'post_type': 'post',
    'dateCreated': datetime.now(),
    'date_created_gmt': datetime.now(),
    'categories': [],
    'mt_keywords': ['tag1','tag2','tag3'],
    'mt_excerpt': "<p>This is the...</p>",
    'mt_text_more': "Hey-oooooO!",
    'mt_allow_comments':True,
    'mt_allow_pings': True,
    'wp_slug': 'this-is-the-test-title',
    'wp_password': 'mypassword',
    # 'wp_author_id': ''
    # 'wp_author_display_name':
    'post_status':'publish',
    'wp_post_format': 'Post',
    'sticky': False,
    'custom_fields':[],
    'enclosure':{},
}

@override_settings(
    ROOT_URLCONF='xblog.tests.conf.urls'
)
class MtTestCase(TestCase):
    """
    Test Cases for the wp.* XMLRPC API calls
    """

    def setUp(self):
        """
        Bring up the test environment
        """
        # create our test user
        self.test_user1 = User.objects.create(
            username="test_user1",
            first_name="Test",
            last_name="User2",
            email="testuser@example.com",
            password="MyTestPass1",
            is_staff=False,
            is_superuser=False
        )

        #
        self.test_user2 = User.objects.create(
            username="test_user2",
            first_name="Test",
            last_name="User2",
            email="testuser2@example.com",
            password="MyTestPass1",
            is_staff=False,
            is_superuser=False
        )
        self.rogue_user = User.objects.create(
            username="rogue_user",
            first_name="Rogue",
            last_name="User",
            email="testuser2@example.com",
            password="MyTestPass1",
            is_staff=False,
            is_superuser=False
        )
        self.test_admin = User.objects.create(
            username="admin",
            first_name="Admin",
            last_name="User",
            email="admin@example.com",
            password="MyAdminPass1",
            is_staff=True,
            is_superuser=True
        )

        self.test_blog = Blog.objects.create(
            title="Test User 1's Space",
            description="A blog for Test User 1.  Slippery when wet!",
            owner = User.objects.get(username="test_user1"),
            site = Site.objects.get_current()
        )

        self.test_category1 = Category.objects.create(
            title="Test Category 1",
            description="Category mean namely for testing",
            blog = self.test_blog
        )

        self.post = Post.objects.create(
            title = "Test User 1 Post",
            body = "This is some stuff.\n\nSome stuff, you know.",
            blog = self.test_blog,
            author = self.test_user1.author,
            status = 'publish'
        )
        self.post.save()

        self.draft = Post.objects.create(
            title = "Test User 1 Post",
            body = "This is some stuff.\n\nSome stuff, you know.",
            blog = self.test_blog,
            author = self.test_user1.author,
            status = 'draft'
        )

        # enable remote access for test_user1
        self.test_user1.author.remote_access_enabled = True
        self.test_user1.author.save()

        # disable remote access for test_user2
        self.test_user2.author.remote_access_enabled = False
        self.test_user2.author.save()

        self.rogue_user.author.remote_access_enabled = True
        self.rogue_user.author.save()

        self.test_admin.author.remote_access_enabled = True
        self.test_admin.author.save()


        self.s = ServerProxy('http://localhost:8000/xmlrpc/', transport=TestTransport(), verbose=0)

    def test_mt_set_post_categories(self):
        """
        make sure that categories can be set
        """
        postid = self.post.id
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        cat = self.test_category1
        categories = [{
            'categoryId': cat.id,
            'isPrimary': True
        },]
        res = self.s.mt.setPostCategories(postid, username, password, categories)
        # smoke check
        self.assertTrue(res)

        p = self.post

        for category in categories:
            c = Category.objects.get(pk=category['categoryId'])
            self.assertIn(c, p.categories.all())



    def test_mt_get_post_categories(self):
        postid = self.post.id
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key

        categories = self.s.mt.getPostCategories(postid, username, password)


        for category in categories:
            c = Category.objects.get(pk=categories['categoryId'])
            self.assertIn(c, p.categories.all())

    def test_mt_publish_post(self):
        postid = self.draft.id
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key

        self.assertTrue(self.draft.status=="draft")
        res = self.s.mt.publishPost(postid, username, password)
        self.assertTrue(res)
        post = Post.objects.get(pk=postid)
        self.assertTrue(post.status=='publish')
