#!/usr/local/bin/python
# import feedparser
import os
import sys
import datetime

import traceback
# import chardet
import MySQLdb
from MySQLdb.cursors import DictCursor

os.environ['DJANGO_SETTINGS_MODULE']= 'settings'
SITE_DIR = os.path.abspath(os.path.split(__file__)[0]+'/..')
#print __file__
#print SITE_DIR
sys.path.insert(0,SITE_DIR)
sys.path.insert(0,os.path.join(SITE_DIR,'..'))
sys.path.insert(0,os.path.join(SITE_DIR,'..','..'))
# print sys.path
from xblog.models import Post, Category, Blog, Author, Tag, Link, LinkCategory, Pingback
from django.conf import settings
from django.contrib.auth.models import User 
from django.contrib.contenttypes.models import ContentType
from xcomments.models import FreeComment
from django.contrib.sites.models import Site
from xblog import metaWeblog


def xmlify(data):
    return data
    replaced=False
    for let in data:
        # fix non-unicodies.
        if ord(let) > 127:
            replaced=True
            print "Replacing %s -> &%d;" % (let,ord(let) )
            data = data.replace(let,"&#%d;" % ord(let))

    return data

from import_config import config            
config['cursorclass'] = DictCursor
conn = MySQLdb.connect(**config)
cur = conn.cursor()
# load the posts
q = "select * from ybwp_posts"
cur.execute(q)
posts = cur.fetchall()
print len(posts)
REPLACE=1

if REPLACE:
    print "Cleaning out posts..."
    for post in Post.objects.all():
        post.delete()
        
    print "Cleaning out categories..."
    for cat in Category.objects.all():

        cat.delete()
        
    print "Cleaning out tags..."
    for tag in Tag.objects.all():
        tag.delete()
    
    print "Cleaning out Links..."
    for link in Link.objects.all():
        link.delete()

    print "Cleaning out pingbacks..."
    for p in Pingback.objects.all():
        p.delete()
        
    print "Killing comments"
    ct = ContentType.objects.get(model__exact='post')
    for comment in FreeComment.objects.filter(content_type=ct):
        print "deleting comment", comment.id
        comment.delete()
        


# load the categories
q = "select * from ybwp_categories"
cur.execute(q)
cats = cur.fetchall()
loblog = Blog.objects.get(id__exact=1)
print loblog
louser = User.objects.get(username__exact='Rube')


# get links...
q = """
            SELECT * FROM 
                ybwp_categories, ybwp_links, ybwp_link2cat
            WHERE
                ybwp_links.link_id = ybwp_link2cat.link_id 
            AND
                ybwp_categories.cat_ID = ybwp_link2cat.category_id

"""

cur.execute(q)
links = cur.fetchall()

for link in links:
    # try to get the category...
    try:

        cat = LinkCategory.objects.get(title__iexact=link['cat_name'])
    except:
        # create a new category...blah.
        print "Creating category", link['cat_name']
        cat = LinkCategory(
            title=link['cat_name'],
            description=link['category_description'],
            blog=loblog,
            visible=True
        )
        cat.save()
    # create a new link...
    l = Link(
        link_name = link['link_name'],
        category = cat,
        description=link['link_description'],
        rss=link['link_rss'],
        visible=True,
        url=link['link_url'],
        blog=loblog,
        
    )
    print l.description
    try:
        l.save()
    except:
        pass



print len(cats), "categories loaded..."
# for each wordpress entry
counter = 1
for post in posts:
    status =  "Processing %d from %d" % (counter, len(posts))
    counter = counter + 1
    # publish time
    # author
    # categories
    q = """
    select ybwp_categories.cat_name, ybwp_categories.category_description
        from ybwp_categories, ybwp_post2cat
    where ybwp_post2cat.post_id = %d and ybwp_categories.cat_ID = ybwp_post2cat.category_id
    """  % (post['ID'])
    cur.execute(q)
    mycats = cur.fetchall()
    # status 
    # cq = "select * from ybwp_comments where comment_post_ID = %d" % entry['ID']
    # cur.execute(q)
    # comments = cur.fetchall()
    # 
    catlist = []
    for cat in mycats:
      # try to get the category
      try:
          locat = Category.objects.get(title__iexact=cat['cat_name']) 
          # print "Found category", locat
      except Exception, e:
          print "Error:", e
          # create the category...
          print "Creating", cat['cat_name']
          locat = Category(title=cat['cat_name'], description=cat['category_description'], blog=loblog)
          locat.save()
        
      catlist.append(locat)
      # print chardet.detect(post['post_title'])
    # post['post_title'] = post['post_title'].encode('latin-1')
    # post['post_content'] = post['post_content'].encode('latin-1')
    try:
        # let's see if this post already exists...
        p = Post.objects.get(title__exact=post['post_title'])
        # print "Found similar post", p.title
        if p.create_date == post['post_date']:
            print "NOT IMPORTING %s -- it exists" % str(p)
    except:
        status = status +  ": %s" % post['post_title']
        # mod the dates...
        for dtime in ['post_date', 'post_modified']:
            if not post[dtime]:
                post[dtime] = datetime.datetime.now()
        p = Post(
               title=post['post_title'],
               body = post['post_content'],
               create_date = post['post_date'],
               update_date = post['post_modified'],
               pub_date = post['post_date'],
               blog = loblog,
               author =louser,
               status = post['post_status'],
               slug=post['post_name']
               )
        
        
        p.prepopulate()
        try:
            p.save()
            p.categories = catlist
            p.save()
        except:
            import traceback
            traceback.print_exc(sys.stderr)
        
        
        # get comments for this post...
        q = """
        SELECT * FROM ybwp_comments
            WHERE
        comment_post_ID = %d
        """ % post['ID']
        try:
            cur.execute(q)
            comments = cur.fetchall()
            ct = ContentType.objects.get(model__exact='post')
            site = Site.objects.get(id__exact=settings.SITE_ID)
            # create a comment for each comment...
        except:
            traceback.print_exc(sys.stdout)
            comments=[]
            raw_input("press enter...")

        for comment in comments:
            if comment['comment_type'] == 'pingback':
                # create a pingback for this post...
                metaWeblog.pingback_ping(comment['comment_author_url'], p.get_absolute_url(), check_spam=False, post=p)
                
            else:
                if comment['comment_approved']!='spam':
                    c = FreeComment(
                        content_type = ct,
                        object_id = p.id,
                        comment = xmlify(comment['comment_content']),
                        person_name = comment['comment_author'],
                        person_email = xmlify(comment['comment_author_email']),
                        person_url = xmlify(comment['comment_author_url']),
                        # submit_date = comment['comment_date'],
                        is_public = comment['comment_approved'],
                        ip_address = comment['comment_author_IP'],
                        # approved = comment['comment_approved'],
                        site =site,
                
                    )
                    
                    
                    try:
                        c.save()
                        c.submit_date = comment['comment_date']
                        c.save()
                    except:
                        print "ERROR:"
                        traceback.print_exc(sys.stderr)
                        print c.person_name
                        print c.person_url                        
                        print c.comment
                        
                        raw_input('error: hit enter to continue')
        status = status + ": %d comments" % len(comments)
        print status