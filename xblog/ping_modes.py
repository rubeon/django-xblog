#!/usr/bin/env python
# encoding: utf-8
"""
trackbacktest.py

Created by Eric Williams on 2007-04-04.

Need to audit this for convert_logging

"""
from xml.sax.handler import ContentHandler
from xml.sax import parseString, SAXParseException
from xblog.models import Pingback, Post
from django.conf import settings
import datetime
from django.http import HttpResponseRedirect, HttpResponse, Http404
try:
    import xmlrpc
except ImportError:
    import xmlrpclib as xmlrpc
import urllib, re

try:
    from urllib import urlopen
except ImportError:
    from urllib.request import urlopen

# from external.BeautifulSoup import BeautifulSoup as bs
from bs4 import BeautifulSoup as bs
try:
    import builtins
except ImportError:
    import exceptions as builtins
import logging
logger = logging.getLogger(__name__)

def process_trackback(request, slug):
    logger.debug("process_trackback called")
    if request.method == 'POST':
        logger.info( "Got a trackback, methinks... %s" % slug)
        source_uri = request.POST['url']
        try:
            post = Post.objects.get(slug__exact=slug)
            logger.debug( "post: %s" % post.title)
            target_uri = post.get_absolute_uri()
        except Exception as e:
            logger.warn(e)
            return False
        logger.debug("From: %s" % source_uri)
        logger.debug("To: %s" % target_uri)
        logger.debug("Post:" % post.title)
        res, message = trackback_ping(source_uri, target_uri, check_spam=True)
        if res:
            return HttpResponse("""
            <?xml version="1.0" encoding="iso-8859-1"?>
            <response>
            <error>0</error>
            </response>
            """)
            
        else:
            return HttpResponse("""
            <?xml version="1.0" encoding="iso-8859-1"?>
            <response>
            <error>1</error>
            <message>%s</message>
            </response>
            """ % message)
    else:
        return HttpResponse( "Ping?")
        

def pingback_ping(source_uri, target_uri, check_spam=True, post=None, outgoing=False):
    """
    Pingback interface
    for outgoing pings, set keyword arguments post (post object) and
    outgoing=True
    """
    logger.info("pingback_ping called...")
    logger.info( "Ping from: %s" % source_uri)
    logger.info( "Ping to: %s" % target_uri)
    # check for dupes...
    
    try:
        pb = Pingback.objects.filter(source_url=source_uri).filter(target_url=target_uri)
        for x in pb:
            logger.debug( "-" + str(x))
        if pb.count() > 0:
            # it's a dupe, just ignore it.
            logger.warn( "Got this pingback already, homey.")
            return False
    except Exception as e:
        import sys
        logger.warn(e)
        return False, sys.exc_info()[0]
            
    logger.info("ping: %s -> %s" % (source_uri, target_uri))
    if outgoing:
        p = post
        if source_uri[0]=="/":
          # this is a site-absolute url, let's make it a real one...
          # source_uri = settings.SITE_URL + source_uri[1:]
          source_url = "%s/%s" % (Post.blog.get_url(), source_uri[1:])
          logger.debug("source_url: %s" %  source_url)
          
        logger.info("Sending ping...")
        pingback_address = get_pingback_url(target_uri)
        logger.info("pingback_address: %s" % pingback_address)
        
        if pingback_address:
            try:
                # we got *something*
                logger.info("Sending ping request %s -> %s" % (source_uri, pingback_address))
                s = xmlrpc.client.ServerProxy(pingback_address)
                logger.warn("s: %s" % str(s))
                res = s.pingback.ping(source_uri, target_uri)
                logger.info( "Got back '%s'" % res)
                struct = {}
                struct['author_name'] = post.author.get_profile().fullname
                struct['source_url']  = source_uri
                struct['target_url']  = target_uri
                struct['title'] = post.title
                logger.debug(str(struct))
            except Exception as e:
                import sys
                logger.warn(e)
                return False, sys.exc_info()[0]
    
    else:
        # this is an incoming ping-a-ling
        slug = slug_from_uri(target_uri)
        logger.info( "got %s" % slug)
        
        try:
            if not post:
                p = Post.objects.get(slug__iexact=slug)
            else:
                p = post    
        except:
            logger.warn( "No post for %s" % slug)
            return False
        logger.debug("Got trackback request for '%s'" % p.title)
        # title = p.has_key('title') and request.POST['title'] or ''
        title = p.title
        # excerpt = p.has_key('excerpt') and request.POST['excerpt'] or ''
        is_spam, struct = confirm_pingback(source_uri, target_uri, check_spam = check_spam)
        logger.info("is_spam: %s" % is_spam)
        logger.debug( "struct: %s" % str(struct))
        if check_spam and is_spam:
            logger.info("spam")
            return "Sorry, buddy, go peddle your v1agra somewhere else"
    # ok, let's get this started
    logger.info("Creating Pingback...")
    try:
        pb              = Pingback(
            author_name = struct['author_name'],
            title       = struct['title'],
            source_url  = struct['source_url'],
            target_url  = struct['target_url'],
            is_public   = True,
            pub_date    = datetime.datetime.now(),
            post = p,
        )
        
        logger.debug("Saving pingback...")

        logger.debug(p.post_id)
        logger.debug("Added post, saving PB again...(!)")
        pb.save()
        res = "Pingback to '%s' successfully registered." % title
        logger.debug("pingback_ping completed: res=%s" % str(res))
        return res

    except Exception as e:
        logger.warn("pingback_ping exception: " + str(e))
        # logger.error(e)
        return False

        
