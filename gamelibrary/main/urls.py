# main/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.library_view, name='library'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('game/<int:appid>/', views.game_detail, name='game_detail'),
    path('logout/',views.logout_view, name='logout'),
    path("filter-games-api/", views.filter_games_api, name="filter_games_api"),
]