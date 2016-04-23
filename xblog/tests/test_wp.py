"""
Test Cases for the WordPress XML RPC API
"""
# pylint: disable=invalid-name
# pylint: disable=too-many-instance-attributes

try:
    from xmlrpc.client import Fault
    from xmlrpc.client import ServerProxy
except ImportError:  # Python 2
    from xmlrpclib import Fault
    from xmlrpclib import ServerProxy


from datetime import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

from xblog.models import Post
from xblog.models import Blog
from xblog.models import Category


from .utils import TestTransport, POST_CONTENT

class WpTestCase(TestCase):
    """
    Test Cases for the wp.* XMLRPC API calls

    # Eight is reasonable in this case.

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
            owner=User.objects.get(username="test_user1"),
            site=Site.objects.get_current()
        )

        self.test_category1 = Category.objects.create(
            title="Test Category 1",
            description="Category mean namely for testing",
            blog=self.test_blog
        )

        self.post = Post.objects.create(
            title="Test User 1 Post",
            body="This is some stuff.\n\nSome stuff, you know.",
            blog=self.test_blog,
            author=self.test_user1.author
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


        self.server_proxy = ServerProxy('http://localhost:8000/xmlrpc/',
                                        transport=TestTransport(),
                                        verbose=0)

    # Posts
    # wp.getPost
    def test_getPost_own(self):
        """
        Test that a user can get his own post
        """
        blog_id = self.test_blog.id
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        post_id = self.post.id
        self.server_proxy.wp.getPost(blog_id, username, password, post_id)

    def test_getPost_others(self):
        """
        Test that a user cannot get other's own post
        """
        blog_id = self.test_blog.id
        username = self.rogue_user.username
        password = self.rogue_user.author.remote_access_key
        post_id = self.post.id
        with self.assertRaises(Fault):
            self.server_proxy.wp.getPost(blog_id, username, password, post_id)

    # wp.getPosts
    def test_getPosts_own_blog(self):
        """
        Test that getPosts works on own posts, own blog
        pylint: disable=invalid-name
        """
        blog_id = self.test_blog.id
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key
        empty_filter = {}

        res = self.server_proxy.wp.getPosts(blog_id, username, password, empty_filter)
        # make sure it's the correct set
        for post in res:
            local_post = Post.objects.get(id=post['post_id'])
            self.assertEqual(self.test_user1, local_post.author.user)
            self.assertEqual(self.test_user1, local_post.blog.owner)

    def test_wp_getPosts_others_blog(self):
        """
        Test that a user cannot get posts from others' blogs
        pylint: disable=invalid-name
        """
        blog_id = self.test_blog.id
        username = self.rogue_user.username
        password = self.rogue_user.author.remote_access_key
        empty_filter = {}

        with self.assertRaises(Fault):
            self.server_proxy.wp.getPosts(blog_id, username, password, empty_filter)

    # wp.newPost
    def test_wp_newPost_own_blog(self):
        """
        Full-feature blog post
        pylint: disable=invalid-name
        """
        blog_id = self.test_blog.id
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key

        new_content = POST_CONTENT.copy()

        new_content['author_id'] = self.test_user1.id

        res = self.server_proxy.wp.newPost(blog_id, username, password, POST_CONTENT)

        # make sure it got made

        new_post = Post.objects.get(id=res)

        self.assertEqual(str(blog_id), str(new_post.blog.id))
        self.assertEqual(new_post.author.user, self.test_user1)


    def test_wp_new_category_own_blog(self):
        """
        creates a new category, makes sure it takes
        pylint: disable=invalid-name
        """
        blog_id = self.test_blog.id
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key

        new_cat = {
            'name': 'New Category',
            'parent_id': 0,
            'description': 'A great category for stuff!'
        }

        res = self.server_proxy.wp.newCategory(blog_id, username, password, new_cat)

        # get the created Category

        cat = Category.objects.get(pk=res)
        blog = Blog.objects.get(pk=blog_id)
        self.assertEqual(cat.title, new_cat['name'])
        self.assertEqual(cat.description, new_cat['description'])
        self.assertEqual(cat.blog, blog)

    def test_wp_get_options_own_blog(self):
        """
        get options for own blog
        """
        blog_id = self.test_blog.id
        username = self.test_user1.username
        password = self.test_user1.author.remote_access_key

        struct = {}

        self.server_proxy.wp.getOptions(blog_id, username, password, struct)

    # wp.editPost
    # wp.deletePost
    # wp.getPostType
    # wp.getPostTypes
    # wp.getPostFormats
    # wp.getPostStatusList


    # Taxonomies (for categories, tags, and custom taxonomies) - Added in WordPress 3.4
    # wp.getTaxonomy
    # def test_wp_getTaxonomy_own_blog(self):
    #     blog_id = self.test_blog.id
    #     username = self.test_user1.username
    #     password = self.test_user1.author.remote_access_key
    #     for taxonomy in ['category', 'link_category','post_format', 'post_tag']:
    #         res = self.server_proxy.wp.getTaxonomy(blog_id, username, password, taxonomy)
    #
    # # wp.getTaxonomies
    # def test_wp_getTaxonomies(self):
    #     blog_id = self.test_blog.id
    #     username = self.test_user1.username
    #     password = self.test_user1.author.remote_access_key
    #     res = self.server_proxy.wp.getTaxonomies(blog_id, username, password)
    #

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
