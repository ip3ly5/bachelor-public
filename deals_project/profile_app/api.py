from django.contrib.auth.decorators import login_required
from .models import UserProfile, Vote
from django.http import HttpResponse, JsonResponse
from .serializers import VoteSerializer
from rest_framework.parsers import JSONParser
from rest_framework import generics, permissions

def voteProfile(request, profile_id):
    if request.method == "POST":
        data = JSONParser().parse(request)
        if Vote.objects.filter(user=request.user, profile=profile_id).exists():
            vote = Vote.objects.get(user=request.user, profile=profile_id)
            vote.vote = int(data['vote'])
            vote.save()
            profile = UserProfile.objects.get(pk=profile_id)
            count = -profile.voteForUser.filter(vote=-1).count() + profile.voteForUser.filter(vote=1).count()
            upCount = profile.voteForUser.filter(vote=1).count()
            downCount = profile.voteForUser.filter(vote=-1).count()
            return JsonResponse({'message': 'vote updated', 'count':count, 'upCount': upCount, 'downCount': downCount}, status=200)
        else: 
            data['user'] = request.user.id
            data['profile'] = profile_id

            voteSerializer = VoteSerializer(data=data)
            if voteSerializer.is_valid():
                voteSerializer.save()
                profile = UserProfile.objects.get(pk=profile_id)
                count = -profile.voteForUser.filter(vote=-1).count() + profile.voteForUser.filter(vote=1).count()        
                upCount = profile.voteForUser.filter(vote=1).count()
                downCount = profile.voteForUser.filter(vote=-1).count()
                return JsonResponse({'message': 'vote successful', 'count':count, 'upCount': upCount, 'downCount': downCount}, status=200)
            return JsonResponse(voteSerializer.errors, status=400)

    if request.method == "DELETE":
        if Vote.objects.filter(user=request.user, profile=profile_id).exists():
            vote = Vote.objects.get(user=request.user, profile=profile_id)
            vote.delete()
            profile = UserProfile.objects.get(pk=profile_id)
            count = -profile.voteForUser.filter(vote=-1).count() + profile.voteForUser.filter(vote=1).count()
            upCount = profile.voteForUser.filter(vote=1).count()
            downCount = profile.voteForUser.filter(vote=-1).count()

            return JsonResponse({'message': 'vote deleted', 'count': count, 'upCount': upCount, 'downCount': downCount}, status=200)
        return JsonResponse({'message': 'vote does not exist'}, status=400)
