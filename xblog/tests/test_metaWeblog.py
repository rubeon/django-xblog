"""
Test cases for metaWeblog access
"""

from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test.utils import override_settings
from django.conf import settings

from xblog.models import Post
from xblog.models import Blog
from xblog.models import Author
from xblog.models import Category
from xblog.models import Link
from xblog.models import Tag
from xblog.models import LinkCategory
from xblog.models import FILTERS

from .utils import TestTransport
"""Test cases for XBlog's MetaWeblog API"""


try:
    from xmlrpc.client import Binary
    from xmlrpc.client import Fault
    from xmlrpc.client import ServerProxy
except ImportError:  # Python 2
    from xmlrpclib import Binary
    from xmlrpclib import Fault
    from xmlrpclib import ServerProxy

from tempfile import TemporaryFile
from datetime import datetime

POST_CONTENT = {
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
            last_name="User1",
            email="testuser1@example.com",
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
        self.test_category2 = Category.objects.create(
            title="Test Category 2",
            description="",
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
        res = self.s.metaWeblog.newPost(self.test_blog.id, username, password, POST_CONTENT)
        self.assertEqual(type(1), type(int(res)))

    def test_newPost_nown_blog_tags(self):
        appkey = 0
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        blog = self.test_blog
        res = self.s.metaWeblog.newPost(self.test_blog.id, username, password, POST_CONTENT)
        post = Post.objects.get(pk=res)
        # check for tags
        for tag in POST_CONTENT['mt_keywords']:
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
        POST_CONTENT['categories'] = ["Status"]
        res = self.s.metaWeblog.newPost(self.test_blog.id, username, password, POST_CONTENT)

        # verify that the category exists
        cats = Category.objects.filter(blog=self.test_blog, title="Status")
        self.assertTrue(len(cats) > 0)

    def test_newPost_as_status(self):
        """
        When a post is created in the category "Status", or the category defined as
        "XBLOG_STATUS_CATEGORY_NAME" in settings.py, mark this post format as status
        """
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        blog = self.test_blog
        new_content = POST_CONTENT.copy()
        new_content['categories'].append(getattr(settings, 'XBLOG_STATUS_CATEGORY_NAME', 'Status'))
        # post = self.s.metaWeblog.getPost(res, username, password)
        res = self.s.metaWeblog.newPost(self.test_blog.id, username, password, new_content)
        new_post = Post.objects.get(pk=res)

        self.assertEqual("status", new_post.post_format)


    # metaWeblog.getPost
    def test_getPost_own_blog(self):
        appkey = 0
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        blog = self.test_blog
        res = self.s.metaWeblog.newPost(self.test_blog.id, username, password, POST_CONTENT)

        post = self.s.metaWeblog.getPost(res, username, password)

        self.assertEqual(res, post['postid'])
        for field in list(POST_CONTENT.keys()):
            if post.get(field):
                    self.assertEqual(POST_CONTENT['title'], post['title'])
                    self.assertEqual(POST_CONTENT['description'], post['description'])

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
        new_content = POST_CONTENT.copy()
        new_content['title']="This is the new title"
        res = self.s.metaWeblog.editPost(postid, username, password, new_content, publish)

        post = Post.objects.get(id=postid)

        self.assertEquals(post.title, new_content['title'])

    def test_editPost_own_publish(self):
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
        publish = True
        new_content = POST_CONTENT.copy()
        new_content['title']="This is the new title"
        res = self.s.metaWeblog.editPost(postid, username, password, new_content, publish)

        post = Post.objects.get(id=postid)

        self.assertEquals(post.title, new_content['title'])
        self.assertTrue(post.status, 'publish')

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

        new_content = POST_CONTENT.copy()
        new_content['title']="This is the new title"

        for publish in [True, False]:
            if publish:
                status='publish'
            else:
                status = 'draft'
            res = self.s.metaWeblog.editPost(postid, username, password, new_content, publish)
            post = Post.objects.get(id=postid)
            self.assertEquals(post.title, new_content['title'])
            self.assertTrue(post.status==status)

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
            # metaWeblog returns title as category description if it is empty
            if local_cat.description != '':
                self.assertEqual(local_cat.description, cat['categoryDescription'])
                self.assertEqual(local_cat.description, cat['description'])
            else:
                self.assertEqual(local_cat.title, cat['categoryDescription'])
                self.assertEqual(local_cat.title, cat['description'])
                
            self.assertIn(local_cat.get_absolute_url(), cat['htmlUrl'])
            # FIXME: need to update once feeds have been done...
            self.assertIn(local_cat.get_absolute_url()+"feed/", cat['rssUrl'])

    def test_getCategories_other_blog(self):
        """
        Should return a valid list of categories for this user's blog
        """
        blogid = self.test_blog.id
        username = self.rogue_user.username
        password = self.rogue_user.author.remote_access_key
        with self.assertRaisesRegex(Fault, 'Permission denied for'):
            cats = self.s.metaWeblog.getCategories(blogid, username, password)

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
        new_content = POST_CONTENT.copy()
        keywords = "One Tag, Two Tag, Red Tag, Blue Tag"
        new_content['mt_keywords']=keywords
        res = self.s.metaWeblog.editPost(postid, username, password, new_content, publish)
        self.assertTrue(res)

        for tag in keywords.split(","):
            t = Tag.objects.get(title__iexact=tag)
            self.assertIn(t, post.tags.all())

    def test_twitter_post_from_ifttt(self):
        """
        This peters out for some reason with IFTTT <-> Twitter
        """
        blogid = ''
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        struct =  {
            'post_status': 'publish',
            'mt_keywords': ['IFTTT', 'Twitter'],
            'description': '<blockquote class="twitter-tweet"><p lang="en" dir="ltr">The software development process<br><br>i can\u2019t fix this<br><br>*crisis of confidence*<br>*questions career*<br>*questions life*<br><br>oh it was a typo, cool</p>&mdash; I Am Devloper (@iamdevloper) <a href="https://twitter.com/iamdevloper/status/694848050796212224">February 3, 2016</a></blockquote>\n<script async src="//platform.twitter.com/widgets.js" charset="utf-8"></script>',
            'categories': ['Status'],
            'title': 'RT @iamdevloper: The software development process i can\u2019t fix this *crisis of confidence* *questions career* *questions life* oh it was a typo, cool'
        }

        res = self.s.metaWeblog.newPost(blogid, username, password, struct)

        p = Post.objects.get(pk=res)
        self.assertEqual(p.title, struct['title'])
        self.assertEqual(p.body, struct['description'])

    # metaWeblog.newMediaObject

    def test_edit_post_not_my_post(self):
        """
        Need to make sure you can't edit other people's posts!
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
        new_content = POST_CONTENT.copy()
        keywords = "One Tag, Two Tag, Red Tag, Blue Tag"
        new_content['mt_keywords']=keywords
        with self.assertRaisesRegex(Fault, 'Permission denied for'):
            res = self.s.metaWeblog.editPost(postid, username, password, new_content, publish)
        