#!/usr/bin/env python
# encoding: utf-8
"""
gazette.py

Created by Eric Williams on 2007-03-08.
"""

import sys
import os
# init django stuff
SITE_DIR = os.path.abspath(os.path.split(__file__)[0]+'/..')
os.environ['DJANGO_SETTINGS_MODULE']= 'settings'
sys.path.insert(0,SITE_DIR)
sys.path.insert(0,os.path.join(SITE_DIR,'..'))
sys.path.insert(0,os.path.join(SITE_DIR,'..','..'))

import urlparse
from django.conf import settings
try:
    from django.contrib.auth import get_user_model
    User = settings.AUTH_USER_MODEL
except ImportError:
    from django.contrib.auth.models import User 

from xblog.models import Tag, Post, Blog, Author, Category
from xmlrpc_views import public
import xmlrpclib
import urllib
import re
#print __file__
#print SITE_DIR
from django.conf import settings
import time
import datetime
import os

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer 
from reportlab.lib.styles import getSampleStyleSheet 
from reportlab.lib import styles
from reportlab.rl_config import defaultPageSize 
from reportlab.lib.units import inch 

def myFirstPage(canvas, doc): 
    canvas.saveState() 
    canvas.setFont('Times-Bold',16) 
    canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT-108, Title) 
    canvas.setFont('Times-Roman',9) 
    canvas.drawString(inch, 0.75 * inch, "First Page / %s" % pageinfo) 
    canvas.restoreState() 

def myLaterPages(canvas, doc): 
    canvas.saveState() 
    canvas.setFont('Times-Roman',9) 
    canvas.drawString(inch, 0.75 * inch, "Page %d %s" % (doc.page, pageinfo)) 
    canvas.restoreState() 

# create the document
def go(): 
    doc = SimpleDocTemplate("/Users/eric/Desktop/phello.pdf") 
    Story = [Spacer(1,2*inch)] 
    styles = getSampleStyleSheet()
    style = styles["Normal"] 
    for i in range(100): 
        bogustext = ("This is Paragraph number %s.  " % i) *20 
        p = Paragraph(bogustext, style) 
        Story.append(p) 
        Story.append(Spacer(1,0.2*inch)) 
    doc.build(Story, onFirstPage=myFirstPage, onLaterPages=myLaterPages) 

# go()