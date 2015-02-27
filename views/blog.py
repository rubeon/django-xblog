#!/usr/bin/env python
# encoding: utf-8
"""
blog.py

Created by Eric Williams on 2007-02-21.
"""
from django.contrib.auth.decorators import login_required
from django.template import RequestContext, Context, loader
from django.views.generic.list import ListView
# from xcomments.models import FreeComment
from django.http import HttpResponseRedirect, HttpResponse, Http404
from xblog.models import Post, Blog, Author


from xml.etree import ElementTree
from xml.dom import minidom

import logging
logger = logging.getLogger(__name__)

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
    
    

def template_preview(request, **kwargs):
    """
    just let's me preview a template in context...
    """
    logger.debug("template_preview entered")
    tmpl = kwargs.get("template_file", None)
    logger.info("previewing '%s'" % tmpl)
    if tmpl:
        try:
            c = {}
            context = RequestContext(request, c)
            t = loader.get_template("xblog/%s.html" % tmpl )
            logger.info("Got %s" % t)
            return HttpResponse(t.render(context))
        except Exception, e:
            logger.warn(e)
            return HttpResponse(str(e))
    else:
        return HttpResponse("Please specify template filename")
    

def blog_overview(request):
    # shows the latest entries in all blogs...
    # get last posts...
    # r = HttpResponse(mimetype="text/plain")
    logger.debug("blog_overview entered")
    latest_posts = Post.objects.order_by('-pub_date')[:10]
    # thisblog = Blog.objects.all()[0]
    c = {}
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
    c = {}
    ignorelist = ['Feature','Miscellany','Uncategorized']
    frontlist = []
    featurecat = Category.objects.get(title__iexact='Feature')
    for cat in Category.objects.all():
        if cat.title not in ignorelist:
            # get latest in this category...
            try:
                p = Post.objects.filter(categories__in=[cat]).order_by('-pub_date')[:10]
                if p:
                    p.mycat = cat
                    frontlist.append(p)
            except Exception, e:
                logger.warn("%s:%s" % (cat, e)) 
    

    latest_posts = Post.objects.all().order_by('-pub_date')[:10]
    # latest_comments = FreeComment.objects.all().order_by('-submit_date')[:10]
    
    c['latest_feature'] = featurecat.post_set.order_by('-pub_date')
    logger.debug("Latest feature: %s" % c['latest_feature'])
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