def slug_from_uri(uri):
    # take the re from the uri.
    # pat = "http://ericbook.local:8000/blog/2007/mar/05/a-shadow-world-within-a-world/"
    pat = r"%sblog/(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/(?P<slug>[-\w]+)/$" % "http://dev.ehw.io" #FIXME
    c = re.compile(pat)
    m = c.match(uri)
    if m:
        slug = m.groupdict()['slug']
    else:
        slug = ""
    logger.debug( "got slug... %s" % slug)
    return slug
    
def get_pingback_url(target_url):
    """
    Grabs an page, and reads the pingback url for it.
    """
    logger.debug("get_pingback_url called...")
    logger.debug("grabbing " + str(target_url))
    html = urlopen(target_url).read()
    logger.info( "Got %d bytes" % len(html))
    soup = bs(html, 'html.parser')
    # check for link tags...
    pbaddress = None
    for l in soup.findAll('link'):
        if l.get('rel','') == 'pingback':
            pbaddress = str(l.get('href'))
            logger.debug("Got: %s" % pbaddress)
    
    logger.debug("get_pingback_url completed")        
    return pbaddress
    
def confirm_pingback(target_url, search_url, check_spam=True):
    # target url must contain search_url
    # returns bool is_spam, struct  
    logger.debug("Loading external page: %s" % target_url)
    text = urlopen(target_url).read()
    soup = bs(text, 'html.parser')
    logger.info("Checking for URL: %s" % str(search_url))
    for a in soup.findAll('a'):
        if not check_spam or a.get('href') == search_url:
            logger.info( "Got %s" % a.get('href'))
            struct = {}
            # read the author's name, if possible...
            struct['author_name'] = ''
            struct['source_url']  = target_url
            struct['target_url']  = search_url
            struct['title'] = str(soup.html.head.title.string)
            logger.info( "returning pingback")
            return False, struct
    # didn't find it...sod off, spamboy!
    return True, None

