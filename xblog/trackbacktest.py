#!/usr/bin/env python
# encoding: utf-8
"""
trackbacktest.py

Created by Eric Williams on 2007-04-04.
"""
from xml.sax.handler import ContentHandler
from xml.sax import parseString, SAXParseException

import urllib, re
from external.BeautifulSoup import BeautifulSoup as bs
def get_ping_urls(url):
    """
    returns a two-tuple of lists, ([pingback urls],[trackback urls])
    """
    ping_urls = []
    tb_urls = []
    
    txt = urllib.urlopen(url).read()
    print("Got %d bytes" % len(txt))
    soup = bs(txt)
    # walk through the links, looking for ping-entries
    
    for a in soup.findAll('link'):
        print(a)
        rel = a.get('rel')
        if rel == 'pingback':
            print("Got pingback URL:", a.href)
            ping_urls.append(a.get('href'))
    
    # now do t he trackbacks...
    tb_re=re.compile('(<rdf:RDF .*?</rdf:RDF>)')
    rdfdata = RDF()
    for x in tb_re.findall(txt.replace('\n',' ')):
        parseString(x, rdfdata)
        # print rdf.ids
        print("URL:", rdfdata.attrs.get('dc:identifier'))
        print("Trackback URL:", rdfdata.attrs.get('trackback:ping'))
        tb_urls.append(rdfdata.attrs.get('trackback:ping'))
    
    return ping_urls, tb_urls


class RDF(ContentHandler):
    """ xml -> dictionary of {dc:identifier => trackback:ping|rdf:about}

    Parse a given html page, and retrieve the rdf:about information associated
    with a given href.
    """
    attrs = {}
    ids = {}
    def startElement(self, name, attrs):
        # print name, attrs
        if name == 'rdf:Description':
            attrs=dict(attrs)
            self.attrs = attrs
            # print "ATTRS:", attrs
            if attrs.has_key('dc:identifier'):
                # print "ID:", attrs['dc:identifier']
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
    