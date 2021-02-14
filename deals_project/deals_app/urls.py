from django.urls import path, include
from . import views
from .api import newComment, deleteComment, getAddress


app_name = 'deals_app'

urlpatterns = [
    path('', views.base, name='base'),
    path('browse/<slug:base>/', views.base, name='base'),
    path('browse/<slug:base>/<slug:order>/', views.base, name='base'),
    path('browse/<slug:base>/<slug:order>/<int:page>/', views.base, name='base'),
    path('browse/<slug:base>/<slug:order>/<int:page>/<int:location>/', views.base, name='base'),
    path('browse/<slug:base>/<slug:order>/<int:page>/<int:location>/<slug:live>', views.base, name='base'),
    path('post/<slug:slug>', views.post, name='post'),
    path('add', views.addPost, name='addPost'),
    path('post/<int:post_id>/comment', newComment, name='newComment'),
    path('get_address/', getAddress, name='getAddress'),
    path('post/<slug:slug>/get_address/', getAddress, name='getAddress'),
    path('post/<int:post_id>/comment/delete', deleteComment, name='deleteComment'),
    path('post/<slug:slug>/delete', views.delete, name='delete'),
    path('post/<slug:slug>/edit', views.edit, name='edit')
]