#!/usr/bin/env python
import os
import sys
os.environ['DJANGO_SETTINGS_MODULE']= 'settings'
SITE_DIR = os.path.abspath(os.path.split(__file__)[0]+'/..')
#print __file__
#print SITE_DIR
sys.path.insert(0,SITE_DIR)
sys.path.insert(0,os.path.join(SITE_DIR,'..'))
sys.path.insert(0,os.path.join(SITE_DIR,'..','..'))
# os.chdir('..')
#print sys.path
from django.template.defaultfilters import slugify
try:
    from django.contrib.auth import get_user_model
    User = settings.AUTH_USER_MODEL
except ImportError:
    from django.contrib.auth.models import User 

try:
    from django.contrib.auth import get_user_model
    User = settings.AUTH_USER_MODEL
except ImportError:
    from django.contrib.auth.models import User 
import datetime
import shutil
import settings

from xblog.models import *
#

def add_podcast(struct):
    # adds the podcast according to information in struct
    # struct is a dictionary with:
    # src_file
    # title
    # subtitle
    # categories (list of category names)
    # summary - longish text
    # author - django user object of author
    # channel - if not provided, choose default
    # returns django podcast object
    
    target_dir = os.path.join(settings.MEDIA_ROOT,'blog_uploads','podcasts/')
    src_file = struct['src_file']
    orig_filename = target_filename = os.path.basename(src_file)
    
    i = 0
    while os.path.exists(os.path.join(target_dir,target_filename)):
        target_filename = "%d-%s" % (i,orig_filename)
        i = i + 1
    #  copy the file...
    shutil.copy(src_file, os.path.join(target_dir,target_filename))
    # choose the default channel...
    channel = PodcastChannel.objects.get(pk=1)
    print channel
    title = struct['title']
    subtitle= struct['subtitle']
    categories = Category.objects.all()[:1]
    summary = "Here is a summary, bub."
    slug = slugify(title)
    author = Author.objects.get(user = struct['author'])
    
    print "Using author", author
    enclosure = os.path.join(target_dir,target_filename).replace(settings.MEDIA_ROOT,'')    
    # djangofy the podcast
    p = Podcast(
      title = title,
      subtitle= subtitle,
      channel = channel,
      summary = summary,
      slug = slug,
      pubdate = datetime.datetime.now(),
      author = author,
      enclosure=enclosure,
    )
    p.save()
    # once saved, categories can be added...
    p.categories = categories
    p.save()
    return p
    

if __name__=='__main__':
    # add a postcast from the commandline
    import getopt
    title = "Default Title"
    subtitle = "Default Subtitle"
    struct = {}
    options, args = getopt.getopt(sys.argv[1:], 'i:o:t:s:a:',["input-file=","output-file=", "title=","subtitle=","author=" ])
    for opt, val in options:
        if opt in ('-i','--input-file'):
            src_file = val
        elif opt in ('-o','--output-file'):
            target_file = val
        elif opt in ('-t','--title'):
            title = val
        elif opt in ('-s','--subtitle'):
            subtitle = val
        elif opt in ('-a','--author'):
            author = val
            
    struct['title'] = title
    struct['subtitle'] = subtitle
    struct['src_file'] = src_file
    # struct['target_file'] = target_file
    struct['author'] = User.objects.get(username__exact = author)
    res = add_podcast(struct)
    print res.enclosure