from django.contrib.auth.decorators import login_required
from .models import Comment, Post
from django.http import HttpResponse, JsonResponse
from .serializers import CommentSerializer, QuoteSerializer
from rest_framework.parsers import JSONParser
from rest_framework import generics, permissions
import requests

# class comment_detail(generics.ListCreateAPIView):
#     def get_serializer_class(self):
#         return CommentSerializer

#     def get_queryset(self):
#         if request.method == 'GET':
#             comments = Comment.objects.all()
#             serializer = CommentSerializer(comments, many=True)
#             return JsonResponse(serializer.data, safe=False)
#         print(self.request.user)
#         print('reeeeeeee')

def newComment(request, post_id):
    if request.method == 'POST':
        if request.user.is_authenticated:   
            data = JSONParser().parse(request)
            data['user'] = request.user.id
            data['post'] = post_id
            data['private'] = data.get('private')
            if data.get('quotee'):
                data["is_quote"] = True
            commentSerializer = CommentSerializer(data=data)
            if commentSerializer.is_valid():
                commentSerializer.save()
                if data.get('quotee'):
                    data['quoter'] = commentSerializer['pk'].value
                    quoteSerializer = QuoteSerializer(data=data)
                    if quoteSerializer.is_valid():
                        quoteSerializer.save()
                    return JsonResponse({"pk":commentSerializer['pk'].value}, status=200)
                return JsonResponse({"pk":commentSerializer['pk'].value}, status=200)
            return JsonResponse(commentSerializer.errors, status=400)
        return JsonResponse({'status':'false','message':'Not logged in'}, status=400)


def deleteComment(request, post_id):
    if request.method == 'DELETE':
        if request.user.is_authenticated:   
            data = JSONParser().parse(request)
            pk = data['pk']
            comment = Comment.objects.get(pk=pk, user=request.user, post=post_id) 
            comment.delete()
            return JsonResponse({'message': 'Comment was deleted successfully!'}, status=200)
    return JsonResponse({'message': 'Could not delete comment'}, status=400)



def getAddress(request, slug=""):
    data = JSONParser().parse(request)
    lng = data["lng"]
    lat = data["lat"]
    response = requests.get(f'https://api.mapbox.com/geocoding/v5/mapbox.places/{lng},{lat}.json?access_token=pk.eyJ1IjoiaXAzbHk1IiwiYSI6ImNrMGM1ZXg2bjB5cXgzYm53bHAyem5ldmkifQ.LM4FfJrdUcagfWYHuDUjww')
    return JsonResponse({'response': response.json()}, status=200)


