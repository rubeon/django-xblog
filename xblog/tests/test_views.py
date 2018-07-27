"""
Test cases for XBlog blog views
"""
import logging
try:
    from django.urls import reverse
except ImportError: # django < 2
    from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.conf import settings

from django.test import TestCase
from django.test.client import Client

# from django.template.exceptions import TemplateDoesNotExist
from ..models import Post, Blog, Category

from .utils import POST_CONTENT, USER1_PARAMS, USER2_PARAMS, ROGUE_USER_PARAMS, \
    ADMIN_USER_PARAMS, TEST_BLOG_PARAMS, POST1_PARAMS, CAT1_PARAMS

LOGGER = logging.getLogger(__name__)

class BlogViewsBaseCase(TestCase):
    """
    Class for XBLog blog view test cases
    """
    def setUp(self):
        """
        Bring up the test environment
        """
        # create our test user
        self.test_user1 = get_user_model().objects.create(**USER1_PARAMS)
        self.test_user2 = get_user_model().objects.create(**USER2_PARAMS)
        self.rogue_user = get_user_model().objects.create(**ROGUE_USER_PARAMS)
        self.test_admin = get_user_model().objects.create(**ADMIN_USER_PARAMS)
        site = Site.objects.get_current()
        self.test_blog = Blog.objects.create(site=site, owner=self.test_user1,
                                             **TEST_BLOG_PARAMS)
        self.test_category1 = Category.objects.create(
            blog=self.test_blog,
            **CAT1_PARAMS
        )
        self.client = Client()
        # self.post = Post.objects.create(
        #     title="Test User 1 Post",
        #     body="This is some stuff.\n\nSome stuff, you know.",
        #     blog=self.test_blog,
        #     author=self.test_user1.author
        # )
        # self.post.save()
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

    def add_post(self, params):
        self.post = Post.objects.create(**params)
        self.post.save()

class IndexViewsTestCase(BlogViewsBaseCase):
    """
    Test all the main index views
    """
    def setUp(self):
        """
        Call super's setup, then add some content_list
        """
        super(IndexViewsTestCase, self).setUp()
        params = POST1_PARAMS.copy()
        params['blog'] = self.test_blog
        params['author'] = self.test_user1.author
        self.add_post(params)

    def test_postDetail(self):
        """
        view a single post view
        """
        LOGGER.debug("test_postDetail entered")
        self.post.status = 'publish'
        self.post.save()
        url = self.post.get_absolute_url()

        LOGGER.debug("using %s for postDetail", url)
        response = self.client.get(url)
        LOGGER.debug(response.content)

    def test_yearArchive(self):
        """
        Make sure yearArchive is showing properly
        """
        self.post.status = 'publish'
        self.post.save()

        url = self.post.get_year_archive_url()
        response = self.client.get(url)
        self.assertContains(response, self.post.title)

    def test_monthArchive(self):
        """
        Make sure monthArchive is showing properly
        """
        self.post.status = 'publish'
        self.post.save()

        # url = reverse('xblog:month-archive',
        #                kwargs={'year':self.post.pub_date.year,
        #                        'month': self.post.pub_date.strftime('%b').lower(),
        #                })
        url = self.post.get_month_archive_url()
        response = self.client.get(url)
        LOGGER.debug("XXX" + str(response))
        self.assertContains(response, self.post.title)

    def test_indexPage(self):
        """
        Views the index page, makes sure that it loaders
        """
        LOGGER.debug("XXX: test_indexPage entered")
        LOGGER.debug("XXX: %s", settings.TEMPLATES)
        self.post.status = 'publish'
        self.post.save()
        response = self.client.get('/blog/')
        self.assertContains(response, self.post.title)
        # how to debug the loading stuff
        # except TemplateDoesNotExist, e:
        #         for tmpl, msg in e.tried:
        #             LOGGER.debug("XXX Tried '%s'", tmpl.name)
