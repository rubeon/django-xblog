"""
Models and functions for tracking XBlog Objects:
- Post
- Author
- Blog
- Category
- Tag

"""
import logging
import os
import string
import bs4
import markdown2
import django.utils.timezone
import random

try:
    from urllib.parse import urlparse, urljoin
except ImportError:
     from urlparse import urlparse, urljoin
from django.db import models
# from django.core.mail import send_mail
from django.core.exceptions import PermissionDenied
from django.core.validators import MinLengthValidator
from django.utils.text import Truncator
from django.utils.html import linebreaks
from django.utils.encoding import python_2_unicode_compatible
from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.sites.managers import CurrentSiteManager
from django.forms import ModelForm
from django.db.models.signals import post_save
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
# from django.contrib.auth import get_user_model
try:
    from django.urls import reverse
except ImportError: # django < 2
    from django.core.urlresolvers import reverse
from .external.postutils import SlugifyUniquely
from .external import fuzzyclock
from .external import text_stats


LOGGER = logging.getLogger(__name__)

def create_profile(*args, **kwargs):
    """
    Creates a user profile for new users
    assigns an author instance
    """
    LOGGER.debug('%s.create_profile entered', __name__)
    LOGGER.debug('args: %s', str(args))
    user = kwargs["instance"]
    # if kwargs["created"]:
    #     # check if the profile already exists
    if hasattr(user, 'author'):
        LOGGER.info('Author profile exists, skipping')
        return
    else:
        userprofile = Author(user=user)
        userprofile.save()

post_save.connect(create_profile, sender=settings.AUTH_USER_MODEL)

def random_string(length=24):
    """
    generates a random string of characters for
    an API key, for example.
    """
    # create a pool of 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    pool = list(string.ascii_uppercase) + list(string.ascii_lowercase) + [str(i) for i in range(0, 10)]
    # hmm... wouldn't it have been shorter to set pool to
    # ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 ?
    # next time...
    # res = "".join([pool[ord(c[0])) % len(pool)] for c in os.urandom(length)])
    res = ''.join(random.choice(pool) for _ in range(length))
    return res

STATUS_CHOICES = (('draft', 'Draft'), ('publish', 'Published'), ('private', 'Private'))
FORMAT_CHOICES = (('standard', 'Standard'), ('video', 'Video'), ('status', 'Status'),)
# text FILTERS
FILTER_CHOICES = (
    ('markdown', 'Markdown'),
    ('html', 'HTML'),
    ('convert linebreaks', 'Convert linebreaks')
)

FILTERS = {}
def get_markdown(data):
    """
    # m = Markdown(data,
    #                  extensions=['footnotes'],
    #                  # extension_configs= {'footnotes' : ('PLACE_MARKER','~~~~~~~~')},
    #                  encoding='utf8',
    #                  safe_mode = False
    #                  )
    # res = m.toString()
    # res = smartyPants(res, "1qb")
    """
    LOGGER.debug("%s.get_markdown entered", __name__)
    res = markdown2.markdown(data, extras=['footnotes', 'fenced-code-blocks', 'smartypants'])
    # LOGGER.debug("res: %s" % res)
    return res

FILTERS['markdown'] = get_markdown

def get_html(data):
    """
    used when the post is written in standard HTML
    might be a good place to clean up / validate HTML to
    keep it from breaking the site..?
    """
    LOGGER.debug("%s.get_html entered", __name__)
    # just return it.
    # maybe tidy it up or something...
    # data = smartyPants(data, "1qb")
    return data

FILTERS['html'] = get_html

def convert_linebreaks(data):
    """
    The most basic filter, just translates linebreaks to
    <br>'s.  This is pants.
    """
    LOGGER.debug("%s.convert_linebreaks entered", __name__)
    data = linebreaks(data)
    # return smartyPants(data,"1qb")
    return data

FILTERS['convert linebreaks'] = convert_linebreaks
FILTERS['__default__'] = get_markdown

@python_2_unicode_compatible
class LinkCategory(models.Model):
    """Categories for  the blogroll"""
    title = models.CharField(blank=True, max_length=255)
    description = models.TextField(blank=True)
    visible = models.BooleanField(default=True)
    blog = models.ForeignKey('Blog', on_delete=models.CASCADE)
    display_order = models.IntegerField(blank=True, null=True)

    def __str__(self):
        if self.title != '':
            return str(self.title)
        else:
            return str('Untitled Link Category %d' % self.id)
    
    __repr__ = __str__


