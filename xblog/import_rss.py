"""
Imports a WordPress blog (older one, haven't tested with new ones)
into an XBlog site.

"""
#!/usr/local/bin/python
# import feedparser
import os
import sys
import datetime

import traceback
# import chardet
import MySQLdb # pylint: disable=import-error
from MySQLdb.cursors import DictCursor # pylint: disable=import-error
from xblog.models import Post, Category, Blog, Tag, Link, LinkCategory, Pingback
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from xcomments.models import FreeComment # pylint: disable=import-error
from import_config import config # pylint: disable=import-error

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
SITE_DIR = os.path.abspath(os.path.split(__file__)[0]+'/..')
#print __file__
#print SITE_DIR
sys.path.insert(0, SITE_DIR)
sys.path.insert(0, os.path.join(SITE_DIR, '..'))
sys.path.insert(0, os.path.join(SITE_DIR, '..', '..'))
# print sys.path

def xmlify(data):
    """
    Converts high-ascii characters to HTML/XML entities
    """
    # return data
    # replaced = False
    for let in data:
        # fix non-unicodies.
        if ord(let) > 127:
            # replaced = True
            print "Replacing %s -> &%d;" % (let, ord(let))
            data = data.replace(let, "&#%d;" % ord(let))
    return data

def main():
    """docstring for main"""
    config['cursorclass'] = DictCursor
    cur = MySQLdb.connect(**config).cursor()
    # load the posts
    cur.execute("select * from ybwp_posts")
    posts = cur.fetchall()
    print "Cleaning out posts..."
    Post.objects.all().delete()

    print "Cleaning out categories..."
    Category.objects.all().delete()

    print "Cleaning out tags..."
    Tag.objects.all().delete()

    print "Cleaning out Links..."
    Link.objects.all().delete()

    print "Cleaning out pingbacks..."
    Pingback.objects.all().delete()

    print "Killing comments"
    FreeComment.objects.filter(content_type=\
                               ContentType.objects.get(\
                               model__exact='post')).delete()

    # load the categories
    # cur.execute("select * from ybwp_categories")
    # cats = cur.fetchall()
    loblog = Blog.objects.get(pk=1)
    print loblog
    louser = User.objects.filter(username__exact='Rube')

    # get links...
    cur.execute("""
                SELECT * FROM 
                    ybwp_categories, ybwp_links, ybwp_link2cat
                WHERE
                    ybwp_links.link_id = ybwp_link2cat.link_id 
                AND
                    ybwp_categories.cat_ID = ybwp_link2cat.category_id
            """)

    for link in cur.fetchall():
        # try to get the category...
        try:
            cat = LinkCategory.objects.get(title__iexact=link['cat_name'])
        except LinkCategory.DoesNotExist:
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
        link = Link(
            link_name=link['link_name'],
            category=cat,
            description=link['link_description'],
            rss=link['link_rss'],
            visible=True,
            url=link['link_url'],
            blog=loblog,
        )
        print link.description
        try:
            link.save()
        except Link.DoesNotExist:
            pass

    # for each wordpress entry
    for post in posts:
        status = "Processing %d" % (len(posts))
        cur.execute("""
        select ybwp_categories.cat_name, ybwp_categories.category_description
            from ybwp_categories, ybwp_post2cat
        where ybwp_post2cat.post_id = %d and ybwp_categories.cat_ID = ybwp_post2cat.category_id
        """  % (post['ID']))

        # status
        # cq = "select * from ybwp_comments where comment_post_ID = %d" % entry['ID']
        # cur.execute(q)
        # comments = cur.fetchall()
        #
        catlist = []
        for cat in cur.fetchall():
          # try to get the category
            try:
                locat = Category.objects.get(title__iexact=cat['cat_name'])
                # print "Found category", locat
            except Category.DoesNotExist, error:
                print "Error:", error
                # create the category...
                print "Creating", cat['cat_name']
                locat = Category(title=cat['cat_name'], description=cat['category_description'],
                                 blog=loblog)
                locat.save()
            catlist.append(locat)
            # print chardet.detect(post['post_title'])
            # post['post_title'] = post['post_title'].encode('latin-1')
            # post['post_content'] = post['post_content'].encode('latin-1')
        try:
            # let's see if this post already exists...
            xpost = Post.objects.get(title__exact=post['post_title'])
            # print "Found similar post", p.title
            if xpost.create_date == post['post_date']:
                print "NOT IMPORTING %s -- it exists" % str(post)
        except Post.DoesNotExist:
            status = status +  ": %s" % post['post_title']
            # mod the dates...
            for dtime in ['post_date', 'post_modified']:
                if not post[dtime]:
                    post[dtime] = datetime.datetime.now()
            xpost = Post(title=post['post_title'],
                         body=post['post_content'],
                         create_date=post['post_date'],
                         update_date=post['post_modified'],
                         pub_date=post['post_date'],
                         blog=loblog,
                         author=louser,
                         status=post['post_status'],
                         slug=post['post_name']
                        )

            xpost.prepopulate()
            try:
                xpost.save()
                xpost.categories = catlist
                xpost.save()
            except Post.DoesNotExist:
                traceback.print_exc(sys.stderr)

            # get comments for this post...
            try:
                cur.execute("""
            SELECT * FROM ybwp_comments
                WHERE
            comment_post_ID = %d
            """ % post['ID'])
                comments = cur.fetchall()
                contenttype = ContentType.objects.get(model__exact='post')
                site = Site.objects.get(id__exact=settings.SITE_ID)
                # create a comment for each comment...
            except Site.DoesNotExist:
                traceback.print_exc(sys.stdout)
                comments = []
                raw_input("press enter...")

            for comment in comments:
                if comment['comment_type'] == 'pingback':
                    # create a pingback for this post...
                    continue

                else:
                    if comment['comment_approved'] != 'spam':
                        newcomment = FreeComment(content_type=contenttype,
                                                 object_id=xpost.id,
                                                 comment=xmlify(comment['comment_content']),
                                                 person_name=comment['comment_author'],
                                                 person_email=\
                                                    xmlify(comment['comment_author_email']),
                                                 person_url=xmlify(comment['comment_author_url']),
                                                 # submit_date=comment['comment_date'],
                                                 is_public=comment['comment_approved'],
                                                 ip_address=comment['comment_author_IP'],
                                                 # approved=comment['comment_approved'],
                                                 site=site,
                                                )
                        try:
                            newcomment.save()
                            newcomment.submit_date = comment['comment_date']
                            newcomment.save()
                        except FreeComment.DoesNotExist:
                            print "ERROR:"
                            traceback.print_exc(sys.stderr)
                            print newcomment.person_name
                            print newcomment.person_url
                            print newcomment.comment

                            raw_input('error: hit enter to continue')
            status = status + ": %d comments" % len(comments)
            print status

if __name__ == '__main__':
    main()
