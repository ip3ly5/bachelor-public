from rest_framework import serializers
from .models import Comment, Quote

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment    
        fields = ['pk', 'user', 'post', 'body', 'date_created', 'is_quote', 'private']

class QuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quote  
        fields = ['quoter', 'quotee']