from django.db import models
from django.template.defaultfilters import slugify
# from django.contrib.auth.models import User
from django.core.mail import mail_managers, send_mail
from django.core.exceptions import PermissionDenied
from django.core.validators import MinLengthValidator
# from django.utils.text import truncate_html_words
# replaced by the following
from django.utils.text import Truncator
from django.utils.encoding import python_2_unicode_compatible
# for setting default date
import django.utils.timezone
from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.sites.managers import CurrentSiteManager
from django.forms import ModelForm

from django.db.models.signals import post_save

from django.db.models.signals import m2m_changed
from django.dispatch import receiver

import urlparse

try:
    from django.contrib.auth import get_user_model
    User = settings.AUTH_USER_MODEL
except ImportError:
    from django.contrib.auth.models import User

def create_profile(sender, **kwargs):
    user = kwargs["instance"]
    if kwargs["created"]:
        # check if the profile already exists
        if hasattr(user, 'author'):
            return
        else:
            up = Author(user=user)
            up.save()

# weird.
post_save.connect(create_profile, sender=User)

from external import fuzzyclock
from external import text_stats

import datetime
import time
import os
import string
from django.core.urlresolvers import reverse
# from cumulus.storage import SwiftclientStorage
# openstack_storage = SwiftclientStorage()

from mimetypes import guess_type
# from external.markdown import Markdown
# from external.smartypants import smartyPants
from external.postutils import SlugifyUniquely
# # from external.BeautifulSoup import BeautifulSoup
import BeautifulSoup
import markdown2

import logging
logger = logging.getLogger(__name__)

def random_string(length=24):
    """
    generates a random string of characters for
    an API key, for example.
    """
    # create a pool of 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    pool = list(string.uppercase) + list(string.lowercase) + [str(i) for i in range(0,10)]
    # hmm... wouldn't it have been shorter to set pool to
    # ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ?
    # next time...
    res = "".join([pool[ord(c) % len(pool)] for c in os.urandom(length)])
    return res

STATUS_CHOICES=(('draft','Draft'),('publish','Published'),('private','Private'))
FORMAT_CHOICES=(('standard', 'Standard'), ('video', 'Video'), ('status','Status'),)
# text filters
FILTER_CHOICES=(
    ('markdown','Markdown'),
    ('html','HTML'),
    ('convert linebreaks','Convert linebreaks')
)

filters={}
def get_markdown(data):
    # m = Markdown(data,
    #                  extensions=['footnotes'],
    #                  # extension_configs= {'footnotes' : ('PLACE_MARKER','~~~~~~~~')},
    #                  encoding='utf8',
    #                  safe_mode = False
    #                  )
    # res = m.toString()
    # res = smartyPants(res, "1qb")
    logger.debug("get_markdown entered")
    res = markdown2.markdown(data, extras=['footnotes','fenced-code-blocks','smartypants'])
    # logger.debug("res: %s" % res)
    return res

filters['markdown']=get_markdown

def get_html(data):
    logger.debug("get_html entered")
    # just return it.
    # maybe tidy it up or something...
    # data = smartyPants(data, "1qb")
    return data

filters['html']=get_html

def convert_linebreaks(data):
    logger.debug("convert_linebreaks entered")
    data = data.replace("\n", "<br />")
    # return smartyPants(data,"1qb")
    return data

filters['convert linebreaks']=convert_linebreaks
filters['__default__']=get_markdown

def xmlify(data):
    logger.debug("xmlify entered")
    return data
    replaced=False
    for let in data:
        # fix non-unicodies.
        if ord(let) > 127:
            replaced=True
            logger.info("Replacing %s -> &%d;" % (let,ord(let) ))
            data = data.replace(let,"&#%d;" % ord(let))

    return data

@python_2_unicode_compatible
class LinkCategory(models.Model):
    """Categories for  the blogroll"""
    title = models.CharField(blank=True, max_length=255)
    description = models.TextField(blank=True)
    visible = models.BooleanField(default=True)
    blog = models.ForeignKey('Blog')
    display_order = models.IntegerField(blank=True, null=True)

    # Admin moved to admin.py
    #class Admin:
    #    list_display = ('title',)
    #    search_fields = ('title',)

    def __str__(self):
        return str(self.title)
    __repr__=__str__


