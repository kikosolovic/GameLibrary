from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.db import transaction
from django.db.models import Count

import urllib.parse
import requests
import json

from .forms import RegistrationForm, LoginForm
from .models import (
    Users,
    Game,
    FavoriteGame,
    PlayedGame,
    SteamProfile,
    Achievement,
    UserAchievement,
)

# API key from settings (recommended)
API_KEY = getattr(settings, "STEAM_API_KEY", "TU_API_KEY_AQUI")


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
#   GAME DETAIL
# ---------------------------------------------
def normalize_requirements(req):
    """Ensure system requirements are returned as a clean dict."""
    if isinstance(req, dict):
        return {
            "minimum": req.get("minimum", ""),
            "recommended": req.get("recommended", "")
        }
    return {"minimum": "", "recommended": ""}


def game_detail(request, appid):
    store = fetch_steamstore(appid)

    if not store:
        return render(request, "gamecard.html", {
            "game": {
                "appid": appid,
                "name": "Unknown Game",
                "description": "No data available.",
                "fallback_image": "/static/images/no-cover.png",
            },
            "achievements": [],
            "unlocked_ids": [],
            "progress": 0,
            "total_achievements": 0,
            "unlocked_count": 0,
        })

    # BASIC INFO
    name = store.get("name", "Unknown")
    short_desc = store.get("short_description") or ""
    long_desc = store.get("detailed_description") or store.get("about_the_game") or ""

    image = store.get("header_image")
    background = store.get("background") or store.get("background_raw")
    fallback = "/static/images/no-cover.png"

    genres = ", ".join(g.get("description", "") for g in store.get("genres", []))
    categories = [c.get("description", "") for c in store.get("categories", [])]

    screenshots = store.get("screenshots", [])
    if not isinstance(screenshots, list):
        screenshots = []

    movies = store.get("movies", [])
    trailer_url = None
    if isinstance(movies, list) and movies:
        mp4 = movies[0].get("mp4") or {}
        trailer_url = mp4.get("max") or mp4.get("480")

    release = store.get("release_date", {})
    release_date = release.get("date", "Unknown")

    developers = store.get("developers", [])
    publishers = store.get("publishers", [])

    platforms = store.get("platforms", {})
    if not isinstance(platforms, dict):
        platforms = {"windows": False, "mac": False, "linux": False}

    price_info = store.get("price_overview")
    if price_info:
        price = f"{price_info['final'] / 100:.2f} {price_info['currency']}"
        discount = price_info.get("discount_percent", 0)
    else:
        price = "Free" if store.get("is_free") else "Not available"
        discount = 0

    pc_reqs = normalize_requirements(store.get("pc_requirements"))
    mac_reqs = normalize_requirements(store.get("mac_requirements"))
    linux_reqs = normalize_requirements(store.get("linux_requirements"))

    # DATABASE GAME OBJECT
    game_obj, _ = Game.objects.get_or_create(
        appid=appid,
        defaults={"name": name}
    )

    # READ-ONLY: NO WRITES HERE
    achievements_in_db = Achievement.objects.filter(game=game_obj).order_by("display_name")

    # UNLOCKED ACHIEVEMENTS BY USER
    user_id = request.session.get("user_id")
    unlocked_ids = []
    if user_id:
        unlocked_ids = list(
            UserAchievement.objects.filter(
                user_id=user_id,
                achievement__game=game_obj,
                unlocked=True
            ).values_list("achievement_id", flat=True)
        )

    # CALCULATE PROGRESS
    total_achievements = achievements_in_db.count()
    unlocked_count = len(unlocked_ids)

    if total_achievements > 0:
        progress = round((unlocked_count / total_achievements) * 100)
    else:
        progress = 0

    # CONTEXT
    context = {
        "game": {
            "appid": appid,
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
        },
        "achievements": achievements_in_db,
        "unlocked_ids": unlocked_ids,
        "progress": progress,
        "total_achievements": total_achievements,
        "unlocked_count": unlocked_count,
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

    favorite_games_qs = FavoriteGame.objects.filter(user=user)
    played_games_qs = PlayedGame.objects.filter(user=user)

    favorite_games = list(favorite_games_qs)
    played_games = list(played_games_qs)

    def attach_game(obj):
        gid = (obj.game_id or "").strip()
        try:
            gid_int = int(gid)
        except:
            gid_int = None

        obj.appid = gid_int
        obj.real_game = Game.objects.filter(appid=gid_int).first()
        return obj

    # 🔥 FIX: antes decía attach_appid → eso no existe
    favorite_games = [attach_game(g) for g in favorite_games]
    played_games = [attach_game(g) for g in played_games]

    steam_profile = SteamProfile.objects.filter(user=user).first()

    return render(request, "profile.html", {
        "user": user,
        "favorite_games": favorite_games,
        "played_games": played_games,
        "favorites_count": len(favorite_games),
        "played_count": len(played_games),
        "steam_profile": steam_profile,
    })



def edit_profile_view(request):
    return HttpResponse("Edit profile page here")


# ---------------------------------------------
#   FAVORITES / PLAYED ADD
# ---------------------------------------------
def add_favorite(request):
    if request.method != "POST":
        return JsonResponse({"success": False}, status=405)

    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"success": False, "error": "unauthenticated"}, status=403)

    data = json.loads(request.body)
    game_id = data.get("game_id")
    if game_id is None:
        return JsonResponse({"success": False, "error": "missing_game_id"}, status=400)

    game_id = str(game_id).strip()
    if not game_id.isdigit():
        return JsonResponse({"success": False, "error": "invalid_game_id"}, status=400)

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
        return JsonResponse({"success": False}, status=405)

    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"success": False, "error": "unauthenticated"}, status=403)

    data = json.loads(request.body)
    game_id = data.get("game_id")
    if game_id is None:
        return JsonResponse({"success": False, "error": "missing_game_id"}, status=400)

    game_id = str(game_id).strip()
    if not game_id.isdigit():
        return JsonResponse({"success": False, "error": "invalid_game_id"}, status=400)

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
        return JsonResponse({'success': False, 'error': 'Not logged in'}, status=403)

    try:
        data = json.loads(request.body)
        game_id = (data.get('game_id') or "").strip()
        if not game_id.isdigit():
            return JsonResponse({'success': False, 'error': 'invalid_game_id'}, status=400)

        deleted_count, _ = FavoriteGame.objects.filter(
            user_id=user_id,
            game_id=game_id
        ).delete()
        return JsonResponse({'success': True, 'deleted': deleted_count})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
