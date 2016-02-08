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
from xblog.models import Tag
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
        
    def test_getApiKey(self):
        """
        make sure he's gets an API key assigned
        """
        self.test_user1.author.remote_access_enabled = True
        self.test_user1.author.save()
        self.assertTrue(len(self.test_user1.author.remote_access_key)>1)

    # metaWeblog.getUsersBlogs    
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

    # metaWeblog.newPost
    def test_newPost_own_blog(self):
        appkey = 0
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        blog = self.test_blog
        res = self.s.metaWeblog.newPost(self.test_blog.id, username, password, post_content)
        self.assertEqual(type(1), type(int(res)))
    
    def test_newPost_nown_blog_tags(self):
        appkey = 0
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        blog = self.test_blog
        res = self.s.metaWeblog.newPost(self.test_blog.id, username, password, post_content)
        post = Post.objects.get(pk=res)
        # check for tags
        for tag in post_content['mt_keywords']:
            t = Tag.objects.get(title=tag)
            self.assertIn(t, post.tags.all() )
        
    def test_newPost_new_category(self):
        """
        when a post is created with a category that doesn't exist
        create that category
        """
        appkey = 0
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        blog = self.test_blog
        post_content['categories'] = ["Status"]
        res = self.s.metaWeblog.newPost(self.test_blog.id, username, password, post_content)
        
        # verify that the category exists
        cats = Category.objects.filter(blog=self.test_blog, title="Status")
        self.assertTrue(len(cats) > 0)
    
    # metaWeblog.getPost
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

    def test_getPost_others_blog(self):
        """
        A user should not be able to getPost on another user's blog
        """
        appkey = 0
        username = self.rogue_user.username
        password = self.rogue_user.author.remote_access_key
        
        with self.assertRaises(Fault):
            post = self.s.metaWeblog.getPost(self.post.id, username, password)
        
        
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
        post.save()
        # # now delete it...
        appkey = 0
        postid = post.id
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        publish = False
        res = self.s.metaWeblog.deletePost(appkey, postid, username, password, publish)
        with self.assertRaises(Post.DoesNotExist):
            gone_post = Post.objects.get(id=post.id)
    
    def test_deletePost_others_post(self):
        """
        deletePost should fail if not the owner or a sysadmin
        """
        post = Post.objects.create(
            title = "Test User 1 Post",
            body = "This is some stuff.\n\nSome stuff, you know.",
            blog = self.test_blog,
            author = self.test_user1.author
        )
        post.save()
        # # now try to delete it as other user
        appkey = 0
        username = self.rogue_user.username
        password = self.rogue_user.author.remote_access_key
        postid = post.id
        publish = False
        
        with self.assertRaises(Fault):
            res = self.s.metaWeblog.deletePost(appkey, postid, username, password, publish)

    def test_deletePost_others_post_admin(self):
        """
        deletePost should success if not the owner but is a sysadmin
        """
        post = Post.objects.create(
            title = "Test User 1 Post",
            body = "This is some stuff.\n\nSome stuff, you know.",
            blog = self.test_blog,
            author = self.test_user1.author
        )
        post.save()
        # # now try to delete it as other user
        appkey = 0
        username = self.test_admin.username
        password = self.test_admin.author.remote_access_key
        postid = post.id
        publish = False
        
        res = self.s.metaWeblog.deletePost(appkey, postid, username, password, publish)
        
        
        
    # metaWeblog.editPost
    def test_editPost_own(self):
        """
        Admin User should be able to edit others' posts
        """
        post = Post.objects.create(
            title = "Test User 1 Post",
            body = "This is some stuff.\n\nSome stuff, you know.",
            blog = self.test_blog,
            author = self.test_user1.author
        )
        post.save()
        # # now try to delete it as other user
        appkey = 0
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        postid = post.id
        publish = False
        new_content = post_content.copy()
        new_content['title']="This is the new title"
        res = self.s.metaWeblog.editPost(postid, username, password, new_content, publish)
        
        post = Post.objects.get(id=postid)
        
        self.assertEquals(post.title, new_content['title'])

    def test_editPost_admin(self):
        """
        Admin User should be able to edit others' posts
        """
        post = Post.objects.create(
            title = "Test User 1 Post",
            body = "This is some stuff.\n\nSome stuff, you know.",
            blog = self.test_blog,
            author = self.test_user1.author
        )
        post.save()
        # # now try to delete it as other user
        appkey = 0
        username = self.test_admin.username
        password = self.test_admin.author.remote_access_key
        postid = post.id
        publish = False
        new_content = post_content.copy()
        new_content['title']="This is the new title"
        res = self.s.metaWeblog.editPost(postid, username, password, new_content, publish)
        post = Post.objects.get(id=postid)
        self.assertEquals(post.title, new_content['title'])
        
    # metaWeblog.getCategories
    def test_getCategories_own_blog(self):
        """
        Should return a valid list of categories for this user's blog
        """
        blogid = self.test_blog.id
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        
        cats = self.s.metaWeblog.getCategories(blogid, username, password)
        
        for cat in cats:
            local_cat = Category.objects.get(id=cat['categoryId'])

            self.assertEqual(str(local_cat.id), cat['categoryId'])
            self.assertEqual(local_cat.title, cat['categoryName'])
            self.assertEqual(local_cat.description, cat['categoryDescription'])
            self.assertEqual(local_cat.description, cat['description'])
            self.assertIn(local_cat.get_absolute_url(), cat['htmlUrl'])
            # FIXME: need to update once feeds have been done...
            self.assertIn(local_cat.get_absolute_url()+"feed/", cat['rssUrl'])
            
    # metaWeblog.getRecentPosts
    def test_getRecentPosts_own_blog(self):
        # create 10 posts
        
        blogid = self.test_blog.id
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        
        
        for i in range(10):
            title = "Test Post %s" % str(i)
            body = "This is test post number %s" % i
            blog = self.test_blog
            author = self.test_user1.author
            p = Post(
                title=title,
                body=body,
                author=author,
                blog=blog
            )
            p.save()
        num_posts = 10
        posts = self.s.metaWeblog.getRecentPosts(blogid, username, password, num_posts)
        self.assertEqual(10, len(posts))
        
    def test_getRecentPosts_others_blog(self):
        """
        this should fail for mr. bad guy rogue user
        """
        blogid = self.test_blog.id
        username = self.rogue_user.username
        password = self.rogue_user.author.remote_access_key
        num_posts = 10
        posts = self.s.metaWeblog.getRecentPosts(blogid, username, password, num_posts)
        
        for post in posts:
            p = Post.objects.get(id=post['postid'])
            owner = p.author.user
            self.assertEqual(owner, self.rogue_user)
            
    def test_edit_post_mt_keywords_string(self):
        """
        ecto sends mt_keywords as a string, and not as an
        array
        
        this should be detected in the backend and fixed
        
        """
        post = Post.objects.create(
            title = "Test User 1 Post",
            body = "This is some stuff.\n\nSome stuff, you know.",
            blog = self.test_blog,
            author = self.test_user1.author
        )
        post.save()
        # # now try to delete it as other user
        appkey = 0
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        postid = post.id
        publish = False
        new_content = post_content.copy()
        keywords = "One Tag, Two Tag, Red Tag, Blue Tag"
        new_content['mt_keywords']=keywords
        print "XXX", new_content
        res = self.s.metaWeblog.editPost(postid, username, password, new_content, publish)
        self.assertTrue(res)
        
        for tag in keywords.split(","):
            t = Tag.objects.get(title__iexact=tag)
            self.assertIn(t, post.tags.all())
        
    
    # metaWeblog.getTemplate -- not WP-supported
    # metaWeblog.setTemplate -- not WP-supported
    
    # metaWeblog.newMediaObject