@python_2_unicode_compatible
class Link(models.Model):
    """Blogroll Struct"""
    url = models.URLField(blank=True)
    link_name = models.CharField(blank=True, max_length=255)
    link_image = models.ImageField(upload_to="blog_uploads/links/",
                                   height_field='link_image_height',
                                   width_field='link_image_width',
                                   blank=True)
    link_image_height = models.IntegerField(blank=True, null=True)
    link_image_width = models.IntegerField(blank=True, null=True)

    description = models.TextField(blank=True)
    visible = models.BooleanField(default=True)
    blog = models.ForeignKey('Blog', on_delete=models.CASCADE)
    rss = models.URLField(blank=True)

    category = models.ForeignKey('LinkCategory', on_delete=models.CASCADE)

    def __str__(self):
        return "%s (%s)" % (self.link_name, self.url)

    __repr__ = __str__

@python_2_unicode_compatible
class Pingback(models.Model):
    """ Replies are either pingbacks """

    author_name = models.CharField(blank=True, max_length=100)
    author_email = models.EmailField(blank=True)
    post = models.ForeignKey('Post', on_delete=models.CASCADE)
    title = models.CharField(blank=True, max_length=255)
    body = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)

    source_url = models.URLField(blank=True)
    target_url = models.URLField(blank=True)
    pub_date = models.DateTimeField(blank=True, default=django.utils.timezone.now)
    mod_date = models.DateTimeField(blank=True, default=django.utils.timezone.now)

    def __str__(self):
        return "Reply %s -> %s" % (self.source_url, self.target_url)

    __unicode__ = __str__

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        """
        save override.
        """
        LOGGER.debug("Pingback.save() entered: %s", str(self))
        super(Pingback, self).save(force_insert=force_insert,
                                   force_update=force_update, using=using,
                                   update_fields=update_fields
                                  )
        mail_subject = "New Pingback from %s" % self.title
        mail_body = """
Source URL: %s
Target URL: %s
      Time: %s
            """ % (self.source_url, self.target_url, self.pub_date)

        LOGGER.debug('mail_subject: %s', mail_subject)
        LOGGER.debug('mail_body: %s', mail_body)
        # mail_managers(mail_subject, mail_body, fail_silently=False)
        # send_mail(mail_subject, mail_body, "eric@xoffender.de", [self.post.author.email])

class Tag(models.Model):
    """(Tag description)"""
    title = models.CharField(blank=True, max_length=100)
    def __str__(self):
        # return "%s (%s - %s)" % (self.title, self.source_url, self.target_url)
        return self.title
    __unicode__ = __str__

@python_2_unicode_compatible
class Author(models.Model):
    """User guy"""
    fullname = models.CharField(blank=True, max_length=100)
    url = models.URLField(blank=True)
    avatar = models.ImageField(blank=True,
                               upload_to="avatars",
                               height_field='avatar_height',
                               width_field='avatar_width')
    # user = models.ForeignKey(User, unique=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    about = models.TextField(blank=True)
    avatar_height = models.IntegerField(blank=True, null=True)
    avatar_width = models.IntegerField(blank=True, null=True)
    # API-related stuff
    remote_access_enabled = models.BooleanField(default=False)
    remote_access_key = models.CharField(blank=True,
                                         max_length=100,
                                         validators=[MinLengthValidator(8)])

    def get_avatar_url(self):
        """
        returns the avatar URL for this user
        """
        LOGGER.debug("%s: %s", str(self), "Getting avatar url")
        return self.avatar.url

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        """
        special instructions on save
        """
        if self.id:
            if self.remote_access_enabled:
                if not self.remote_access_key:
                    self.remote_access_key = random_string()

        super(Author, self).save(force_insert=force_insert,
                                 force_update=force_update,
                                 using=using,
                                 update_fields=update_fields
                                )

    def __str__(self):
        if self.fullname == '':
            return str(self.user)
        return self.fullname
    def get_fullname(self):
        """
        get_fullname will return something, even if fullname isn't set
        """
        return str(self)

