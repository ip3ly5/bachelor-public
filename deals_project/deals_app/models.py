from django.contrib.auth.models import User
from django.db import models
from datetime import datetime
from django.utils import timezone
from django.db.models.signals import pre_save, post_save, post_delete
import channels.layers
from asgiref.sync import async_to_sync
from django.dispatch import receiver
import math
import json
import string
import django.dispatch

from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=30)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("deals_app:post", kwargs={"slug": self.slug})

class Postcode(models.Model):
    code = models.IntegerField()
    text = models.CharField(max_length=200)

    def __str__(self):
        return '{} - {}'.format(self.code, self.text)

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=80, null=True)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=200)
    address_line_1 = models.CharField(max_length=200)
    address_line_2 = models.CharField(max_length=200)
    postcode = models.ForeignKey(Postcode, on_delete=models.PROTECT)
    frozen_to = models.ForeignKey(User, related_name="frozen_to", on_delete=models.PROTECT, null=True)
    frozen_read = models.BooleanField(default=False)
    thumbnail = models.ImageField(upload_to='images/')
    date_created = models.DateTimeField(auto_now_add=True)
    latest_update = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True)
    staff_picked = models.BooleanField(default=False)
    expiration_date = models.DateField()
    lng = models.FloatField()
    lat = models.FloatField()
    region_code = models.IntegerField()

    def when_published(self):
        now = timezone.now()
        
        diff= now - self.date_created

        if diff.days == 0 and diff.seconds >= 0 and diff.seconds < 60:
            seconds= diff.seconds
            if seconds == 1:
                return str(seconds) +  "second ago"
            else:
                return str(seconds) + " seconds ago"

        if diff.days == 0 and diff.seconds >= 60 and diff.seconds < 3600:
            minutes= math.floor(diff.seconds/60)
            if minutes == 1:
                return str(minutes) + " minute ago"
            else:
                return str(minutes) + " minutes ago"

        if diff.days == 0 and diff.seconds >= 3600 and diff.seconds < 86400:
            hours= math.floor(diff.seconds/3600)
            if hours == 1:
                return str(hours) + " hour ago"
            else:
                return str(hours) + " hours ago"

        if diff.days >= 1 and diff.days < 30:
            days= diff.days
            if days == 1:
                return str(days) + " day ago"
            else:
                return str(days) + " days ago"

        if diff.days >= 30 and diff.days < 365:
            months= math.floor(diff.days/30)
            if months == 1:
                return str(months) + " month ago"
            else:
                return str(months) + " months ago"

        if diff.days >= 365:
            years= math.floor(diff.days/365)
            if years == 1:
                return str(years) + " year ago"
            else:
                return str(years) + " years ago"

    # Override save method for field specific only (frozen_to) logic for notification consumer
    # custom signal needed for custom (old value) arg
    def save(self, *args, **kwargs):
        old = type(self).objects.get(pk=self.pk) if self.pk else None
        post = super(Post, self).save(*args, **kwargs)
        if old and old.frozen_to != self.frozen_to: # Field has changed (and post is not new)
            #when = self.when_published()
            new_frozen_to.send(sender=self, old=old.frozen_to)

    def __str__(self):
        return self.title

class PostImage(models.Model):
    post = models.ForeignKey(Post, default=None, on_delete=models.CASCADE)
    image = models.ImageField(upload_to = 'images/')

    def __str__(self):
        return self.post.title

class CancelledFrozenTo(models.Model):
    post = models.ForeignKey(Post,on_delete=models.CASCADE, related_name='cancelledPoster')    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cancelledUser')
    time = models.DateTimeField(auto_now=True)
    frozen_read = models.BooleanField(default=False)

    class Meta:
        unique_together = [['post', 'user', 'time']]

    def __str__(self):
        return '{} was cancelled to collect {}'.format(self.user, self.post)

class Comment(models.Model):
    post = models.ForeignKey(Post,on_delete=models.CASCADE,related_name='comments')    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.CharField(max_length=200)
    date_created = models.DateTimeField(auto_now_add=True)
    read_by_author = models.BooleanField(default=False)
    is_quote = models.BooleanField(default=False)
    private = models.BooleanField(default=False)

    class Meta:
        ordering = ['date_created']

    def __str__(self):
        return 'Comment {} by {}'.format(self.body, self.user)

class Quote(models.Model):
    quoter = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='quoter')
    quotee = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='quotee')

    class Meta:
        unique_together = [['quoter', 'quotee']]

    def __str__(self):
        return '{} is quoting {}'.format(self.quoter, self.quotee)


def reformat_category(instance, *args, **kwargs):
    instance.name = string.capwords(instance.name)

def create_slug(instance, new_slug=None):
    slug = slugify(instance.title)
    if new_slug is not None:
        slug = new_slug
    qs = Post.objects.filter(slug=slug).order_by("-id")
    exists = qs.exists()
    if exists:
        new_slug = "%s-%s" %(slug, qs.first().id)
        return create_slug(instance, new_slug=new_slug)
    return slug

def pre_save_slug_receiver(sender, instance, *args, **kwargs):
    # if already exist  
    old = Post.objects.filter(id=instance.id)
    # update
    if old.exists():
        old = old.first()
        if old.title != instance.title:
            instance.slug = create_slug(instance)  
    # create
    else:
        instance.slug = create_slug(instance)  

pre_save.connect(pre_save_slug_receiver, sender=Post)
pre_save.connect(reformat_category, sender=Category)

# custom signal for changing frozen_to state
new_frozen_to = django.dispatch.Signal()
