"""
Importing from a WordPress blog:

- get a list of authors
- get a list of categories
- get a list of posts

First, Create a local cache of all the posts.



map an author to the logged-in guy

"""

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    print 20*'x'
    print User
except ImportError:
    from django.contrib.auth.models import User 


from optparse import make_option
from xblog.models import Blog, Post, Author
import sys
import xmlrpclib
import urllib
import getpass
import os
import BeautifulSoup
import json
import getpass
from pprint import pprint
# username = "subcriticalorg"
# password = getpass.getpass()
# password = open(os.path.expanduser("~/pw.txt")).read().strip()
# wp_url = "https://subcriticalorg.wordpress.com/xmlrpc.php"
# wp = xmlrpclib.ServerProxy(wp_url, use_datetime=True)

# create all the categories
INCLUDE_DRAFTS=1
date_fields = [ 'date_created',
                'date_created_gmt', 
                'post_date_gmt', 
                'post_date', 
                'post_date_gmt',
                'post_modified',
                'post_modified_gmt'
            ]
# create ALL the posts

def notify(msg):
    tmpl = "* %s\n"
    
    sys.stderr.write(tmpl % msg)
    sys.stderr.flush()

class Command(BaseCommand):
    """ Import blog posts from a remote blog """
    option_list = BaseCommand.option_list + (
            # make_option("-u", "--username", dest="username", default=[], metavar="username", help="User name for remote API endpoint"),
            make_option("-o", "--owner", dest="owner", metavar="ownername", help="Owner's Django user name"),
            make_option("-a", "--all", dest="all_blogs", action="store_true", help="Import all user blogs from API endpoint"),
            make_option("-x", "--api-endpoint", dest="api_endpoint", default=None, metavar="API endpoint", help="Direct URL for remote API endpoint"),
            make_option("-p", "--password", dest="password", default=[], help="Password for remote API connection"),
            make_option("-f", "--filename", dest="filename", metavar="json_filename", help="JSON file which contains dump blog data (created with --dump)"),
            make_option("-n", "--dry-run", dest="dry_run", action="store_true", help="Do not write anything to the database"),
            make_option("-d", "--dump", dest="dump", action="store_true", help="Write retrieved data to screen in JSON format"),
        )
    args = "[blog_url] [xblog_id] [-u username] [-p password]"
    help = """ Import blog posts from a remote blog """
    
    def handle(self, *args, **options):
        """
        imports a remote blog via the WordPress API
        """
        
        if options.get("api_endpoint", None):
            self.xmlrpc_import(args, options)
        elif options.get('filename'):
            self.json_import(args, options)
    
    def json_import(self, args, options):
        """
        Takes a json file of another xblog
        
        importantly, this script will try to sanitize it.
        
        Categories are imported as tags.
        Blog posts are assigned to an existing user, so make sure that user exists.
        
        New owner is passed using --owner=username
        
        """
        username = options.get('username')
        filename = options.get('filename')
        try:
            local_user = User.objects.get(username=options.get('owner'))
        except ObjectDoesNotExist:
            local_user = None

        print "Parsing %s for %s" % (username, filename)        
        # owner = None
        owner = local_user
        while not owner:
            try:
                owner = User.objects.get(username=username)
                print "Found %s" % owner
                
            except ObjectDoesNotExist:
                print "User name '%s' not found" % username
                print "Choose from one of the following:"
                for user in User.objects.all():
                    print "- %s" % user.username
                print "[q] Quit"
                username = raw_input('> ').strip()
                if username.lower()=='q':
                    sys.exit()
            
        print "Proceeding with %s (id=%s)" % (owner, owner.id)
        
        data = json.load(open(options.get("filename")))

        new_data = []
        bad_cats = [1, 4, 5] # specifically for YB; remove this
        for point in data:
    
            if point['model'] == 'xblog.category':
                continue
            if point['model'] == 'xblog.blog':
                pprint( point)
                point['fields']['owner'] = owner.id
        
            if point['model'] == 'xblog.author':
                pprint(point)
                print "Removing author record for %s" % point['fields']['fullname']
                data.remove(point)
                continue

            if point['model'] == 'xblog.post':
                for category in point['fields']['categories']:
                    if category in bad_cats:
                        continue
                # print point['fields']['author']
                point['fields']['author'] = owner.id

    
            # remove primary_category_name
            for old_field in ["primary_category_name", "categories"]:
                if old_field in point.get('fields').keys():
                    point['fields'].pop(old_field, None)
            new_data.append(point)
            
            # for point in new_data:
            #     print point
            
            json.dump(new_data, open('new_data.json','w'), indent=4)
            

    def xmlrpc_import(self, args, options ):
        """
        Sucks a blog over the internet using its XMLRPC protocol.
        """
        blog_url = args[0]
        xblog_id = args[1]
        
        if options.get("dump"):
            dry_run = True
            notify("Dumping %s to screen" % args[0])

        username = options.get("username") or raw_input("Username: ").strip()
        password = options.get("password") or getpass.getpass()
        
        wp_url =  options.get('api_endpoint')
        if not wp_url:
            notify("Couldn't find API link in page %s" % blog_url)
            notify("Please re-run with '-x url_to_api_endpoint'")
        # create the xmlrpc connection
        if wp_url[:4]!='http':
            # this is a relative URL
            notify("Normalizing URL")
            a = blog_url
            b = wp_url
            c = os.path.join(str(blog_url), str(wp_url))
            notify(c)
            
            notify(os.path.join(blog_url, wp_url))
            wp_url = os.path.join(blog_url, wp_url)
            notify(os.path.join(blog_url, wp_url))
            notify(wp_url)
            
        notify("Logging in at %s" % wp_url)
        wp = xmlrpclib.ServerProxy(wp_url, use_datetime=True, verbose=1)
        blogs = wp.wp.getUsersBlogs(username, password)
        
        notify("Got %d blogs" % len(blogs))
        
        active_blogs = []
        if len(blogs) > 1 and not options.get("all_blogs"):
            notify("Please enter the number of the blog you'd like to import:")
            counter = 1
            for blog in blogs:
                notify("[%d]: %s (ID:%s) " % (counter, blog["blogName"], blog["blogid"]))
                counter+=1
            notify("[a]: All blogs")
            choice = raw_input("Enter %s or 'a' for all blogs" % str(range(1,len(blogs)))).strip()
            if choice.lower() == 'a':
                notify("Grabbing all blogs from this user")
                active_blogs = blogs
            elif int(choice) in range(1,counter):
                notify("Grabbing blog %s" % choice)
                # print blogs
                # print blogs[0]
                # print blogs[1]
                # print '---'
                # print int(choice)-1
                # print blogs[0]
                active_blogs = blogs[int(choice)-1:int(choice)]
        else:
            active_blogs = blogs
        notify("Importing:")
        notify( ",".join(["'%s'" % blog['blogName'] for blog in active_blogs]))
        
        xblog = Blog.objects.get(id=int(xblog_id))
        # xblog_author = User.objects.all()[0] # FIXME: should probably try to get fancy and match email address or some'n
        owner_username = options.get("owner") or raw_input("Owner's username").strip()
        # print "|%s|" % owner_username
        xblog_author = User.objects.get(username=owner_username)
        categories = []
        posts = []
                
        for blog in active_blogs:
            # create a dictionary of categories
            categories = categories + wp.metaWeblog.getCategories(blog['blogid'], username, password)
            # create a list of posts
            notify("%d categories" % len(categories))
            # walk through the posts
            filter = {}
            filter['offset'] = 0
            all_posts = []
            counter = 0
            while True:
                filter['number'] = 10
                posts = wp.wp.getPosts(blog['blogid'], username, password, filter)
                # print "%d posts" % len(posts)
                if len(posts) == 0:
                    notify("Done!")
                    break
                for post in posts:
                    # convert the post date. 
                    all_posts.append(post)
                    counter = counter + 1
                    # print "[%3d] %s (%s) %s" % (counter, post['post_title'], post['post_date'], post['post_status']),
                    notify("Title: %s" % post['post_title'])
                    # notify("Date: %s" % post['post_date'])
                    # notify("Status: %s" % post['post_status'])
                    # notify("Author: %s" % post['post_author'])
                    # notify("Type: %s" % post['post_type'])
                    # notify(10 * "-")
                    # print post['post_content'] 
                filter['offset']+=len(posts)
            
            notify("Downloaded %d posts" % len(all_posts))
            

            # category_map = {}
            # for category in categories:
            #     category_map[category['categoryId']] = self.get_or_create_category(category, xblog)
                
            for post in all_posts:
                xblog_post = self.get_or_create_post(post, xblog)
                xblog_post.author = xblog_author
                if options.get('dry_run'):
                    notify("Not saving '%s'" % xblog_post.title)
                else:
                    xblog_post.save()
                    categories = self.get_post_categories(post, xblog)
                    for category in categories:
                        xblog_post.categories.add(category)
                    xblog_post.save()
    
    def get_or_create_post(self, post, xblog):
        # takes a wp.getPost object and set of categories, and creates 
        # an xblog post object from it
        
        # extract the relevant information from the post
        keys = post.keys()
        keys.sort()
        # pprint(keys)
        # try to find if this post has already been imported?
        try:
            xpost = Post.objects.get(guid=post['guid'])
            return xpost
        except ObjectDoesNotExist, e:
            pass
        
        xblog_post = {}
        xblog_post['pub_date'] = post['post_date_gmt']
        xblog_post['update_date'] = post['post_modified_gmt']
        xblog_post['create_date'] = post['post_date_gmt']
        xblog_post['enable_comments'] = False
        xblog_post['title'] = post['post_title']
        # # xblog_post['slug'] = 
        xblog_post['body'] = post['post_content']
        xblog_post['summary'] = post['post_excerpt']
        # xblog_post['categories'] = self.get_post_categories(post, xblog)
        # xblog_post['author'] = 
        xblog_post['status'] = post['post_status']
        xblog_post['guid'] = post['guid']
        xblog_post['blog'] = xblog
        # print xblog_post
        
        xpost = Post(**xblog_post)
        return xpost
    
    def get_or_create_xblog(self, xblog_id):
        # looks for a blog matching either the
        xblog = Blog.objects.get(id=xblog_id)
        return xblog
    
    def get_or_create_category(self, category, xblog):
        # looks for a category in XBlog, creates if it hasn't found one
        # print category
        # slug = self.get_category_slug(category)
        cat = {}
        print category.keys()
        try:
            xblog_category = Category.objects.get(title=category['description'])
        except ObjectDoesNotExist, e:
            cat['title'] = category['description']
            # cat['description'] = category['categoryDescription']
            cat['blog'] = xblog
            
            xblog_category = Category(**cat)
            xblog_category.save()
        return xblog_category
        
    def get_category_slug(self, category):
        # takes a wordpress category, and gets the slug from it
        html_url = category['htmlUrl']
        slug = html_url.split("/category/")[-1]
        slug = slug.replace("/",'')
        return slug
    
    def get_post_categories(self, post, xblog):
        # returns a list of categories for the given post
        category_list = []
        for term in  post['terms']:
            if term['taxonomy'] == 'category':
                mycat = {'description':term['name']}
                category_list.append(self.get_or_create_category(mycat, xblog))
        # print category_list
        return category_list


    def get_xmlrpc_url(self, page):
        """
        Gets the API endpoint as encoded in the blog's headers
        """
        # print "Opening %s..." % page
        data = urllib.urlopen(page).read()
        # print "Got %d bytes" % len(data)
        soup = BeautifulSoup.BeautifulSoup(data)
        xmlrpc_url = [link.get('href') for link in soup.findAll("link", rel="EditURI", type="application/rsd+xml")]
        if len(xmlrpc_url):
            # for now, just return the first one choose a proper link
            return xmlrpc_url[0]
        else:
            return None
        
    def get_posts(self, blog):
        # gets the posts for a particular remote blog 
        pass




