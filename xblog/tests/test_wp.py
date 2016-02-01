from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType
from django.test.utils import override_settings
from django.test.client import Client
from django.conf import settings

from xblog.models import Post
from xblog.models import Blog
from xblog.models import Author
from xblog.models import Category
from xblog.models import Link
from xblog.models import LinkCategory
from xblog.models import Tag
from xblog.models import filters



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

# Posts (for posts, pages, and custom post types) - Added in WordPress 3.4
# wp.getPost

content = {
    'post_type' : 'post',
    'post_status' : 'publish',
    'post_title' : 'A Normal Post',
    'post_author' : '',
    'post_excerpt' : '',
    'post_content' : u"<p>This is some post content.  Sweet",
    'post_date_gmt' : datetime.now(),
    'post_format' : 'standard',
    'post_name' : '',
    'post_password' : '',
    'comment_status' : 'open',
    'ping_status' : 'open',
    'sticky' : False,
    'post_thumbnail' : [],
    'post_parent' :  0,
    'terms' : {
        'mytags': [ContentType.objects.get_for_model(Tag)]
    },
    'terms_names':{
        'mytags':["MyTagNumber1", "MyTagNumber2"],
    },
    'enclosure': {
        'url' : '',
        'length' : '',
        'type' : '',
    }
}

class WpTestCase(TestCase):
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
            author = self.test_user1.author
        )
        self.post.save()
    
    
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

    # Posts
    # wp.getPost
    def test_wp_getPost_own_post(self):
        blog_id = self.test_blog.id
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        post_id = self.post.id
        res = self.s.wp.getPost(blog_id, username, password, post_id)
    
    def test_wp_getPost_others_post(self):
        blog_id = self.test_blog.id
        username = self.rogue_user.username
        password = self.rogue_user.author.remote_access_key
        post_id = self.post.id
        with self.assertRaises(Fault):
            res = self.s.wp.getPost(blog_id, username, password, post_id)

    # wp.getPosts
    def test_wp_getPosts_own_posts_own_blog(self):
        blog_id = self.test_blog.id
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        filter = {}
        
        res = self.s.wp.getPosts(blog_id, username, password, filter)
        # make sure it's the correct set
        for post in res:
            local_post = Post.objects.get(id=post['post_id'])
            self.assertEqual(self.test_user1, local_post.author.user)
            self.assertEqual(self.test_user1, local_post.blog.owner)

    def test_wp_getPosts_others_blog(self):
        blog_id = self.test_blog.id
        username = self.rogue_user.username
        password = self.rogue_user.author.remote_access_key
        filter = {}
        
        with self.assertRaises(Fault):
            res = self.s.wp.getPosts(blog_id, username, password, filter)
            print res
        
    # wp.newPost
    def test_wp_newPost_own_blog(self):
        """
        Full-feature blog post
        """
        blog_id = self.test_blog.id
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        
        new_content = content.copy()
        
        new_content['author_id'] = self.test_user1.id
        
        res = self.s.wp.newPost(blog_id, username, password, content)
        
        # make sure it got made
        
        new_post = Post.objects.get(id=res)
        
        assertEqual(str(blog_id), str(new_post.blog.id))
        assertEqual(new_post.author.user, self.test_user1)
        
    # wp.editPost
    # wp.deletePost
    # wp.getPostType
    # wp.getPostTypes
    # wp.getPostFormats
    # wp.getPostStatusList
    
    
    # Taxonomies (for categories, tags, and custom taxonomies) - Added in WordPress 3.4
    # wp.getTaxonomy
    def test_wp_getTaxonomy_own_blog(self):
        blog_id = self.test_blog.id
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        for taxonomy in ['category', 'link_category','post_format', 'post_tag']:
            res = self.s.wp.getTaxonomy(blog_id, username, password, taxonomy)
    
    # wp.getTaxonomies
    def test_wp_getTaxonomies(self):
        blog_id = self.test_blog.id
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        res = self.s.wp.getTaxonomies(blog_id, username, password)
        
    
    # wp.getTerm
    # wp.getTerms
    # wp.newTerm
    # wp.editTerm

    # Media
    # wp.deleteTermMedia - Added in WordPress 3.1
    # wp.getMediaItem
    # wp.getMediaLibrary
    # wp.uploadFile

    # Comments - Added in WordPress 2.7
    # wp.getCommentCount
    # wp.getComment
    # wp.getComments
    # wp.newComment
    # wp.editComment
    # wp.deleteComment
    # wp.getCommentStatusList
    # Options - Added in WordPress 2.6
    # wp.getOptions
    # wp.setOptions

    # Users
    # wp.getUsersBlogs
    # wp.getUser (3.5)
    # wp.getUsers (3.5)
    # wp.getProfile (3.5)
    # wp.editProfile (3.5)
    # wp.getAuthors

