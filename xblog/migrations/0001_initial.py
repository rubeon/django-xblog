# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.manager
import django.contrib.sites.managers
import django.utils.timezone
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fullname', models.CharField(max_length=100, blank=True)),
                ('url', models.URLField(blank=True)),
                ('avatar', models.ImageField(height_field=b'avatar_height', width_field=b'avatar_width', upload_to=b'avatars', blank=True)),
                ('about', models.TextField(blank=True)),
                ('avatar_height', models.IntegerField(null=True, blank=True)),
                ('avatar_width', models.IntegerField(null=True, blank=True)),
                ('remote_access_enabled', models.BooleanField(default=False)),
                ('remote_access_key', models.CharField(blank=True, max_length=100, validators=[django.core.validators.MinLengthValidator(8)])),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Blog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100, blank=True)),
                ('description', models.TextField(blank=True)),
                ('slug', models.SlugField(max_length=100)),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('site', models.ForeignKey(to='sites.Site')),
            ],
            managers=[
                ('objects', django.db.models.manager.Manager()),
                ('on_site', django.contrib.sites.managers.CurrentSiteManager()),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('description', models.CharField(max_length=100, blank=True)),
                ('slug', models.SlugField(max_length=100)),
                ('blog', models.ForeignKey(to='xblog.Blog')),
            ],
        ),
        migrations.CreateModel(
            name='Link',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(blank=True)),
                ('link_name', models.CharField(max_length=255, blank=True)),
                ('link_image', models.ImageField(height_field=b'link_image_height', width_field=b'link_image_width', upload_to=b'blog_uploads/links/', blank=True)),
                ('link_image_height', models.IntegerField(null=True, blank=True)),
                ('link_image_width', models.IntegerField(null=True, blank=True)),
                ('description', models.TextField(blank=True)),
                ('visible', models.BooleanField(default=True)),
                ('rss', models.URLField(blank=True)),
                ('blog', models.ForeignKey(to='xblog.Blog')),
            ],
        ),
        migrations.CreateModel(
            name='LinkCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, blank=True)),
                ('description', models.TextField(blank=True)),
                ('visible', models.BooleanField(default=True)),
                ('display_order', models.IntegerField(null=True, blank=True)),
                ('blog', models.ForeignKey(to='xblog.Blog')),
            ],
        ),
        migrations.CreateModel(
            name='Pingback',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('author_name', models.CharField(max_length=100, blank=True)),
                ('author_email', models.EmailField(max_length=254, blank=True)),
                ('title', models.CharField(max_length=255, blank=True)),
                ('body', models.TextField(blank=True)),
                ('is_public', models.BooleanField(default=False)),
                ('source_url', models.URLField(blank=True)),
                ('target_url', models.URLField(blank=True)),
                ('pub_date', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('mod_date', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pub_date', models.DateTimeField(default=django.utils.timezone.now, blank=True)),
                ('update_date', models.DateTimeField(auto_now=True)),
                ('create_date', models.DateTimeField(auto_now_add=True)),
                ('enable_comments', models.BooleanField(default=True)),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField(max_length=100)),
                ('guid', models.CharField(max_length=255, blank=True)),
                ('body', models.TextField(blank=True)),
                ('summary', models.TextField(blank=True)),
                ('status', models.CharField(default=b'Draft', max_length=32, null=True, blank=True, choices=[(b'draft', b'Draft'), (b'publish', b'Published'), (b'private', b'Private')])),
                ('text_filter', models.CharField(default=b'__default__', max_length=100, blank=True, choices=[(b'markdown', b'Markdown'), (b'html', b'HTML'), (b'convert linebreaks', b'Convert linebreaks')])),
                ('post_format', models.CharField(default=b'standard', max_length=100, blank=True, choices=[(b'standard', b'Standard'), (b'video', b'Video'), (b'status', b'Status')])),
                ('author', models.ForeignKey(to='xblog.Author')),
                ('blog', models.ForeignKey(to='xblog.Blog')),
                ('categories', models.ManyToManyField(to='xblog.Category')),
                ('primary_category_name', models.ForeignKey(related_name='primary_category_set', blank=True, to='xblog.Category', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100, blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='post',
            name='tags',
            field=models.ManyToManyField(to='xblog.Tag', blank=True),
        ),
        migrations.AddField(
            model_name='pingback',
            name='post',
            field=models.ForeignKey(to='xblog.Post'),
        ),
        migrations.AddField(
            model_name='link',
            name='category',
            field=models.ForeignKey(to='xblog.LinkCategory'),
        ),
    ]
