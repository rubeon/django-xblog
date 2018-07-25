#!/usr/bin/env python
# encoding: utf-8
"""
blog.py

Created by Eric Williams on 2007-02-21.
"""
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.template import RequestContext, Context, loader
from django.shortcuts import get_object_or_404

# from xcomments.models import FreeComment
from django.http import HttpResponseRedirect, HttpResponse, Http404
from xblog.models import Post, Blog, Author, Category
from django.views.generic.dates import YearArchiveView
from django.views.generic.dates import MonthArchiveView
from django.views.generic.dates import DayArchiveView
from django.views.generic.dates import ArchiveIndexView
from django.views.generic.dates import DateDetailView

from django.views.generic.list import ListView

from django.views.generic.edit import CreateView
from django.views.generic.edit import UpdateView
from django.views.generic.edit import DeleteView

from django.views.generic.detail import DetailView

from xml.etree import ElementTree
from xml.dom import minidom

LOGGER = logging.getLogger(__name__)

"""
def tag_overview(request, tag):
    # grabs a list of tags...
    t = Tag.objects.get(title__iexact=tag)
    latest_posts = t.post_set.order_by('-pub_date')[:10]
    c = {}
    c['latest_posts'] = latest_posts
    c['pagetitle'] = "Tag Overview: %s" % t.title
    c['pageclass'] = "blog"

    context = RequestContext(request, c)
    t = loader.get_template('xblog/overview.html')

    return HttpResponse(t.render(context))
"""

class AuthorListView(ListView):
    # shows the list of authors
    model = Author

def empty(request, **kwargs):
    LOGGER.debug("%s.empty entered", __name__)
    t = loader.get_template("xblog/first_page")
    return HttpResponse({}, request)

def template_preview(request, **kwargs):
    """
    just let's me preview a template in context...
    """
    LOGGER.debug("template_preview entered")
    tmpl = kwargs.get("template_file", None)
    LOGGER.info("previewing '%s'" % tmpl)
    if tmpl:
        try:
            c = {}
            context = RequestContext(request, c)
            t = loader.get_template("xblog/%s.html" % tmpl )
            LOGGER.info("Got %s" % t)
            html = t.render(c, request)
            return HttpResponse(html)
        except Exception as e:
            import sys, traceback
            print("Exception in user code:")
            print('-'*60)
            traceback.print_exc(file=sys.stdout)
            print('-'*60)
            LOGGER.warn(e.message)
            return HttpResponse(str(e))
    else:
        return HttpResponse("Please specify template filename")


def blog_overview(request):
    # shows the latest entries in all blogs...
    # get last posts...
    # r = HttpResponse(mimetype="text/plain")
    LOGGER.debug("blog_overview entered")
    latest_posts = Post.objects.filter(status='publish').order_by('-pub_date')[:10]

    # thisblog = Blog.objects.all()[0]
    c = {}
    c['site'] = Site.objects.get_current()

    c['latest_posts'] = latest_posts
    c['pagetitle'] = "blog"
    c['pageclass'] = "blog"
    # c['thisblog'] = thisblog
    context = RequestContext(request, c)
    t = loader.get_template('xblog/overview.html')

    return HttpResponse(t.render(context))


def site_overview(request):
    # a default start page
    # includes:
    # - last 5 blog entries, as summary..?
    # latest special, which doesn't exist yet.
    # some content.
    # latest comments
    LOGGER.debug('site_overview entered')
    c = {}
    ignorelist = ['Feature','Miscellany','Uncategorized']
    frontlist = []
    # featurecat = Category.objects.get(title__iexact='Feature')
    # for cat in Category.objects.all():
    #     if cat.title not in ignorelist:
    #         # get latest in this category...
    #         try:
    #             p = Post.objects.filter(categories__in=[cat]).order_by('-pub_date')[:10]
    #             if p:
    #                 p.mycat = cat
    #                 frontlist.append(p)
    #         except Exception as e:
    #             LOGGER.warn("%s:%s" % (cat, e))


    latest_posts = Post.objects.filter(status='publish').order_by('-pub_date')[:10]
    # latest_comments = FreeComment.objects.all().order_by('-submit_date')[:10]

    c['latest_feature'] = featurecat.post_set.order_by('-pub_date')
    LOGGER.debug("Latest feature: %s" % c['latest_feature'])
    c['latest_posts']= latest_posts
    # c['latest_comments']= latest_comments
    c['frontlist']=frontlist

    context = RequestContext(request, c)
    t = loader.get_template('base_site.html')
    return HttpResponse(t.render(context))

