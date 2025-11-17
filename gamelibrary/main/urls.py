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
    path("u/<str:username>/", views.public_profile_view, name="public_profile"),
    path("edit-profile/", views.edit_profile_view, name="edit_profile"),
    path("filter-games-api/", views.filter_games_api, name="filter_games_api"),
    path("api/add-favorite/", views.add_favorite, name="add_favorite"),
    path("api/add-played/", views.add_played, name="add_played"),
    path("api/add-wishlist/", views.add_wishlist, name="add_wishlist"),
    path("api/remove-from-favorite/", views.remove_from_favorites, name="remove_from_favorite"),
    path("api/remove-from-played/", views.remove_from_played, name="remove_from_played"),
    path("api/remove-from-wishlist/", views.remove_from_wishlist, name="remove_from_wishlist"),
    path("api/people-search/", views.people_search_api, name="people_search_api"),
    path("api/friend-request/", views.send_friend_request, name="send_friend_request"),
    path("api/friend-request/accept/", views.accept_friend_request, name="accept_friend_request"),
    path("api/friend-request/decline/", views.decline_friend_request, name="decline_friend_request"),
    path("api/friends/", views.friends_api, name="friends_api"),
    path("api/friend-requests/", views.friend_requests_api, name="friend_requests_api"),
]