@python_2_unicode_compatible
class Link(models.Model):
    """Blogroll Struct"""
    url = models.URLField(blank=True)
    link_name = models.CharField(blank=True, max_length=255)
    link_image = models.ImageField(upload_to="blog_uploads/links/", height_field='link_image_height', width_field='link_image_width',blank=True)
    link_image_height = models.IntegerField(blank=True, null=True)
    link_image_width = models.IntegerField(blank=True, null=True)

    description = models.TextField(blank=True)
    visible = models.BooleanField(default=True)
    blog = models.ForeignKey('Blog')
    rss = models.URLField(blank=True)

    category = models.ForeignKey('LinkCategory')

    def __str__(self):
        return "%s (%s)" % (self.link_name, self.url)

    __repr__=__str__

@python_2_unicode_compatible
class Pingback(models.Model):
    """ Replies are either pingbacks """

    author_name = models.CharField(blank=True, max_length=100)
    author_email = models.EmailField(blank=True)
    post = models.ForeignKey('Post')
    title = models.CharField(blank=True, max_length=255)
    body = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)

    source_url = models.URLField(blank=True)
    target_url = models.URLField(blank=True)
    pub_date = models.DateTimeField(blank=True, default=django.utils.timezone.now)
    mod_date = models.DateTimeField(blank=True, default=django.utils.timezone.now)

    def __str__(self):
        return "Reply %s -> %s" % (self.source_url,self.target_url)

    def __repr__(self):
        return "%s (%s - %s)" % (self.title, self.source_url, self.target_url)

    def save(self, *args, **kwargs):
        logger.debug("Pingback.save() entered: %s" % self)
        super(self.__class__, self).save(*args, **kwargs)
        mail_subject = "New Pingback from %s" % self.title.strip()
        mail_body = """

Source URL: %s
Target URL: %s
      Time: %s
            """ % (self.source_url, self.target_url, self.pub_date)

        logger.debug(mail_subject)
        logger.debug(mail_body)
        # mail_managers(mail_subject, mail_body, fail_silently=False)
        send_mail(mail_subject, mail_body, "eric@xoffender.de", [self.post.author.email])

class Tag(models.Model):
    """(Tag description)"""
    title = models.CharField(blank=True, max_length=100)
    def __str__(self):
        # return "%s (%s - %s)" % (self.title, self.source_url, self.target_url)
        return self.title


@python_2_unicode_compatible
class Author(models.Model):
    """User guy"""
    fullname = models.CharField(blank=True, max_length=100)
    url = models.URLField(blank=True)
    avatar = models.ImageField(blank=True, upload_to="avatars", height_field='avatar_height', width_field='avatar_width')
    # user = models.ForeignKey(User, unique=True)
    user = models.OneToOneField(User)
    about = models.TextField(blank=True)
    avatar_height = models.IntegerField(blank=True, null=True)
    avatar_width = models.IntegerField(blank=True, null=True)
    # API-related stuff
    remote_access_enabled = models.BooleanField(default=False)
    remote_access_key = models.CharField(blank=True, max_length=100, validators=[MinLengthValidator(8)])

    def get_avatar_url(self):
        logger.debug("%s: %s" % (self, "Getting avatar url"))
        return self.avatar.url

    def save(self, *args, **kwargs):
        """
        special instructions on save
        """
        if self.id:
            if self.remote_access_enabled:
                if not self.remote_access_key:
                    self.remote_access_key=random_string()

        super(self.__class__, self).save(*args, **kwargs)

    def __str__(self):
        if self.fullname == '':
            return str(self.user)
        else:
            return self.fullname

