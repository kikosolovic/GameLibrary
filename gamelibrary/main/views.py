from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import requests
import json

from .forms import RegistrationForm, LoginForm
from .models import Users, Game


# ---------------------------------------------
#   FETCH FUNCTIONS (STEAMSPY + STEAMSTORE)
# ---------------------------------------------

def fetch_steamspy(appid):
    url = f"https://steamspy.com/api.php?request=appdetails&appid={appid}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None


def fetch_steamstore(appid):
    # Force English always
    url = (
        f"https://store.steampowered.com/api/appdetails?"
        f"appids={appid}&l=english&cc=us"
    )

    response = requests.get(url)
    if response.status_code != 200:
        return None

    data = response.json()

    if not data or not data.get(str(appid), {}).get("success", False):
        return None

    return data[str(appid)].get("data", {})


# ---------------------------------------------
#   LIBRARY VIEW
# ---------------------------------------------

def library_view(request):
    games = Game.objects.all()[:75]
    shelves = [games[i:i+15] for i in range(0, len(games), 15)]
    return render(request, 'library.html', {'shelves': shelves})


# ---------------------------------------------
#   LOGIN
# ---------------------------------------------

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


# ---------------------------------------------
#   GAME DETAIL (MAIN FIXED SECTION)
# ---------------------------------------------

def normalize_requirements(req):
    """Some games return a list instead of a dict. Some return empty strings.
       This function ensures a clean dictionary is returned."""
    if isinstance(req, dict):
        return {
            "minimum": req.get("minimum", ""),
            "recommended": req.get("recommended", "")
        }
    return {"minimum": "", "recommended": ""}  # fallback always safe


def game_detail(request, appid):

    store = fetch_steamstore(appid)

    if not store:
        return render(request, "gamecard.html", {
            "game": {
                "name": "Unknown Game",
                "description": "No data available.",
                "fallback_image": "/static/images/no-cover.png",
            }
        })

    # --- BASIC INFO ---
    name = store.get("name", "Unknown")
    short_desc = store.get("short_description") or ""
    long_desc = store.get("detailed_description") or store.get("about_the_game") or ""

    image = store.get("header_image")
    background = store.get("background") or store.get("background_raw")
    fallback = "/static/images/no-cover.png"

    # --- GENRES ---
    genres = ", ".join(g.get("description", "") for g in store.get("genres", []))

    # --- FEATURES / CATEGORIES ---
    categories = [c.get("description", "") for c in store.get("categories", [])]

    # --- SCREENSHOTS ---
    screenshots = store.get("screenshots", [])
    if not isinstance(screenshots, list):
        screenshots = []  # safety

    # --- MOVIES / TRAILERS ---
    movies = store.get("movies", [])
    trailer_url = None
    if isinstance(movies, list) and movies:
        first = movies[0]
        mp4 = first.get("mp4") or {}
        trailer_url = mp4.get("max") or mp4.get("480")

    # --- RELEASE DATE ---
    release = store.get("release_date", {})
    release_date = release.get("date", "Unknown")

    # --- DEVS & PUBS ---
    developers = store.get("developers", [])
    publishers = store.get("publishers", [])

    # --- PLATFORMS ---
    platforms = store.get("platforms", {})
    if not isinstance(platforms, dict):
        platforms = {"windows": False, "mac": False, "linux": False}

    # --- PRICE ---
    price_info = store.get("price_overview")
    if price_info:
        price = f"{price_info['final'] / 100:.2f} {price_info['currency']}"
        discount = price_info.get("discount_percent", 0)
    else:
        price = "Free" if store.get("is_free") else "Not available"
        discount = 0

    # --- REQUIREMENTS (FULLY FIXED) ---
    pc_reqs = normalize_requirements(store.get("pc_requirements"))
    mac_reqs = normalize_requirements(store.get("mac_requirements"))
    linux_reqs = normalize_requirements(store.get("linux_requirements"))

    context = {
        "game": {
            "name": name,
            "genre": genres or "Unknown",
            "description": short_desc or "No description available.",
            "long_description": long_desc,
            "image": image,
            "fallback_image": fallback,
            "background": background,

            "screenshots": screenshots,
            "trailer_url": trailer_url,
            "categories": categories,

            "release_date": release_date,
            "developers": developers,
            "publishers": publishers,
            "platforms": platforms,

            "price": price,
            "discount": discount,

            "pc_requirements": pc_reqs["minimum"],
            "pc_recommend": pc_reqs["recommended"],
            "mac_requirements": mac_reqs["minimum"],
            "linux_requirements": linux_reqs["minimum"],
        }
    }

    return render(request, "gamecard.html", context)


# ---------------------------------------------
#   LOGOUT
# ---------------------------------------------

def logout_view(request):
    request.session.flush()
    return redirect('login')


# ---------------------------------------------
#   REGISTER
# ---------------------------------------------

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


# ---------------------------------------------
#   PROFILE VIEW
# ---------------------------------------------

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


# ---------------------------------------------
#   REMOVE FAVORITES / PLAYED
# ---------------------------------------------

@require_POST
def remove_from_favorites(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'Not logged in'})

    try:
        data = json.loads(request.body)
        game_id = data.get('game_id')

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


# ---------------------------------------------
#   SEARCH
# ---------------------------------------------

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
