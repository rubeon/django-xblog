"""

Test cases for metaWeblog access

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
from xblog.models import LinkCategory
from xblog.models import filters

"""Test cases for XBlog's MetaWeblog API"""

import six

try:
    from xmlrpc.client import Binary
    from xmlrpc.client import Fault
    from xmlrpc.client import ServerProxy
except ImportError:  # Python 2
    from xmlrpclib import Binary
    from xmlrpclib import Fault
    from xmlrpclib import ServerProxy
from tempfile import TemporaryFile


try:
    from urllib.parse import parse_qs
    from urllib.parse import urlparse
    from xmlrpc.client import Transport
except ImportError:  # Python 2
    from urlparse import parse_qs
    from urlparse import urlparse
    from xmlrpclib import Transport
from datetime import datetime 


class TestTransport(Transport):
    """
    Handles connections to XML-RPC server through Django test client.
    """

    def __init__(self, *args, **kwargs):
        Transport.__init__(self, *args, **kwargs)
        self.client = Client()

    def request(self, host, handler, request_body, verbose=0):
        self.verbose = verbose
        response = self.client.post(handler,
                                    request_body,
                                    content_type="text/xml")
        res = six.BytesIO(response.content)
        setattr(res, 'getheader', lambda *args: '')  # For Python >= 2.7
        res.seek(0)
        return self.parse_response(res)

# create User, enable API access, make sure an API key is created

# create User, enable API access, make sure can  API key is created

# functions in metaWeblog API (not wp,mt, or blogger)





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
class MetaWeblogTestCase(TestCase):
    """
    MetaWeblog API tests
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
        
        # enable remote access for test_user1
        self.test_user1.author.remote_access_enabled = True
        self.test_user1.author.save()
        
        # disable remote access for test_user2
        self.test_user2.author.remote_access_enabled = False
        self.test_user2.author.save()
        
        
        self.s = ServerProxy('http://localhost:8000/xmlrpc/', transport=TestTransport(), verbose=1)
        
    def test_getApiKey(self):
        """
        make sure he's gets an API key assigned
        """
        self.test_user1.author.remote_access_enabled = True
        self.test_user1.author.save()
        self.assertTrue(len(self.test_user1.author.remote_access_key)>1)
    
    def test_getUsersBlogs_correct_blogs(self):
        """
        see if the blogs are properly returned
        """
        appkey = 0
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        
        res = self.s.metaWeblog.getUsersBlogs(appkey, username, password)
        
        for blog in res:
            b = Blog.objects.get(id=blog['blogid'])
            self.assertEqual(self.test_user1, b.owner)
    
    def test_newPost_own_blog(self):
        # metaWeblog.newPost
        appkey = 0
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        blog = self.test_blog
        res = self.s.metaWeblog.newPost(self.test_blog.id, username, password, post_content)
        self.assertEqual(type(1), type(int(res)))
    
    def test_getPost_own_blog(self):
        appkey = 0
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        blog = self.test_blog
        res = self.s.metaWeblog.newPost(self.test_blog.id, username, password, post_content)
        
        post = self.s.metaWeblog.getPost(res, username, password)
        
        self.assertEqual(res, post['postid'])
        for field in post_content.keys():
            if post.get(field):
                    self.assertEqual(post_content['title'], post['title'])
                    self.assertEqual(post_content['description'], post['description'])

    # metaWeblog.deletePost
    def test_deletePost_own_post(self):
        """
        post owner should be able to delete it.
        """
        # create the post...
        post = Post.objects.create(
            title = "Test User 1 Post",
            body = "This is some stuff.\n\nSome stuff, you know.",
            blog = self.test_blog,
            author = self.test_user1.author
        )

        # now delete it...
        appkey = 0
        postid = post.id
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        publish = False
        res = self.s.metaWeblog.deletePost(appkey, postid, username, password, publish)
        
        gone_post = Post.objects.get(id=post.id)
        
    # metaWeblog.editPost

    # metaWeblog.getCategories
    # metaWeblog.getPost
    # metaWeblog.getRecentPosts
    # metaWeblog.getTemplate
    # metaWeblog.getUsersBlogs
    # metaWeblog.newMediaObject
    # metaWeblog.newPost
    # metaWeblog.setTemplate