class Category(models.Model):
    """
    Keeps track of post categories
    """
    title = models.CharField(blank=False, max_length=255)
    description = models.CharField(blank=True, max_length=100)
    blog = models.ForeignKey('Blog', on_delete=models.CASCADE)
    slug = models.SlugField(max_length=100)

    def __unicode__(self):
        return self.title

    def get_absolute_url(self, absolute=False):
        """
        setting absolute will prepened host's URL
        """
        local_url = urljoin(self.blog.get_absolute_url(), self.slug)
        # dumb
        if local_url[-1] != "/":
            local_url = local_url + "/"

        if absolute:
            return "http://%s" % self.blog.site.domain + local_url
        return local_url

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        """
        Override save for Category
        """
        if not self.slug or self.slug == '':
            self.slug = SlugifyUniquely(self.title, self.__class__)

        LOGGER.debug("%s.Category.save entered %s", __name__, self.title)
        super(Category, self).save(force_insert=force_insert,
                                   force_update=force_update,
                                   using=using,
                                   update_fields=update_fields
                                  )
        LOGGER.debug("category.save complete")
        
    def __str__(self):
        if self.title != '':
            return str(self.title)
        else:
            return super(Category, self).__str__()
        

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
    primary_category_name = models.ForeignKey(Category,
                                              related_name='primary_category_set',
                                              blank=True,
                                              on_delete=models.CASCADE,
                                              null=True)
    tags = models.ManyToManyField(Tag, blank=True)
    blog = models.ForeignKey('Blog', on_delete=models.CASCADE)
    # author = models.ForeignKey(User)
    author = models.ForeignKey('Author', on_delete=models.CASCADE)
    status = models.CharField(blank=True,
                              null=True,
                              max_length=32,
                              choices=STATUS_CHOICES,
                              default="Draft")
    # filter to display when "get_formatted_body" is called.
    text_filter = models.CharField(blank=True,
                                   max_length=100,
                                   choices=FILTER_CHOICES,
                                   default='__default__')
    # format of this post
    post_format = models.CharField(blank=True,
                                   max_length=100,
                                   choices=FORMAT_CHOICES,
                                   default='standard')

    def __str__(self):
        return self.title

    def comment_period_open(self):
        """ determines if a post is too old..."""
        # uncomment rest of line to set limit at 30 days.
        # Sometimes I get hits on older entries, so I'll leave this one for now.
        # consider adding:
        # # and datetime.datetime.today() - datetime.timedelta(30) <= self.pub_date
        return self.enable_comments

    def prepopulate(self):
        """
        sets up slug, etc.
        """
        LOGGER.debug("prepopulate entered for %s", str(self))
        if not self.slug or self.slug == '':
            self.slug = SlugifyUniquely(self.title, self.__class__)

        if not self.summary or self.summary == '':
            # do an auto-summarize here.
            # now what could that be?
            pass
        if not self.guid or self.guid == '':
            self.guid = self.get_absolute_url()

    def handle_technorati_tags(self):
        """
        takes the post, and returns the technorati links in them...
        from ecto:
        """
        LOGGER.debug("handle_technorati_tags entered for %s", str(self))
        start_tag = "<!-- technorati tags start -->"
        end_tag = "<!-- technorati tags end -->"
        text = self.body
        start_idx = text.find(start_tag) + len(start_tag)
        end_idx = text.find(end_tag)
        if start_idx == -1 or end_idx == -1:
            return
        logging.debug("Got target text: starts at %s", str(start_idx))
        logging.debug("Ends at %s", str(end_idx))
        logging.debug("Got: %s", text[start_idx:end_idx])
        soup = bs4.BeautifulSoup(text, 'html.parser')
        tags = []
        for anchor in soup.findAll('a'):
            if "http://www.technorati.com/tag/" in anchor.get('href'):
                # seems to be taggy
                tags.append(anchor.string)

        LOGGER.debug("Tags: %s", str(tags))
        taglist = []
        for tag in tags:
            # try to find the tag
            try:
                taginstance = Tag.objects.get(title__iexact=tag)
                LOGGER.info("Got Tag: '%s'", taginstance)
            except Tag.DoesNotExist:
                # not found, create tag
                LOGGER.info("Creating '%s'", tag)
                taginstance = Tag(title=tag)
                taginstance.save()

            taglist.append(taginstance)
        self.tags = taglist


    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        """
        save override for Post model
        """
        LOGGER.debug("Post.save entered for %s", str(self))
        # make sure that person is allowed to create posts in this blog
        if self.author.user != self.blog.owner and not self.author.user.is_superuser:
            # print self.author.user
            # print self.blog.owner
            raise PermissionDenied
        if not self.slug or self.slug == '':
            self.slug = SlugifyUniquely(self.title, self.__class__)

        trunc = Truncator(FILTERS.get(self.text_filter,
                                      convert_linebreaks)(self.body)).chars(50, html=True)
        self.summary = trunc
        # finally, save the whole thing
        super(Post, self).save(force_insert=force_insert,
                               force_update=force_update,
                               using=using,
                               update_fields=update_fields
                              )
        LOGGER.debug("Post.save complete")

    def get_archive_url(self):
        """
        gets the URL of the main archive.
        """
        LOGGER.debug("get_archive_url entered for %s", str(self))
        archive_url = "%s/%s" % (self.blog.get_url(), "blog/archive/")
        # archive_url = settings.SITE_URL + "blog/archive/"
        return archive_url

    def get_year_archive_url(self):
        """
        gets the URL of the year archive.
        """
        LOGGER.debug("get_year_archive_url entered for %s", str(self))
        kwargs = {
            "year": self.pub_date.year,
        }
        return reverse("xblog:year-archive", kwargs=kwargs)

    def get_month_archive_url(self):
        """
        gets the URL of the month archive.
        """
        LOGGER.debug("get_month_archive_url entered for %s", str(self))
        kwargs = {
            "year": self.pub_date.year,
            'month': self.pub_date.strftime("%b").lower(),
        }
        return reverse("xblog:month-archive", kwargs=kwargs)


    def get_day_archive_url(self):
        """
        gets the URL of the day archive.
        """
        kwargs = {
            "year": self.pub_date.year,
            'month': self.pub_date.strftime("%b").lower(),
            'day': self.pub_date.day,

        }
        return reverse("xblog:day-archive", kwargs=kwargs)


    def get_post_archive_url(self):
        """
        get the URL of the archive for all posts
        """
        return self.get_absolute_url()

    def get_trackback_url(self):
        """
        returns url for trackback pings.
        """
        return urljoin(self.get_absolute_uri(), "trackback/")

    def get_absolute_uri(self):
        """
        returns a url for the public interweb
        """
        # uri = urllib.parse.urljoin(self.blog.get_url(), self.get_absolute_url())
        return self.get_absolute_url()

    # will standardize on this in the future
    get_url = get_absolute_uri

    def get_absolute_url(self):
        """
        Calculates the Post's full URL
        """
        LOGGER.debug("get_absolute_url entered for %s", str(self))
        LOGGER.debug("post_format: %s", self.post_format)
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
        bodytext = self.body.replace('<!--more-->', '')
        textproc = FILTERS.get(self.text_filter, convert_linebreaks)
        bodytext = textproc(bodytext)
        return bodytext

    # newness
    # what's this?
    get_full_body.allow_tags = True

    @property
    def full_body(self):
        """
        added a property for e-z access
        """
        return self.get_full_body()

    def get_formatted_body(self, split=True):
        """
        returns the formatted version of the body text
        """
        LOGGER.debug("get_formatted_body entered for %s", str(self))
        # check for 'more' tag
        if split and self.body.find('<!--more-->') > -1:
            # this is split.
            bodytext = self.body.split('<!--more-->')[0]
            splitted = True
        else:
            bodytext = self.body
            splitted = False

        textproc = FILTERS.get(self.text_filter, convert_linebreaks)
        bodytext = textproc(bodytext)
        if splitted:
            bodytext += """<p><a href="%s">Continue reading "%s"</p>""" %  \
                    (self.get_absolute_url(), self.title)
        return bodytext

    def get_video_body(self):
        """
        if this is a video post, reformat it to embed the video instead of showing the URL
        """
        # parse a video URL... slowly at first, but then badly
        LOGGER.debug("get_video_body entered: %s", str(self))
        video_url = self.body.split("\n")[0]
        if video_url.startswith("http"):
            LOGGER.debug('video_url: %s', video_url)
            if video_url.find('vimeo.com') > -1:
                LOGGER.debug('Got vimeo link')
                # naive ID finder...
                video_id = video_url.split("/")[-1]
                video_link = """<iframe src="//player.vimeo.com/video/%s"
                                width="WIDTH" height="HEIGHT" frameborder="0"
                                webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>
                                """ % video_id
                return video_link
            return "<b>Unsupported Video...</b>"
    # newness?
    get_formatted_body.allow_tags = True

    def get_fuzzy_pub_date(self):
        """
        Whimsical display of time, not really used any more
        """
        LOGGER.debug('get_fuzzy_pub_date entered for %s', str(self))
        hour = self.pub_date.hour
        minute = self.pub_date.minute
        fclock = fuzzyclock.FuzzyClock()
        fclock.setHour(hour)
        fclock.setMinute(minute)
        res = string.capwords(fclock.getFuzzyTime())
        return res

    def get_pingback_count(self):
        """
        Returns the number of pingbacks on this post
        """
        LOGGER.debug("get_pingback_count entered for %s", str(self))
        return len(self.pingback_set.all())

    def get_readability(self):
        """
        Calculates the Readability score.  It's totally
        broken for most text, like anything with Umlauts.
        FIXME: Get a good readability module from somewhere.
        """
        LOGGER.debug('get_readability entered for %s', str(self))
        my_readability = text_stats.calculate_readability(self)
        return my_readability

