from django.urls import path
from . import views
from django.http import JsonResponse
urlpatterns = [
    path('login/', views.client_login, name='client_login'),
    path('logout/', views.client_logout, name='client_logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('messages/', views.message_history, name='message_history'),
    path('rules/', views.rules, name='rules'),
    path('profile/', views.profile, name='profile'),
    path('contacts/', views.contacts, name='contacts'),
    path('broadcast/', views.broadcast, name='broadcast'),
    path('analytics/', views.analytics, name='analytics'),
    path('business-hours/', views.business_hours, name='business_hours'),
    path('products/', views.products, name='products'),
    path('message-templates/', views.message_templates, name='message_templates'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
   
    path('test-connection/', views.test_connection, name='test_connection'),
    path('update-token/', views.update_token, name='update_token'),
    path('test-connection/', views.test_connection, name='test_connection'),
    path('', views.landing, name='landing'),
    path('register/', views.register, name='register'),
    path('meta-setup/', views.meta_setup, name='meta_setup'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('pending/', views.pending, name='pending'),
    path('renew/', views.renew, name='renew'),
]