class Category(models.Model):
    """
    Keeps track of post categories
    """
    title = models.CharField(blank=False, max_length=255)
    description = models.CharField(blank=True, max_length=100)
    blog = models.ForeignKey("Blog")
    slug = models.SlugField(max_length=100)

    def __unicode__(self):
        return self.title

    def get_absolute_url(self, absolute=False):
        """
        setting absolute will prepened host's URL
        """

        local_url = urlparse.urljoin(self.blog.get_absolute_url(),self.slug)
        # dumb
        if local_url[-1]!="/":
            local_url = local_url + "/"

        if absolute:
            return "http://%s" % self.blog.site.domain + local_url
        else:
            return local_url

    def save(self, *args, **kwargs):

        if not self.slug or self.slug=='':
            self.slug = SlugifyUniquely(self.title, self.__class__)

        logger.debug("%s.Category.save entered %s" % (__name__, self.title))
        super(self.__class__, self).save(*args, **kwargs)
        logger.debug("category.save complete")



@python_2_unicode_compatible
class Post(models.Model):
    """A Blog Entry, natch"""
    # metadata
    pub_date = models.DateTimeField(blank=True, default=django.utils.timezone.now)
    update_date = models.DateTimeField(blank=True, auto_now=True)
    create_date = models.DateTimeField(blank=True, auto_now_add=True)
    enable_comments = models.BooleanField(default=True)
    # post content
    title = models.CharField(blank=False, max_length=255)
    slug = models.SlugField(max_length=100)
    # adding, because it's a good idea (mainly for importing!)
    guid = models.CharField(blank=True, max_length=255)
    body = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    categories = models.ManyToManyField(Category)
    primary_category_name = models.ForeignKey(Category, related_name='primary_category_set', blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True)
    blog = models.ForeignKey('Blog')
    # author = models.ForeignKey(User)
    author = models.ForeignKey('Author')
    status = models.CharField(blank=True, null=True, max_length=32, choices=STATUS_CHOICES, default="Draft")
    # filter to display when "get_formatted_body" is called.
    text_filter = models.CharField(blank=True, max_length=100, choices=FILTER_CHOICES, default='__default__')
    # format of this post
    post_format = models.CharField(blank=True, max_length=100, choices=FORMAT_CHOICES, default='standard')

    def __str__(self):
        return self.title

    def comment_period_open(self):
        """ determines if a post is too old..."""
        # uncomment rest of line to set limit at 30 days.
        # Sometimes I get hits on older entries, so I'll leave this one for now.
        return self.enable_comments # and datetime.datetime.today() - datetime.timedelta(30) <= self.pub_date


    def prepopulate(self):
        logger.debug("prepopulate entered for %s" % self)
        if not self.slug or self.slug=='':
            self.slug = SlugifyUniquely(self.title, self.__class__)

        if not self.summary or self.summary == '':
            # do an auto-summarize here.
            # now what could that be?
            pass
        if not self.guid or self.guid=='':
            self.guid = self.get_absolute_url()

    def handle_technorati_tags(self):
        # takes the post, and returns the technorati links in them...
        # from ecto:
        logger.debug("handle_technorati_tags entered for %s" % self)
        start_tag = "<!-- technorati tags start -->"
        end_tag = "<!-- technorati tags end -->"
        text = self.body
        start_idx = text.find(start_tag) + len(start_tag)
        end_idx = text.find(end_tag)
        if start_idx==-1 or end_idx ==-1:
            return
        logging.debug("Got target text: starts at %s" % str(start_idx))
        logging.debug("Ends at %s" % str(end_idx))
        logging.debug("Got: %s" % text[start_idx:end_idx])
        soup = BeautifulSoup(text)
        tags = []
        for a in soup.findAll('a'):
            if "http://www.technorati.com/tag/" in a.get('href'):
                # seems to be taggy
                tags.append(a.string)

        logger.debug("Tags: %s" % str(tags))
        taglist = []
        for tag in tags:
            # try to find the tag
            try:
                t = Tag.objects.get(title__iexact=tag)
                logger.info("Got Tag: '%s'" % t)
            except:
                # not found, create tag
                logger.info("Creating '%s'" % tag)
                t = Tag(title = tag)
                t.save()

            taglist.append(t)

        self.tags = taglist


    def save(self, *args, **kwargs):
        logger.debug("Post.save entered for %s" % self)
        # make sure that person is allowed to create posts in this blog
        if self.author.user != self.blog.owner and not self.author.user.is_superuser:
            # print self.author.user
            # print self.blog.owner
            raise PermissionDenied
        if not self.slug or self.slug=='':
            self.slug = SlugifyUniquely(self.title, self.__class__)

        trunc = Truncator(filters.get(self.text_filter, convert_linebreaks)(self.body)).chars(50, html=True)
        logger.debug("Post.save ---")
        logger.debug(trunc)
        self.summary = trunc
        # finally, save the whole thing
        super(self.__class__, self).save(*args, **kwargs)
        logger.debug("Post.save complete")

    def get_archive_url(self):
        # returns the path in archive
        logger.debug("get_archive_url entered for %s" % self)
        archive_url = "%s/%s" % (self.blog.get_url(), "blog/archive/")
        # archive_url = settings.SITE_URL + "blog/archive/"
        return archive_url

    def get_year_archive_url(self):
        # return self.pub_date.strftime( settings.SITE_URL + "blog/%Y/").lower()
        logger.debug("get_year_archive_url entered for %s" % self)
        kwargs = {
            "year": self.pub_date.year,
        }
        return reverse("year-archive", kwargs=kwargs)

    def get_month_archive_url(self):
        # return self.pub_date.strftime(settings.SITE_URL +"blog/%Y/%b").lower()
        logger.debug("get_month_archive_url entered for %s" % self)
        kwargs = {
            "year": self.pub_date.year,
            'month': self.pub_date.strftime("%b").lower(),
        }
        return reverse("month-archive", kwargs=kwargs)


    def get_day_archive_url(self):
        # return self.pub_date.strftime(settings.SITE_URL +"blog/%Y/%b/%d").lower()
        kwargs = {
            "year": self.pub_date.year,
            'month': self.pub_date.strftime("%b").lower(),
            'day': self.pub_date.day,

        }
        return reverse("day-archive", kwargs=kwargs)


    def get_post_archive_url(self):
        return self.get_absolute_url()

    def get_trackback_url(self):
        # returns url for trackback pings.
        # return self.get_absolute_url() + "trackback/"
        # return "".join([settings.SITE_URL,, str(self.id)]) + "/"
        # return settings.SITE_URL + self.get_absolute_url()[1:] + "trackback/"
        return urlparse.urljoin(self.get_absolute_uri(), "trackback/")

    def get_absolute_uri(self):
        # returns a url for the interweb
        uri = urlparse.urljoin(self.blog.get_url(), self.get_absolute_url())
        return self.get_absolute_url()

    # will standardize on this in the future
    get_url = get_absolute_uri

    def get_absolute_url(self):
        logger.debug("get_absolute_url entered for %s" % self)
        logger.debug("post_format: %s" % self.post_format)
        kwargs = {
            'slug': self.slug,
            'year': self.pub_date.year,
            'month': self.pub_date.strftime("%b").lower(),
            'day': self.pub_date.day,
        }
        return reverse("xblog:post-detail", kwargs=kwargs)

    def get_site_url(self):
        """
        this is the site_url
        FIXME: don't think this is ever used...
        """
        datestr = self.pub_date.strftime("%Y/%b/%d")
        return "/".join(['/blog', datestr.lower(), self.slug]) + "/"


    def get_full_body(self):
        """ same as get_formatted_body, but removes <-- more --> tags."""
        b = self.body.replace('<!--more-->','')
        textproc = filters.get(self.text_filter, convert_linebreaks)
        b = textproc(b)
        return b

    # newness
    # what's this?
    get_full_body.allow_tags = True

    @property
    def full_body(self):
        return self.get_full_body()

    def get_formatted_body(self, split=True):
        """ returns the formatted version of the body text"""
        logger.debug("get_formatted_body entered for %s" % self)
        # check for 'more' tag
        if split and self.body.find('<!--more-->') > -1:
            # this is split.
            b = self.body.split('<!--more-->')[0]
            splitted = True
        else:
            b = self.body
            splitted = False

        textproc = filters.get(self.text_filter, convert_linebreaks)
        b = textproc(b)
        if splitted:
            b += """<p><a href="%s">Continue reading "%s"</p>""" % (self.get_absolute_url(), self.title)
        return b

    def get_video_body(self):
        """
        if this is a video post, reformat it to embed the video instead of showing the URL
        """
        # parse a video URL... slowly at first, but then badly
        logger.debug("get_video_body entered: %s" % self)
        video_url = self.body.split("\n")[0]
        if video_url.startswith("http"):
            logger.debug("video_url: %s" % video_url)
            if video_url.find("vimeo.com") > -1:
                logger.debug("Got vimeo link")
                # naive ID finder...
                video_id = video_url.split("/")[-1]
                video_link ="""<iframe src="//player.vimeo.com/video/%s" width="WIDTH" height="HEIGHT" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>""" % video_id
                return video_link
            else:
                return "<b>Unsupported Video...</b>"


    # newness?
    get_formatted_body.allow_tags = True

    def get_fuzzy_pub_date(self):
        logger.debug("get_fuzzy_pub_date entered for %s" % self)
        h = self.pub_date.hour
        m = self.pub_date.minute
        fc = fuzzyclock.FuzzyClock()
        fc.setHour(h)
        fc.setMinute(m)
        res =  string.capwords(fc.getFuzzyTime())
        return res

    def get_pingback_count(self):
        logger.debug("get_pingback_count entered for %s" % self)
        return len(self.pingback_set.all())

    def get_readability(self):
        logger.debug("get_readability entered for %s" % self)
        my_readability = text_stats.calculate_readability(self)
        return my_readability