def remove_from_played(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'Not logged in'}, status=403)

    try:
        data = json.loads(request.body)
        game_id = (data.get('game_id') or "").strip()
        if not game_id.isdigit():
            return JsonResponse({'success': False, 'error': 'invalid_game_id'}, status=400)

        deleted_count, _ = PlayedGame.objects.filter(
            user_id=user_id,
            game_id=game_id
        ).delete()
        return JsonResponse({'success': True, 'deleted': deleted_count})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


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


# ---------------------------------------------
#   FILTER GAMES API
# ---------------------------------------------
def filter_games_api(request):
    qs = Game.objects.all()

    # Search
    search = request.GET.get("search")
    if search:
        qs = qs.filter(name__icontains=search)

    # Genre
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

    # Price filter
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

    results = [{
        "appid": g.appid,
        "name": g.name,
        "image": g.image or g.fallback_image,
    } for g in qs]

    return JsonResponse({"results": results})


# ---------------------------------------------
#   STEAM OPENID LOGIN
# ---------------------------------------------
STEAM_OPENID = "https://steamcommunity.com/openid/login"


def steam_login(request):
    params = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "checkid_setup",
        "openid.return_to": request.build_absolute_uri("/steam/return/"),
        "openid.realm": request.build_absolute_uri("/"),
        "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
    }

    url = STEAM_OPENID + "?" + urllib.parse.urlencode(params)
    return redirect(url)