def send_pings(post):
    logger.debug("send_pings entered")
    if settings.DEBUG:
        logger.debug("Not sending pings in debug")
        return
    logger.debug("No really, sending pings")
    if post.status=='publish':
        # check for outgoing links.
        logger.debug('Post status is: %s', post.status)
        target_urls = []
        logger.debug(60*'-')
        logger.debug('Post body: %s', post.body)
        logger.debug(60*'-')
        soup = bs(post.get_formatted_body(), 'html.parser')
        logger.debug("Got soup %s", soup)
        for a in soup.findAll('a'):
            target_url = a.get('href',None)
            if target_url:
                logger.info( "Got URL:" + a.get('href'))
                target_urls.append(target_url)
        
        logger.debug("Checking out %d url(s)" % len(target_urls))
        for url in target_urls:
            pb_urls, tb_urls = get_ping_urls(url)
            for pb in pb_urls:
                logger.info("Got pingback URL: %s" % pb)
                pingback_ping(post.get_absolute_url(), pb, post=post, outgoing=True)
            for tb in  tb_urls:
                logger.info("Got trackback URL: %s" % url)
                trackback_ping(post.get_absolute_url(), tb, post=post, outgoing=True)

def trackback_ping(source_uri, target_uri, check_spam=True, post=None, outgoing=False):
    """
    send an MT-style trackback-ping to the given URL, which should be the 
    trackback URL of a blog post
    """

    logger.debug("trackback_ping called...")
    if source_uri[0]=="/":
       # this is a site-absolute url, let's make it a real one...
       # source_uri = settings.SITE_URL + source_uri[1:]
       source_uri = "http://dev.ehw.io/%s" % source_uri[1:] #FIXME
                
    logger.info( "Ping from: %s" % source_uri)
    logger.info( "Ping to: %s" % target_uri)
    # check for dupes...

    try:
        logger.info( "Checking for dupes...")
        pb = Pingback.objects.filter(source_url=source_uri).filter(target_url=target_uri)
        for x in pb:
            logger.debug("- %s" % str(x))
        if pb.count() > 0:
            # it's a dupe, just ignore it.
            logger.warn("Got this pingback already, homey.")
            return False, "Got this pingback already, homey."
    except Exception as e:
        logger.warn(str(e))


    logger.debug("Moving along...")
    logger.info("%s -> %s" % (source_uri, target_uri))
    if outgoing:
        logger.info("outbound ping")
        # trackbacks send a POST to the target URL with:
        # title=title
        # url = post.get_absolute_url
        # excerpt = ??
        # blog_name = post.blog.title
        p = post
        logger.info("Sending trackback...")
        # pingback_address = get_pingback_url(target_uri)
        if target_uri:
            try:
                # we got *something*
                logger.info( "Sending trackback request...")
                # s = xmlrpclib.ServerProxy(pingback_address)
                # res = s.pingback.ping(source_uri, target_uri)
                data = dict(title=p.title, url=source_uri, excerpt=p.summary,blog_name=p.blog.title)
                res = urlopen(target_uri, urllib.urlencode(data)).read()
                logger.info("Got back %s" % str(res))
                struct = {}
                try:
                    struct['author_name'] = post.author.get_profile().fullname
                except:
                    struct['author_name']=post.author.username
                struct['source_url']  = source_uri
                struct['target_url']  = target_uri
                struct['title'] = post.title
            except Exception as e:
                import sys
                logger.warn(e)
                return False, sys.exc_info()[0]

    else:
        # this is an incoming ping-a-ling
        logger.info( "Inbound ping...")
        logger.info( "Checking" % target_uri)
        slug = slug_from_uri(target_uri)
        logger.info("got %s" % slug)

        try:
            if not post:
                p = Post.objects.get(slug__iexact=slug)
            else:
                p = post    
        except:
            logger.warn( "No post for " % slug)
            return False, "Post not found"
        logger.info( "Got trackback request for '%s'" % p.title)
        # title = p.has_key('title') and request.POST['title'] or ''
        title = p.title
        # excerpt = p.has_key('excerpt') and request.POST['excerpt'] or ''
        is_spam, struct = confirm_pingback(source_uri, target_uri, check_spam = check_spam)
        logger.info("is_spam: %s " % str(is_spam))
        logger.debug("struct: %s" % str(struct))
        if check_spam and is_spam:
            logger.info("SPAM!!!11!")
            return False, "Sorry, buddy, go peddle your v1agra somewhere else"
    # ok, let's get this started
    logger.info("Creating Pingback...")
    try:
        pb              = Pingback(
            author_name = struct['author_name'],
            title       = struct['title'],
            source_url  = struct['source_url'],
            target_url  = struct['target_url'],
            is_public   = True,
            pub_date    = datetime.datetime.now(),
            post = p,
        )

        logger.info("Saving pingback...")

        logger.debug(p.post_id)
        # pb.post = p
        logger.debug("Added post, saving PB again...(!)")
        pb.save()
        logger.debug("saved PBw")
        res = "Pingback to '%s' successfully registered." % pb.title
        logger.debug(res)
        return True, res

    except Exception as e:
        logger.warn(str(e))
        return False, "Unknown Error"

    
    
