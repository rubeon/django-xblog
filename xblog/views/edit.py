#!/usr/bin/env python
# encoding: utf-8
"""
edit.py

Created by Eric Williams on 2007-04-09.
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, permission_required
from django.template import RequestContext, Context, loader
from django.shortcuts import render, redirect
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from django.contrib import messages
from django.forms.models import inlineformset_factory
from django.conf import settings
try:
    from django.contrib.auth import get_user_model
    User = settings.AUTH_USER_MODEL
except ImportError:
    from django.contrib.auth.models import User


# from xcomments.models import FreeComment
from django import forms
from django.http import HttpResponseRedirect, HttpResponse, Http404
from xblog.models import Post, PostForm, Blog, FILTERS

import logging
logger = logging.getLogger(__name__)

#    class PublicFreeCommentForm(newforms.Form):
#        person_name = newforms.CharField(label="Your Name")
#        person_url = newforms.CharField(label="Web Site", required=False)
#        person_email = newforms.EmailField(label="Email Address")
#        comment = newforms.CharField(widget=newforms.Textarea(attrs={'rows':10, 'cols':50}, ) )
#        options = newforms.CharField(widget=newforms.HiddenInput)
#        target = newforms.CharField(widget=newforms.HiddenInput)
#        gonzo = newforms.CharField(widget=newforms.HiddenInput)
#


@login_required
def content_list(request, **kwargs):
    """
    This provides a list of published content...
    """
    logger.debug("content_view entered")
    # get a post_list by current user
    site = get_current_site(request)
    post_list = Post.objects.filter(author=request.user.author).order_by('-pub_date')
    # logger.debug("post_list: %s" % str(post_list))

    c = RequestContext(request, {'post_list': post_list, })
    t = loader.get_template("xblog/content_list.html")

    return HttpResponse(t.render(c))


@permission_required("xblog.change_post")
def edit_post_inline(request, **kwargs):
    """
    This provides ajax queries with an edit form...
    """
    logger.debug("edit_post_inline entered")
    p = Post.objects.get(slug=kwargs['slug'])
    # if request.POST:

@login_required
def preview_post(request, **kwargs):
    """
    takes the go-get-me data from the URL, and returns the formatted version of it for previewin'
    """
    logger.debug("preview_post called")
    logger.debug(kwargs)

    p = Post.objects.get(slug=kwargs['slug'])

    logger.info("preview_post showing %s" % p)
    # data = p.get_full_body()

    # put the post into a context for the template render...
    logger.debug("opening template")
    c = RequestContext(request, {'object':p})
    t = loader.get_template('includes/post_template.txt')

    return HttpResponse(t.render(c))


@permission_required("xblog.change_post")
def set_publish(request, **kwargs):
    logger.debug("set_published entered")
    # logger.debug(request.GET)
    if request.GET.has_key('value'):
        new_status = request.GET['value']
        logger.debug("set_published: %s" % new_status )
        p = Post.objects.get(slug=kwargs['slug'])
        p.status = new_status
        p.save()
        return HttpResponse("<p>%s saved</p>" % p.title)
    else:
        logger.warn("Invalid set_status: %s" % request.GET['value'])
        return "<p>Invalid request</p>"

# @login_required
@permission_required("xblog.change_post")
def edit_post(request, **kwargs):
    logger.debug("edit_post:")
    # PostForm = forms.form_for_model(Post)
    p = Post.objects.get(slug=kwargs['slug'])

    if request.POST:

        logger.info("Got POST...")
        form = PostForm(request.POST, instance=p)

        if form.is_valid():
            logger.info("Form is valid, saving...")
            # logger.debug(form)
            model_instance = form.save(commit=False)
            model_instance.update_date = timezone.now()
            model_instance.save()

            # messages.add_message(request, messages.INFO, "Saved '%s'" % model_instance.title)
            messages.info(request, "Saved '%s'" % model_instance.title)
            # return HttpResponseRedirect(model_instance.get_absolute_url())
            # c = RequestContext(request)
            # c['form']=form
            # return HttpResponseRedirect(t.render(c))
            # next line is required to save the many-to-many relations
            form.save_m2m()

        else:
            logger.warn("Form data invalid; showing again")
            logger.warn("Form errors: %s" % form.errors)
            messages.error(request, form.errors)
            # logger.debug(form)
        c = RequestContext(request, {'form': form})
        t = loader.get_template('xblog/edit_post.html')
        # messages.add_message(request, messages.ERROR, form.errors)
        return HttpResponse(t.render(c))

    else:
        # f = forms.form_for_instance(p,form=PostForm)()

        form = PostForm(instance=p)
        c = RequestContext(request, {'form':form})
        t = loader.get_template('xblog/edit_post.html')
        return HttpResponse(t.render(c))

def stats(request, **kwargs) :
    """
    renders the post_stats.txt table
    """
    p = Post.objects.get(slug=kwargs['slug'])
    t = loader.get_template('includes/post_stats.txt')
    c = {}
    c['readability'] = p.get_readability()
    c = RequestContext(request, c)

    return HttpResponse(t.render(c))
