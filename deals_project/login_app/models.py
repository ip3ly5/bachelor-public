from django.db import models
from django.contrib.auth.models import User
from secrets import token_urlsafe
from django.db.models.signals import post_save



class PasswordResetRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=43, default=token_urlsafe)
    created_timestamp = models.DateTimeField(auto_now_add=True)
    updated_timestamp = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user} - {self.created_timestamp} - {self.updated_timestamp} - {self.token}'

#def send_reset_email(sender, instance, *args, **kwargs):
#    instance.user.email
#    user = User.objects.get(id=instance.user.id)

#post_save.connect(send_reset_email, sender=PasswordResetRequest)
