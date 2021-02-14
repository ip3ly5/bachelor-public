import json
import channels.layers
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer, JsonWebsocketConsumer
from .models import Post, Comment, Quote, new_frozen_to, CancelledFrozenTo
from django.contrib.auth.models import User
from django.db.models import signals
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from django.core import serializers
from django.core.cache import cache


# todo: 
# expand to "my watched" (activity categories/posts/etc)
# try-except db calls?
# signal for updates on status=read (replace front end dummy system to keep integrity+sync devices)
# fix user ref from id to name
# (potential front end) reference post, date
# seperate into own app?
# delete signal for if a post get deleted

class NotificationConsumer(JsonWebsocketConsumer):
    def connect(self):
        personal_group = 'personal_group_'+str(self.scope["user"].id)
        async_to_sync(self.channel_layer.group_add)(personal_group, self.channel_name)
        comment_payload = []
        frozen_to_payload = []

        def loop_handler(query_set, otype, payload):
            for obj in query_set:
                data = {}
                if otype == 'comment':
                    data['is_quote'] = False
                if otype == 'quote':
                    obj = obj.quoter
                    data['is_quote'] = True
                if otype == 'post':
                    data['status'] = 'accepted'
                if otype == 'cancelled':
                    obj = obj.post
                    data['status'] = 'cancelled'
                if otype == 'comment' or otype == 'quote':
                    body = obj.body
                    slug = obj.post.slug
                    data['post'] = obj.post.title
                if otype == 'post' or otype == 'cancelled':
                    body = obj.title
                    slug = obj.slug

                data['id'] = obj.id
                data['body'] = body
                data['user'] = obj.user.username
                data['slug'] = slug

                if payload == []:
                    payload.append(data)
                else:
                    # comment may already be in payload from quotes
                    original = next((item for item in payload if item['id'] == obj.id), None)
                    if original != None:
                        print('62 already in', original)
                        # if frozen status change
                        if data['status']:
                            print('65 status change attempt', data['id'], data['status'])
                            original['status'] = data['status']
                    else:
                        payload.append(data)

        # all unread replies from own comments
        unread_from_replies = Quote.objects.exclude(quoter__user=self.scope["user"]).filter(quotee__user=self.scope["user"]).filter(quoter__read_by_author=False).order_by('quotee__date_created')
        loop_handler(unread_from_replies, 'quote', comment_payload)

        # all unread comments from own post
        unread_from_OP = Comment.objects.exclude(user=self.scope["user"]).filter(post__user=self.scope["user"]).filter(read_by_author=False).order_by('date_created')
        loop_handler(unread_from_OP, 'comment', comment_payload)

        # all cancelled 
        unread_cancelled = CancelledFrozenTo.objects.filter(user=self.scope["user"]).filter(frozen_read=False).order_by('time')
        loop_handler(unread_cancelled, 'cancelled', frozen_to_payload)

        # all frozen_to
        unread_collections = Post.objects.filter(frozen_to=self.scope["user"]).filter(frozen_read=False).order_by('latest_update')
        loop_handler(unread_collections, 'post', frozen_to_payload)

        
        # no need to use group for initial on-load payload
        async_to_sync(self.channel_layer.send)(self.channel_name, {
            'type': 'events.alarm',
            'data': {
                'type': 'comment',
                'multi': True,
                'data': comment_payload,
            }})

        # todo: dry
        async_to_sync(self.channel_layer.send)(self.channel_name, {
            'type': 'events.alarm',
            'data': {
                'type': 'frozen_status',
                'multi': True,
                'data': frozen_to_payload,
            }})

        self.accept()

    def disconnect(self, close_code):
        personal_group = 'personal_group_'+str(self.scope["user"].id)
        async_to_sync(self.channel_layer.group_discard)(
            personal_group,
            self.channel_name
        )
        self.close()

    def receive_json(self, content, **kwargs):
        #print(f"Received event: {content}")
        try:
            if content['type'] == 'comment':
                comment = get_object_or_404(Comment, id=content['id'])
                comment.read_by_author = True
                comment.save()
            elif content['status'] == 'cancelled':
                cancelled = get_object_or_404(CancelledFrozenTo, user=self.scope["user"], post__id=content['id'])
                cancelled.frozen_read = True
                cancelled.save()
            else:
                accepted = get_object_or_404(Post, id=content['id'])
                accepted.frozen_read = True
                accepted.save()
        except:
            print('error updating notification read status')

    def events_alarm(self, event):
        self.send_json(event['data'])

    @staticmethod # avoid requiring self arg for signal method
    @receiver(signals.post_save, sender=Comment)
    @receiver(signals.post_save, sender=Quote)
    #@receiver(signals.post_delete, sender=Comment)
    def comment_signal(sender, instance, **kwargs):
        layer = channels.layers.get_channel_layer()
        # we cannot access self or request.user, so we need to examine the incoming comment and send accordingly
        # if comment on user's post // send to the group of comment-post-user
        # group is useful here for sync if user is connected on multiple devices
        
        def typeHandler(comment, target):
            payload = [{
                "id": comment.id,
                "body": comment.body,
                "user": comment.user.username,
                "is_quote": comment.is_quote,
                "slug": comment.post.slug,
                "post": comment.post.title
            }]

            async_to_sync(layer.group_send)('personal_group_'+str(target), {
                'type': 'events.alarm',
                'data': {
                    'type': 'comment',
                    'multi': False,
                    'data': payload
                }
            })

        if sender == Quote and instance.quoter.read_by_author == False and instance.quoter.user != instance.quotee.user:
            typeHandler(instance.quoter, instance.quotee.user.id)
        if sender == Comment and instance.is_quote == False and instance.read_by_author == False and instance.user != instance.post.user:
            typeHandler(instance, instance.post.user.id)

    # custom signal needed for custom (old value) arg
    @receiver(new_frozen_to)
    def new_frozen_signal(sender, old, **kwargs):
        layer = channels.layers.get_channel_layer()

        # if frozen to u changes (also notify cancelled)
        # unlike in init load, we get all occurences live to see latest status
        def statusHandler(status, target):
            payload = [{
                "id": sender.id,
                "body": sender.title,
                "user": sender.user.username,
                "slug": sender.slug,
                "status": status,
            }]

            async_to_sync(layer.group_send)('personal_group_'+str(target), {
                'type': 'events.alarm',
                'data': {
                    'type': 'frozen_status',
                    'multi': False,
                    'data': payload
                }
            })

        if sender.frozen_to != None:
            statusHandler('accepted', sender.frozen_to.id)

        if old != None:
            statusHandler('cancelled', old.id)



