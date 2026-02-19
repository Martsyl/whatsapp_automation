from django.urls import path
from . import views

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
]