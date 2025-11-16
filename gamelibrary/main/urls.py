# main/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.library_view, name='library'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('game/<int:id>/', views.gamecard, name='gamecard'),  # static for now
    path('logout/',views.logout_view, name='logout'),
]