class LivePostConsumer(JsonWebsocketConsumer):
    def connect(self):
        async_to_sync(self.channel_layer.group_add)('post_list_group', self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            'post_list_group',
            self.channel_name
        )
        self.close()

    def events_alarm(self, event):
        self.send_json(event['data'])

    @staticmethod
    @receiver(signals.post_save, sender=Post)
    # pre save for created logic?
    # slug/category/postcode logic for categories?
    def post_signal(sender, instance, **kwargs):
        layer = channels.layers.get_channel_layer()
        async_to_sync(layer.group_send)('post_list_group', {
            'type': 'events.alarm',
            'data': {
                "data": serializers.serialize("json", [instance]),
                "username": instance.user.username,
                "commentCount": instance.comments.count(),
                "areaCode": instance.postcode.code,
                "areaName": instance.postcode.text,
                "category": instance.category.name
            }
        })


class SearchConsumer(JsonWebsocketConsumer):
    # echo consumer
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        self.close()

    def receive_json(self, content, **kwargs):
        print(f"Received event: {content}")
        
        # low-level cache(query only) with redis to enable keystroke search
        if cache.get("all_posts"):
            print('all posts query loaded from cache')
        else:
            all_posts = Post.objects.all()
            cache.set("all_posts", all_posts, 30)
            print('query cache expired')

        payload = []
        for post in cache.get("all_posts"):
            if content["search"].lower() in post.title.lower():
                payload.append({
                   "data":serializers.serialize("json", [post]), 
                   "username":post.user.username, 
                    "commentCount": post.comments.count(),
                    "areaCode": post.postcode.code,
                    "category": post.category.name
                })
        print(payload)
        self.send_json(payload)


# (NOT WORKING ATM)
# todo:
# broadcast/group
# hook up to user
# convert to async
class UserStatusConsumer(WebsocketConsumer):

    def connect(self):  
        #if self.scope["user"].is_anonymous:
        #if self.scope["user"].is_authenticated:
        # userPosts = Post.objects.filter(user__id=self.scope["user"].id)
        async_to_sync(self.channel_layer.group_add)("statusTracker", self.channel_name)
        # anyone con to socket get user list

        async_to_sync(self.channel_layer.group_send)(
            "statusTracker",
            {
                "type": "user.handler",
                "message": str(self.scope["user"].id),
            },
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)("statusTracker", self.channel_name)

    # on recive data from client
    def receive(self, text_data):
        #self.send(text_data=self.scope["user"] + ": " + text_data)
        print(text_data)
        #text_data_json = json.loads(text_data)
        #message = text_data_json['message']

    def user_handler(self, event):
        print("e", event)
        self.send(event['message'])

class LiveCommentConsumer(WebsocketConsumer):
    pass