# main/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('api/search/', views.search_api, name='search_api'),
    path('game/<int:id>/', views.gamecard, name='gamecard'),
    path('logout/', views.logout_view, name='logout'),
]