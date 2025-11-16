# main/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile routes
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    
    # Game routes
    path('game/<int:id>/', views.gamecard, name='gamecard'),
    
    # API/AJAX routes
    path('api/search/', views.search_api, name='search_api'),
    path('api/remove-from-favorites/', views.remove_from_favorites, name='remove_from_favorites'),
    path('api/remove-from-played/', views.remove_from_played, name='remove_from_played'),
]