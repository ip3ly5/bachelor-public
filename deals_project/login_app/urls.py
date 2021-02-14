from django.urls import path
from . import views


app_name = 'login_app'

urlpatterns = [
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('request_password_reset/', views.request_password_reset, name='request_password_reset'),
    path('password_reset/', views.password_reset, name='password_reset'),
    path('register/', views.register, name='register'),
    path('edit/', views.edit_account, name='edit_account'),
    path('delete_account/', views.delete_account, name='delete_account'),
    path('email_change/', views.email_change, name='email_change'),
    path('password_change/', views.password_change, name='password_change'),
]