def get_ping_urls(url):
    """
    returns a two-tuple of lists, ([pingback urls],[trackback urls])
    """
    logger.debug('get_ping_urls called: %s', url)
    ping_urls = []
    tb_urls = []
    
    try:
        logger.debug('Trying to contact: %s', url)
        txt = str(urlopen(url).read())
    except builtins.IOError as e:
        logger.warn("Failed to open %s: IOError" % str(url))
        return [], []
    except ValueError as e:
        logger.warn('Received a bad URL: %s', url)
        return [], []
    logger.debug("Got %d bytes" % len(txt))
    soup = bs(txt, 'html.parser')
    # walk through the links, looking for ping-entries
    
    for a in soup.findAll('link'):
        logger.debug('link: %s', a)
        rel = a.get('rel')
        if rel == 'pingback':
            logger.debug("Got pingback URL: %s" % a.href)
            ping_urls.append(a.get('href'))
    
    # now do t he trackbacks...
    logger.debug('Got the following pingback URLs: [%s]', ping_urls)
    tb_re=re.compile('(<rdf:RDF .*?</rdf:RDF>)')
    rdfdata = RDF()
    for x in tb_re.findall(txt.replace('\n',' ')):
        try:
            parseString(x, rdfdata)
            logger.debug( "URL: %s" % rdfdata.attrs.get('dc:identifier'))
            logger.debug("Trackback URL: %s" % rdfdata.attrs.get('trackback:ping'))
            tb_urls.append(rdfdata.attrs.get('trackback:ping'))
        except Exception as e:
            logger.warn('get_ping_urls: %s', str(e))
    
    return ping_urls, tb_urls


class RDF(ContentHandler):
    """ xml -> dictionary of {dc:identifier => trackback:ping|rdf:about}

    Parse a given html page, and retrieve the rdf:about information associated
    with a given href.
    """
    attrs = {}
    ids = {}
    def startElement(self, name, attrs):
        if name == 'rdf:Description':
            attrs=dict(attrs)
            self.attrs = attrs
            logger.debug("ATTRS: %s" % str(attrs))
            if attrs.has_key('dc:identifier'):
                logger.debug("ID: %s" % attrs['dc:identifier'])
                if attrs.has_key('trackback:ping'):
                    self.ids[attrs['dc:identifier']] = attrs['trackback:ping']
                elif attrs.has_key('about'):
                    self.ids[attrs['dc:identifier']] = attrs['about']
                elif attrs.has_key('rdf:about'):
                    self.ids[attrs['dc:identifier']] = attrs['rdf:about']


if __name__=='__main__':
    tb_test_url = "http://jaksrv.local/mt/2007/03/test_fo_die_trackabacakas.html"
    ping_test_url = "http://rubeon.ath.cx/wp/?p=29"
    print(get_ping_urls(tb_test_url))
    print(get_ping_urls(ping_test_url))
    