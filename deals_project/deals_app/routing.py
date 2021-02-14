# consumer route

from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    # re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/status/', consumers.UserStatusConsumer.as_asgi()),
    re_path(r'ws/notifier/', consumers.NotificationConsumer.as_asgi()),
    re_path(r'ws/postList/', consumers.LivePostConsumer.as_asgi()),
    re_path(r'ws/search/', consumers.SearchConsumer.as_asgi()),
]