def date_to_str(post):
    # print post.keys()
    #post = p.copy()
    for key in post.keys():
        # if it's a dict, recurse
        if type(post[key])==type({}):
            post[key] = date_to_str(post[key])
            
        if key in date_fields:
            # print dir(post[key])
            post[key] = str(post[key].isoformat())
            # print "* %s:%s (%s)" % (key, post[key], type(post[key]))
        else:
            # print "- |%s| not in date_fields" % key
            pass
    
    # for key in post.keys():
        # print "- %s:%s (%s)" % (key, post[key], type(post[key]))
        # if type(post[k]) != type(''):
        #     print "Non-string: %s\t%s" % (k, type(post[k]))
    
    
    # pprint( post)
    
    return post

def get_urls(post):
    """docstring for get_urls"""
    # this is going to return a list of URLs in the post
    # print post.keys()
    # print post['post_format']

    data = post['post_content']
    # print data
    soup = BeautifulSoup.BeautifulSoup(data)
    urls = {}
    urls['links'] = soup.findAll("a")
    urls['imgs'] = soup.findAll("img")
    return urls

if __name__ == '__main__':
    if sys.argv[-1][-4:]=="json":
        # passed a json file, why not...
        data = json.load(open(sys.argv[-1]))
    else:
    # get a list of posts
        blogs = wp.wp.getUsersBlogs(username, password)
        # list of dicts:
        # [{'url': 'https://subcriticalorg.wordpress.com/', 
        # 'isAdmin': True, 
        # 'blogid': '56586856', 
        # 'xmlrpc': 'https://subcriticalorg.wordpress.com/xmlrpc.php', 
        # 'blogName': 'Subcritical'}, 
        # {'url': 'https://cloudcritical.wordpress.com/', 
        # 'isAdmin': True, 
        # 'blogid': '65316393', 
        # 'xmlrpc': 'https://cloudcritical.wordpress.com/xmlrpc.php', 
        # 'blogName': 'Cloudcritical'}]

        # walk through the blogs...
        print "Got %d blogs" % len(blogs)



        for blog in blogs:
            print "Blog:", blog.get('blogName')
            categories =  wp.wp.getCategories(blog['blogid'], username, password)
            print "%d Categories" % len(categories)
            for category in categories:
                print "- %s [%s][%s]" % (category['categoryName'], category['htmlUrl'], category['categoryId'])
            filter = {}
            # if INCLUDE_DRAFTS:
            #     filter
            filter['offset'] = 0
            all_posts = []
            counter = 0
            while True:

                filter['number'] = 10
                posts = wp.wp.getPosts(blog['blogid'], username, password, filter)
                # print "%d posts" % len(posts)
                if len(posts) == 0:
                    print "Done!"
                    break
                for post in posts:
                    # convert the post date. 
                    all_posts.append(post)
                    counter = counter + 1
                    # print "[%3d] %s (%s) %s" % (counter, post['post_title'], post['post_date'], post['post_status']),
                    print "Title:", post['post_title']
                    print "Date:", post['post_date']
                    print "Status:", post['post_status']
                    print "Author", post['post_author']
                    print "Type:", post['post_type']
                    print 10 * "-"
                    # print post['post_content'] 
                filter['offset']+=len(posts)
        
        # dump posts to json file...
        # print all_posts[-1]
        
        print "Dumping to wp_data.json"
        data = [date_to_str(p) for p in all_posts]
        json.dump(date, open("wp_data.json", 'w'))


    for post in data:
        links = get_urls(post)
        print post['post_title']
        pprint(links)