from .models import UserProfile
from django.contrib.auth.models import User

def add_profile_image_to_context(request):  
    if request.user.is_authenticated:
        user = request.user
        profile = UserProfile.objects.get(user=user)
        return {
            'loggedProfileImage': profile.image,
        }
    return ''