def export_opml(request):
    """
    export Links to opml
    this was lifted from the "django_feedreader" application, which you
    should definitely check out: https://github.com/ahernp/django-feedreader
    """
    LOGGER.debug('export_opml entered')
    root = ElementTree.Element('opml')
    root.set('version', '2.0')
    head = ElementTree.SubElement(root, 'head')
    title = ElementTree.SubElement(head, 'title')
    title.text = 'XBlog Blogroll Feeds'
    body = ElementTree.SubElement(root, 'body')

    # feeds = Feed.objects.filter(group=None)
    feeds = Link.objects.filter(category=None)
    for feed in feeds:
        if feed.rss !="":
            feed_xml = ElementTree.SubElement(body,
                                  'outline',
                                  {'type': 'rss',
                                   'text': feed.link_name,
                                   'xmlUrl': feed.rss,
                                   }
            )

    groups = LinkCategory.objects.all()
    for group in groups:
        group_xml = ElementTree.SubElement(body,
                               'outline',
                               {'text': group.title,
                                }
        )
        feeds = Link.objects.filter(category=group).exclude(rss="")
        for feed in feeds:
            feed_xml = ElementTree.SubElement(group_xml,
                                  'outline',
                                  {'type': 'rss',
                                   'text': feed.link_name,
                                   'xmlUrl': feed.rss,
                                   }
            )
    response = HttpResponse(content_type='text/xml')
    response['Content-Disposition'] = 'attachment; filename="feedreader.opml"'
    response.write(minidom.parseString(ElementTree.tostring(root, 'utf-8')).toprettyxml(indent="  "))
    return response
# def trackback(request, id):
#     # cribbed from http://www.personal-api.com/train/2007/jan/31/how-add-trackbacks-django/
#     (post, meta) = (request.POST, request.META)
#     error = None
#     try:
#         # The URL is the only required parameter
#         if post.has_key('url'):
#             url = post['url']
#         else:
#             raise Exception("Trackback URL Not provided")
#         r = Response(p = Post.objects.get(id=int(id)),
#             mode="trackback", url=url
#         )
#
#         # use the title and url to create excerpt
#         title = post.has_key('title') and request.POST['title'] or ''
#         excerpt = post.has_key('excerpt') and request.POST['excerpt'] or ''
#         r.content = (title + "\n\n" + excerpt).strip()
#
#         # fill in Akismet information from the request
#         if meta.has_key('REMOTE_ADDR'): r.ip = meta['REMOTE_ADDR']
#         if meta.has_key('HTTP_USER_AGENT'): r.user_agent = meta['HTTP_USER_AGENT']
#         if meta.has_key('HTTP_REFERER'): r.referrer = meta['HTTP_REFERER']
#
#
#     except Exception, message:
#         error = {'code':1, 'message': message}
#         # trackback errors
#         from django.core.mail import mail_admins
#         mail_admins('Failed Trackback', 'Trackback from %s to %s failed with %s', % (blog_name, url, message))
#
#     else:
#         r.save()
#
#         response = HttpResponse(mimetype='text/xml')
#             t = loader.get_template('train/trackback.xml')
#             c = Context({'error': error})
#             response.write(t.render(c))
#             return response

class AuthorCreateView(CreateView):
    model = Author
    fields = ['fullname', 'url', 'avatar']

class AuthorUpdateView(UpdateView):
    model = Author
    fields = ['fullname','url','avatar']

class AuthorDetailView(DetailView):
    model = Author

    def get_object(self, **kwargs):
        res = get_object_or_404(Author, user__username=self.kwargs.get('username'))
        return res