class Blog(models.Model):
    """
    For different blogs...
    """
    title = models.CharField(blank=True, max_length=100)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    slug = models.SlugField(max_length=100)

    objects = models.Manager()
    on_site = CurrentSiteManager()

    def __str__(self):
        return self.title
    __unicode__ = __str__

    def get_url(self):
        """
        Returns the Site URL for the time being.  This is lazy.
        """
        # return "".join([settings.SITE_URL,"blog","/", str(self.id)]) + "/"
        # return reverse("archive-index")
        # return "http://127.0.0.1:8000/blog/"
        return "http://%s/" % self.site.domain

    def get_absolute_url(self):
        """
        Returns the absolute URL of this blog (from urls.py)
        """
        return reverse('xblog:blog-detail', kwargs={'slug': self.slug})

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        """
        save override for Blog Model
        """
        LOGGER.debug('%s.Blog.save entered %s', __name__, self.title)
        if not self.slug or self.slug == '':
            slug = SlugifyUniquely(self.title, self.__class__)
            LOGGER.debug('Slug not given, setting to %s', slug)
            self.slug = slug

        super(Blog, self).save(force_insert=force_insert,
                               force_update=force_update,
                               using=using,
                               update_fields=update_fields)
        LOGGER.debug('blog.save complete')


class PostForm(ModelForm):
    """
    Django form-based class for editing posts.
    """
    class Meta:
        model = Post
        # exclude = ['update_date', 'create_date', 'slug', ]
        readonly_fields = ('create_date',)
        fields = ['title', 'body', 'author', 'status', 'tags', 'text_filter', 'blog', 'guid']

