from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.http import HttpResponse
from django.http import JsonResponse
from .models import FavoriteGame, PlayedGame

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
    # Extract numeric prices from price string
    def extract_price(p):
        try:
            return float(p.split()[0])
        except Exception:
            return None

    games = Game.objects.all()

    prices = [extract_price(g.price) for g in games if extract_price(g.price) is not None]
    if prices:
        price_min = int(min(prices))
        price_max = int(max(prices))
    else:
        price_min = 0
        price_max = 100

    scores = list(games.values_list("score", flat=True))
    scores = [s for s in scores if s is not None]
    if scores:
        score_min = int(min(scores))
        score_max = int(max(scores))
    else:
        score_min = 0
        score_max = 100

    return render(request, "library.html", {
        "price_min": price_min,
        "price_max": price_max,
        "score_min": score_min,
        "score_max": score_max,
    })


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
                    return redirect('library')
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
        return redirect('login')

    user = Users.objects.get(id=user_id)

    favorite_games = FavoriteGame.objects.filter(user=user)
    played_games = PlayedGame.objects.filter(user=user)

    return render(request, "profile.html", {
        "user": user,
        "favorite_games": favorite_games,
        "played_games": played_games,
        "favorites_count": favorite_games.count(),
        "played_count": played_games.count(),
    })


def edit_profile_view(request):
    return HttpResponse("Edit profile page here")

def add_favorite(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST only"})

    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"success": False, "error": "Not logged in"})

    data = json.loads(request.body)
    game_id = data.get("game_id")
    title = data.get("title")
    cover = data.get("cover")
    genre = data.get("genre")
    year = data.get("year")

    FavoriteGame.objects.get_or_create(
        user_id=user_id,
        game_id=game_id,
        defaults={
            "title": title,
            "cover": cover,
            "genre": genre,
            "year": year,
        }
    )

    return JsonResponse({"success": True})

def add_played(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST only"})

    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"success": False, "error": "Not logged in"})

    data = json.loads(request.body)
    game_id = data.get("game_id")
    title = data.get("title")
    cover = data.get("cover")
    genre = data.get("genre")
    year = data.get("year")

    PlayedGame.objects.get_or_create(
        user_id=user_id,
        game_id=game_id,
        defaults={
            "title": title,
            "cover": cover,
            "genre": genre,
            "year": year,
        }
    )

    return JsonResponse({"success": True})


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

def filter_games_api(request):
    qs = Game.objects.all()

    # Search
    search = request.GET.get("search")
    if search:
        qs = qs.filter(name__icontains=search)

    # Genre (simple substring match)
    genre = request.GET.get("genre")
    if genre:
        qs = qs.filter(genre__icontains=genre)

    # Score filter
    score_min = request.GET.get("score_min")
    score_max = request.GET.get("score_max")
    if score_min:
        qs = qs.filter(score__gte=float(score_min))
    if score_max:
        qs = qs.filter(score__lte=float(score_max))

    # Price filter (price is a string like "12.49 EUR" / "Free" / "Unavailable")
    price_min = request.GET.get("price_min")
    price_max = request.GET.get("price_max")

    def extract_price(p):
        try:
            return float(p.split()[0])
        except Exception:
            return None

    if price_min or price_max:
        ids = []
        for g in qs:
            p = extract_price(g.price)
            if p is None:
                continue
            if price_min and p < float(price_min):
                continue
            if price_max and p > float(price_max):
                continue
            ids.append(g.id)
        qs = qs.filter(id__in=ids)

    # Sort
    sort = request.GET.get("sort")
    if sort == "price_asc":
        qs = sorted(qs, key=lambda g: extract_price(g.price) or 999999)
    elif sort == "price_desc":
        qs = sorted(qs, key=lambda g: extract_price(g.price) or -1, reverse=True)
    elif sort == "name_asc":
        qs = qs.order_by("name")
    elif sort == "name_desc":
        qs = qs.order_by("-name")
    elif sort == "score_desc":
        qs = qs.order_by("-score")
    elif sort == "score_asc":
        qs = qs.order_by("score")

    # Build JSON
    results = [{
        "appid": g.appid,
        "name": g.name,
        "image": g.image or g.fallback_image,
    } for g in qs]

    return JsonResponse({"results": results})