class CategoryDetailView(ListView):
    """
    This is actually a post view.
    """
    model = Post
    slug_url_kwarg = "cat_slug"

    def get_queryset(self, *args, **kwargs):
        LOGGER.debug("CategoryDetailView.get_queryset entered...")
        category = Category.objects.get(slug=self.kwargs[self.slug_url_kwarg])
        qs = category.post_set.all()
        return qs


    def get_object(self):
         # this view should get blog_slug and cat_slug
         LOGGER.debug("CategoryDetailView.get_object entered")
         LOGGER.debug(self.args)
         LOGGER.debug(self.kwargs)
         blog = Blog.objects.get(slug=self.kwargs['blog_slug'])
         category = Category.objects.get(slug=self.kwargs['cat_slug'])
         if category.blog == blog:
             return category
         else:
             return Http404
    def get_slug_field(self):
        return "cat_slug"

class BlogCreateView(CreateView):
    model = Blog
    fields = ['title', 'description']

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.site = Site.objects.get_current()
        return super(BlogCreateView, self).form_valid(form)

class BlogDetailView(DetailView):
    model = Blog
    fields=['title','description', 'owner']

class BlogUpdateView(UpdateView):
    model = Blog
    fields=['title', 'description']
    # success_url = "../blog_details/"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.site = Site.objects.get_current()
        return super(BlogUpdateView, self).form_valid(form)



class PostYearArchiveView(YearArchiveView):
    queryset = Post.objects.filter(status="publish")
    date_field = "pub_date"
    make_object_list = True
    allow_future = True

    Model = Post

    def get_context_data(self, **kwargs):
        """
        makes custom context available in PostYearArchiveView
        """
        LOGGER.debug("PostYearArchiveView.get_context_data entered")
        # Call the base implementation first to get a context
        context = super(PostYearArchiveView, self).get_context_data(**kwargs)
        context['site'] = Site.objects.get_current()
        return context

    # def get_queryset(self):
    #     LOGGER.debug("get_queryset entered...")
    #     if hasattr(self, 'owner'):
    #         LOGGER.debug("i has owner")
    #         queryset = Post.objects.filter(author=self.owner)
    #     else:
    #         LOGGER.debug("i has no owner")
    #         queryset = self.queryset
    #         LOGGER.debug('queryset %s', queryset)
    #     return queryset


class PostMonthArchiveView(MonthArchiveView):
    queryset = Post.objects.filter(status="publish")
    date_field = "pub_date"
    make_object_list = True
    allow_future = True
    # LOGGER.debug(queryset)
    Model = Post

    def get_context_data(self, **kwargs):
        """
        # makes custom context available in PostYearArchiveView
        """
        LOGGER.debug("PostMonthArchiveView.get_context_data entered")
        # Call the base implementation first to get a context
        context = super(PostMonthArchiveView, self).get_context_data(**kwargs)
        context['site'] = Site.objects.get_current()
        return context

class PostDayArchiveView(DayArchiveView):
    queryset = Post.objects.filter(status="publish")
    date_field = "pub_date"
    make_object_list = True
    allow_future = True
    # LOGGER.debug(queryset)
    Model = Post

    def get_context_data(self, **kwargs):
        """
        # makes custom context available in PostYearArchiveView
        """
        # Call the base implementation first to get a context
        context = super(PostDayArchiveView, self).get_context_data(**kwargs)
        context['site'] = Site.objects.get_current()
        return context


class PostArchiveIndexView(ArchiveIndexView):
    queryset = Post.objects.filter(status="publish")
    date_field = "pub_date"
    make_object_list = True
    allow_future = True
    # LOGGER.debug(queryset)
    Model = Post
    allow_empty = True

    def get_context_data(self, **kwargs):
        """
        # makes custom context available in PostYearArchiveView
        """
        # Call the base implementation first to get a context
        context = super(PostArchiveIndexView, self).get_context_data(**kwargs)
        context['site'] = Site.objects.get_current()
        return context

class PostDateDetailView(DateDetailView):
    queryset = Post.objects.filter(status="publish")
    date_field = "pub_date"
    make_object_list = True
    allow_future = True
    # LOGGER.debug(queryset)
    Model = Post

    def get_context_data(self, **kwargs):
        """
        # makes custom context available in PostYearArchiveView
        """
        # Call the base implementation first to get a context
        context = super(PostDateDetailView, self).get_context_data(**kwargs)
        context['site'] = Site.objects.get_current()
        return context
