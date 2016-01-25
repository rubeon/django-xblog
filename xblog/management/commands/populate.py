from django.core.management.base import BaseCommand, CommandError
from xblog.models import Post, Category

class Command(BaseCommand):
    args = '<num_posts>'
    help = 'Populate server with test data'
    
    def handle(self, *args, **options):
        for arg in args:
            print "ARG:", arg
        
        print "Options:", options
