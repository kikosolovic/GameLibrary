# main/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.library_view, name='library'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('game/<int:appid>/', views.game_detail, name='game_detail'),
    path('logout/', views.logout_view, name='logout'),
    path("profile/", views.profile_view, name="profile"),
    path("filter-games-api/", views.filter_games_api, name="filter_games_api"),
    path("api/add-favorite/", views.add_favorite, name="add_favorite"),
    path("api/add-played/", views.add_played, name="add_played"),
    path("api/remove-from-favorite/", views.remove_from_favorites, name="remove_from_favorite"),
    path("api/remove-from-played/", views.remove_from_played, name="remove_from_played"),
    path('api/create-list/', views.create_list, name='create_list'),
    path('api/delete-list/', views.delete_list, name='delete_list'),
    path('api/edit-list/', views.edit_list, name='edit_list'),
    path('api/add-to-list/', views.add_to_list, name='add_to_list'),
    path('api/remove-from-list/', views.remove_from_list, name='remove_from_list'),
    path('api/get-user-lists/', views.get_user_lists, name='get_user_lists'),
    path('api/get-list-games/', views.get_list_games, name='get_list_games'),
    path('api/validate-list-field/', views.validate_list_field, name='validate_list_field'),
]