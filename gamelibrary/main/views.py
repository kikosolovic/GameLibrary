from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import requests
import json

from .forms import RegistrationForm, LoginForm
from .models import Users, Game


# Fetch SteamSpy API data
def fetch_steamspy(appid):
    url = f"https://steamspy.com/api.php?request=appdetails&appid={appid}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None


def library_view(request):
    games = Game.objects.all()[:75]
    shelves = [games[i:i+15] for i in range(0, len(games), 15)]
    return render(request, 'library.html', {'shelves': shelves})


def login_view(request):
    form = LoginForm()
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            try:
                user = Users.objects.get(username=username)

                if check_password(password, user.password):
                    request.session['user_id'] = user.id
                    request.session['username'] = user.username
                    return redirect('index')
                else:
                    messages.error(request, "Invalid password")
            except Users.DoesNotExist:
                messages.error(request, "User does not exist")

    return render(request, 'login.html', {'form': form})


# ✅ ONLY ONE game_detail — SteamSpy-enabled
def game_detail(request, appid):

    # Check local DB first
    try:
        game = Game.objects.get(appid=appid)
    except Game.DoesNotExist:
        game = None

    # Fetch external API data
    api_data = fetch_steamspy(appid)

    # Build combined object (DB data takes priority)
    game_info = {
        "name": game.name if game else api_data.get("name", "Unknown Game"),
        "genre": game.genre if game else api_data.get("genre", "Unknown"),
        "description": game.description if game and game.description else api_data.get("description"),
        "image": game.image if game and game.image else f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/header.jpg",
        "fallback_image": "/static/images/no-cover.png",
    }

    return render(request, "gamecard.html", {"game": game_info})


def logout_view(request):
    request.session.flush()
    return redirect('login')


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully.")
            return redirect('login')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})


def profile_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        messages.error(request, "Please log in to view your profile.")
        return redirect('login')

    try:
        user = Users.objects.get(id=user_id)
    except Users.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('login')

    # Placeholder favorites
    favorite_games = []
    played_games = []

    context = {
        'user': user,
        'favorite_games': favorite_games,
        'played_games': played_games,
        'favorites_count': len(favorite_games),
        'played_count': len(played_games),
    }

    return render(request, 'profile.html', context)


@require_POST
def remove_from_favorites(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'Not logged in'})

    try:
        data = json.loads(request.body)
        game_id = data.get('game_id')

        # TODO remove from DB

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def remove_from_played(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'Not logged in'})

    try:
        data = json.loads(request.body)
        game_id = data.get('game_id')

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def search_api(request):
    query = request.GET.get('q', '').lower()
    if not query:
        return JsonResponse({'results': []})

    games = Game.objects.filter(name__icontains=query)[:20]

    results = [
        {
            'id': g.appid,
            'title': g.name,
            'cover_image': g.image,
            'genre': g.genre or 'Unknown',
        } for g in games
    ]

    return JsonResponse({'results': results})


def search_view(request):
    query = request.GET.get('q', '')
    games = Game.objects.filter(name__icontains=query)

    return render(request, 'search.html', {'query': query, 'games': games})
