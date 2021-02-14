from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from deals_app.models import Post
from .models import UserProfile, Subscription, Subscription_Email
from .serializers import VoteSerializer
from django.core import serializers
from django.db.models.signals import post_save
from django.dispatch import receiver
from . messaging import email_message
from .utils.images import get_image_from_data_url

import django_rq
import json


# Create your views here.
def profile(request, user_id):

    user = get_object_or_404(User, pk=user_id)
    posts = Post.objects.filter(user=user_id)
    subscriptions = Subscription.objects.filter(subscribee=user_id).count()

    if request.user.is_authenticated:
        if user.profile.voteForUser.filter(user=request.user).exists():
            user.profile.voteStatus = user.profile.voteForUser.get(user=request.user).vote

    if request.user.is_authenticated:
        subscriptionStatus = Subscription.objects.filter(subscriber=request.user, subscribee=user_id).count()
        return render(request, 'profile_app/profile.html', {'profileUser':user, 'posts':posts, 'subscribers':subscriptions, 'subscriptionStatus': subscriptionStatus})

    return render(request, 'profile_app/profile.html', {'profileUser':user, 'posts':posts, 'subscribers':subscriptions})


@login_required
def edit_profile(request):
    user = request.user
    if request.method == "POST":
        profile = UserProfile.objects.get(user=user)
        if "summary" in request.POST:
            summary = request.POST["summary"]
            profile.summary = summary
        if "file" in request.POST:
            fileJson = json.loads(request.POST["file"])
            profile.image = get_image_from_data_url(fileJson["data"])[0]
            # myfile = request.POST["filepond"]
            # fs = FileSystemStorage()
            # filename = fs.save(myfile.name, myfile)
            # uploaded_file_url = fs.url(filename)
            # profile.image = filename
        profile.save()

    return render(request, 'profile_app/edit.html', {'profileUser':user})

def subscription_list(request):
    if request.method == 'GET':
        subscriptions = Subscription.objects.all()
        serializer = SubscriptionSerializer(subscriptions, many=True)
        return JsonResponse(serializer.data, safe=False)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = SubscriptionSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)

        return JsonResponse(serializer.errors, status=400)

@login_required
def subscription_detail(request, user_id):
    if request.method == 'DELETE':
        user = request.user.id
        subscription = Subscription.objects.get(subscriber=user, subscribee=user_id)
        subscription.delete()
        return JsonResponse(subscription, status=201, safe=False)

@receiver(post_save, sender=Post)
def subscription_build_email(sender, **kwargs):
    if kwargs['created'] is True:
        post = kwargs['instance']
        uploader = kwargs['instance'].user
        subscribers = Subscription.objects.filter(subscribee=uploader)

        for subscriber in subscribers:
            subscription_email = Subscription_Email()
            subscription_email.user = subscriber.subscriber
            subscription_email.post = post
            subscription_email.save()

            subscriber_posts = Subscription_Email.objects.filter(user=subscriber.subscriber)
            subscriber_posts_serialized = []

            for obj in subscriber_posts:
                subscriber_posts_serialized.append({"name":obj.post.name, "summary":obj.post.summary})

            if subscriber_posts.count() > 2:
                django_rq.enqueue(email_message, {
                    'email': subscriber.subscriber.email,
                    'posts': subscriber_posts_serialized
                })
                subscriber_posts.delete()
