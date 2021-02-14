from django.contrib import admin

from .models import UserProfile, Subscription, Subscription_Email, Vote


# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Subscription)
admin.site.register(Subscription_Email)
admin.site.register(Vote)