@receiver(m2m_changed, sender=Post.categories.through)
def check_status_category(sender, **kwargs):
    """
    Checks to see if this is a status-style post, and changes the post type
    accordingly
    """
    LOGGER.debug('XXcheck_status_category entered')
    LOGGER.debug('sent by %s', sender)
    instance = kwargs.pop('instance', None)
    action = kwargs.pop('action', None)
    pk_set = kwargs.pop('pk_set', None)
    LOGGER.debug('XXpk_set:' + str(pk_set))
    status_category = getattr(settings, "XBLOG_STATUS_CATEGORY_NAME", "Status")
    # try to get the status category...
    try:
        status_cat = Category.objects.get(title=status_category)
        LOGGER.debug(status_category +" XXX FOUND")
    except Category.DoesNotExist:
        LOGGER.debug(status_category +" XX NOT FOUND")
        return
    LOGGER.debug('XXXcheck_status_category:' + status_cat.title)
    # first save, so we can check the categories
    LOGGER.debug('XXXnotq id:' + str(status_cat.id))
    LOGGER.debug('XXXnotq pk_set:' + str(pk_set))
    LOGGER.debug('XXXnotq action: ' + str(action))
    if action == "post_add":
        if status_cat.id in pk_set:
            LOGGER.debug('XXXcat:' + status_cat.title)
            instance.post_format = "status"
            # LOGGER.info("XX:%s|%s setting format to 'status'" % (instance.id, instance.title))
            # sender.save()
            instance.save()
        else:
            pass