def steam_return(request):
    claimed_id = request.GET.get("openid.claimed_id", "")

    if "steamcommunity.com/openid/id/" not in claimed_id:
        return HttpResponse("Steam login failed")

    steamid = claimed_id.split("/")[-1]

    user_id = request.session.get("user_id")
    if not user_id:
        return HttpResponse("You must be logged in with your site account first.")

    user = Users.objects.get(id=user_id)

    profile, _ = SteamProfile.objects.get_or_create(
        user=user,
        defaults={"steamid": steamid}
    )

    profile.steamid = steamid
    profile.save()

    return redirect("profile")


# ---------------------------------------------
#   STEAM WEB API HELPERS
# ---------------------------------------------
def fetch_achievements_schema(appid, api_key):
    url = (
        "https://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/"
        f"?key={api_key}&appid={appid}"
    )
    data = requests.get(url).json()

    if "game" not in data:
        return []

    return data["game"].get("availableGameStats", {}).get("achievements", [])


def fetch_user_achievements(appid, steamid, api_key):
    url = (
        "https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/"
        f"?key={api_key}&steamid={steamid}&appid={appid}"
    )
    data = requests.get(url).json()

    if "playerstats" not in data:
        return []

    return data["playerstats"].get("achievements", [])


def fetch_player_games(steamid, api_key):
    url = (
        "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
        f"?key={api_key}&steamid={steamid}&include_appinfo=true"
    )
    return requests.get(url).json().get("response", {}).get("games", [])


# ---------------------------------------------
#   STEAM SYNC (GAMES + ACHIEVEMENTS)
# ---------------------------------------------
def steam_sync(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    user = Users.objects.get(id=user_id)

    try:
        profile = SteamProfile.objects.get(user=user)
    except SteamProfile.DoesNotExist:
        return HttpResponse("You must link Steam account first")

    games = fetch_player_games(profile.steamid, API_KEY)


        # 1) SAVE PLAYED GAMES
    for g in games:
            appid = g.get("appid")
            if not appid:
                continue

            PlayedGame.objects.update_or_create(
                user=user,
                game_id=str(appid),
                defaults={
                    "title": g.get("name", "Unknown"),
                    "cover": f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/header.jpg",
                }
            )

            Game.objects.update_or_create(
                appid=appid,
                defaults={
                    "name": g.get("name", "Unknown"),
                    "image": f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/header.jpg",
                }
            )

        # 2) ACHIEVEMENTS (schema + unlocked)
    for g in games:
            appid = g.get("appid")
            if not appid:
                continue

            game_obj = Game.objects.filter(appid=appid).first()
            if not game_obj:
                continue

            # Load schema
            schema = fetch_achievements_schema(appid, API_KEY)

            for a in schema:
                Achievement.objects.update_or_create(
                    game=game_obj,
                    api_name=a.get("name"),
                    defaults={
                        "display_name": a.get("displayName"),
                        "description": a.get("description"),
                        "icon": a.get("icon"),
                        "icon_gray": a.get("icongray"),
                    }
                )

            # Remove duplicates
            duplicates = (
                Achievement.objects.filter(game=game_obj)
                .values("api_name")
                .annotate(c=Count("id"))
                .filter(c__gt=1)
            )
            for d in duplicates:
                dupes = Achievement.objects.filter(
                    game=game_obj, api_name=d["api_name"]
                )
                dupes.exclude(id=dupes.first().id).delete()

            # 3) USER UNLOCKED ACHIEVEMENTS
            user_stats = fetch_user_stats_for_game(appid, profile.steamid, API_KEY)
            playerstats = user_stats.get("playerstats", {})
            user_achievements = playerstats.get("achievements", [])

            for ua in user_achievements:
                apiname = ua.get("name")
                achieved = ua.get("achieved", 0) == 1

                ach = Achievement.objects.filter(
                    game=game_obj,
                    api_name=apiname
                ).first()

                if not ach:
                    continue

                UserAchievement.objects.update_or_create(
                    user=user,
                    achievement=ach,
                    defaults={"unlocked": achieved}
                )

    return redirect("profile")



def fetch_user_stats_for_game(appid, steamid, api_key):
    url = (
        "https://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v2/"
        f"?key={api_key}&steamid={steamid}&appid={appid}"
    )
    try:
        return requests.get(url, timeout=10).json()
    except:
        return {}