class Blog(models.Model):
    """ For different blogs..."""
    title = models.CharField(blank=True, max_length=100)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User)
    site = models.ForeignKey(Site)
    slug = models.SlugField(max_length=100)

    objects = models.Manager()
    on_site = CurrentSiteManager()

    def __str__(self):
        return self.title

    def get_url(self):
        # return "".join([settings.SITE_URL,"blog","/", str(self.id)]) + "/"
        # return reverse("archive-index")
        # return "http://127.0.0.1:8000/blog/"
        return "http://%s/" % self.site.domain

    def get_absolute_url(self):
        return reverse('xblog:blog-detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        logger.debug("%s.Blog.save entered %s" % (__name__, self.title))
        if not self.slug or self.slug=='':
            slug = SlugifyUniquely(self.title, self.__class__)
            logger.debug("Slug not given, setting to %s" % slug)
            self.slug = slug

        super(self.__class__, self).save(*args, **kwargs)
        logger.debug("blog.save complete")


class PostForm(ModelForm):
    """
    Django form-based class for editing posts.
    """
    class Meta:
        model = Post
        # fields = ["pub_date", "title",  "enable_comments", "body", "text_filter", "blog", "author"]
        # exclude = ['update_date', 'create_date', 'slug', ]
        readonly_fields = ('create_date',)
        fields = ['title', 'body', 'author', 'status', 'tags', 'text_filter', 'blog',  'guid']

@receiver(m2m_changed, sender=Post.categories.through)
def check_status_category(sender, **kwargs):
    """
    Checks to see if this is a status-style post, and changes the post type
    accordingly
    """
    logger.debug('XXcheck_status_category entered')
    logger.debug(sender)
    instance = kwargs.pop('instance', None)
    action = kwargs.pop('action', None)
    pk_set = kwargs.pop('pk_set', None)
    logger.debug('XXpk_set:' + str(pk_set))
    status_category = getattr(settings, "XBLOG_STATUS_CATEGORY_NAME", "Status")
    # try to get the status category...
    try:
        status_cat = Category.objects.get(title=status_category)
        logger.debug(status_category +" XXX FOUND")
    except Category.DoesNotExist:
        logger.debug(status_category +" XX NOT FOUND")
        return
    logger.debug('XXXcheck_status_category:' + status_cat.title)
    # first save, so we can check the categories
    logger.debug('XXXnotq id:' + str(status_cat.id))
    logger.debug('XXXnotq pk_set:' + str(pk_set))
    logger.debug('XXXnotq action: ' + str(action))
    if action == "post_add":
        if status_cat.id in pk_set:
            logger.debug('XXXcat:' + status_cat.title)
            instance.post_format = "status"
            # logger.info("XX:%s|%s setting format to 'status'" % (instance.id, instance.title))
            # sender.save()
            instance.save()
        else:
            pass
