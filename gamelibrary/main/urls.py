# main/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.library_view, name='library'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('game/<int:appid>/', views.game_detail, name='game_detail'),
    path('logout/',views.logout_view, name='logout'),
    path("profile/", views.profile_view, name="profile"),
    path("edit-profile/", views.edit_profile_view, name="edit_profile"),
    path("filter-games-api/", views.filter_games_api, name="filter_games_api"),
    path("api/add-favorite/", views.add_favorite, name="add_favorite"),
    path("api/add-played/", views.add_played, name="add_played"),
    path("api/remove-from-favorite/", views.remove_from_favorites, name="remove_from_favorite"),
    path("api/remove-from-played/", views.remove_from_played, name="remove_from_played"),
    path("api/add-game", views.add_game, name="add_game"),
    path("api/get-fav-games", views.get_fav_games, name="get_favourite_games"),
    path("api/update-price", views.update_price, name="update_price"),
]