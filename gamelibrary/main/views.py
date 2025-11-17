from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.db.models import Q

import requests
import json

from .forms import RegistrationForm, LoginForm, ProfileForm
from .models import Users, Game, FavoriteGame, PlayedGame, WishlistGame, FriendRequest, Friend


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
    user_obj = None
    user_id = request.session.get("user_id")
    if user_id:
        user_obj = Users.objects.filter(id=user_id).first()

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
        "current_user": user_obj,
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
            "appid": appid,                # <-- added appid so templates send a valid id
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

    favorite_games_qs = FavoriteGame.objects.filter(user=user)
    played_games_qs = PlayedGame.objects.filter(user=user)
    wishlist_games_qs = WishlistGame.objects.filter(user=user)
    friends_qs = Friend.objects.filter(user=user).select_related("friend")
    pending_qs = FriendRequest.objects.filter(to_user=user, status=FriendRequest.PENDING).select_related("from_user")

    favorite_games = list(favorite_games_qs)
    played_games = list(played_games_qs)
    wishlist_games = list(wishlist_games_qs)
    friends = [f.friend for f in friends_qs]
    pending_requests = [fr.from_user for fr in pending_qs]

    def attach_appid(obj):
        gid = (obj.game_id or "").strip()
        try:
            obj.appid = int(gid)
        except (ValueError, TypeError):
            obj.appid = None
        return obj

    favorite_games = [attach_appid(g) for g in favorite_games]
    played_games = [attach_appid(g) for g in played_games]
    wishlist_games = [attach_appid(g) for g in wishlist_games]

    return render(request, "profile.html", {
        "user": user,
        "favorite_games": favorite_games,
        "played_games": played_games,
        "wishlist_games": wishlist_games,
        "favorites_count": len(favorite_games),
        "played_count": len(played_games),
        "wishlist_count": len(wishlist_games),
        "is_owner": True,
        "friends": friends,
        "pending_requests": pending_requests,
    })

def edit_profile_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    user = get_object_or_404(Users, id=user_id)
    favorites_count = FavoriteGame.objects.filter(user=user).count()
    played_count = PlayedGame.objects.filter(user=user).count()
    wishlist_count = WishlistGame.objects.filter(user=user).count()
    friends = [f.friend for f in Friend.objects.filter(user=user).select_related("friend")]
    pending_requests = [fr.from_user for fr in FriendRequest.objects.filter(to_user=user, status=FriendRequest.PENDING).select_related("from_user")]

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
        else:
            messages.error(request, "Please fix the errors highlighted below.")
    else:
        form = ProfileForm(instance=user)

    return render(request, "edit_profile.html", {
        "form": form,
        "user": user,
        "favorites_count": favorites_count,
        "played_count": played_count,
        "wishlist_count": wishlist_count,
        "friends": friends,
        "pending_requests": pending_requests,
    })


def public_profile_view(request, username):
    target_user = get_object_or_404(Users, username=username)
    viewer_id = request.session.get("user_id")
    is_owner = viewer_id == target_user.id if viewer_id else False

    favorite_games_qs = FavoriteGame.objects.filter(user=target_user)
    played_games_qs = PlayedGame.objects.filter(user=target_user)
    wishlist_games_qs = WishlistGame.objects.filter(user=target_user)
    friends = [f.friend for f in Friend.objects.filter(user=target_user).select_related("friend")]
    pending_requests = []

    def attach_appid(obj):
        gid = (obj.game_id or "").strip()
        try:
            obj.appid = int(gid)
        except (ValueError, TypeError):
            obj.appid = None
        return obj

    favorite_games = [attach_appid(g) for g in favorite_games_qs]
    played_games = [attach_appid(g) for g in played_games_qs]
    wishlist_games = [attach_appid(g) for g in wishlist_games_qs]

    return render(request, "profile.html", {
        "user": target_user,
        "favorite_games": favorite_games,
        "played_games": played_games,
        "wishlist_games": wishlist_games,
        "favorites_count": len(favorite_games),
        "played_count": len(played_games),
        "wishlist_count": len(wishlist_games),
        "is_owner": is_owner,
        "friends": friends,
        "pending_requests": pending_requests,
    })

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

def add_wishlist(request):
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

    WishlistGame.objects.get_or_create(
        user_id=user_id,
        game_id=game_id,
        defaults={
            "title": data.get("title"),
            "cover": data.get("cover"),
            "genre": data.get("genre"),
            "year": data.get("year"),
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

        deleted_count, _ = FavoriteGame.objects.filter(user_id=user_id, game_id=game_id).delete()
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

        deleted_count, _ = PlayedGame.objects.filter(user_id=user_id, game_id=game_id).delete()
        return JsonResponse({'success': True, 'deleted': deleted_count})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST
def remove_from_wishlist(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'Not logged in'}, status=403)

    try:
        data = json.loads(request.body)
        game_id = (data.get('game_id') or "").strip()
        if not game_id.isdigit():
            return JsonResponse({'success': False, 'error': 'invalid_game_id'}, status=400)

        deleted_count, _ = WishlistGame.objects.filter(user_id=user_id, game_id=game_id).delete()
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


def people_search_api(request):
    query = (request.GET.get("q") or "").strip()
    qs = Users.objects.all()
    if query:
        qs = qs.filter(username__icontains=query)[:10]
    else:
        qs = qs.order_by("username")[:10]

    current_user_id = request.session.get("user_id")
    friends = set(Friend.objects.filter(user_id=current_user_id).values_list("friend_id", flat=True)) if current_user_id else set()
    incoming = set()
    outgoing = set()
    if current_user_id:
        incoming = set(FriendRequest.objects.filter(to_user_id=current_user_id, status=FriendRequest.PENDING).values_list("from_user_id", flat=True))
        outgoing = set(FriendRequest.objects.filter(from_user_id=current_user_id, status=FriendRequest.PENDING).values_list("to_user_id", flat=True))

    results = []
    for u in qs:
        status = "none"
        if current_user_id == u.id:
            status = "self"
        elif u.id in friends:
            status = "friends"
        elif u.id in outgoing:
            status = "pending_out"
        elif u.id in incoming:
            status = "pending_in"

        results.append({
            "username": u.username,
            "avatar": u.avatar.url if u.avatar else None,
            "favourite_genre": u.get_favourite_genre_display(),
            "favorite_game": u.favorite_game or "",
            "bio": u.bio or "",
            "friend_status": status,
        })

    return JsonResponse({"results": results})


@require_POST
def send_friend_request(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"success": False, "error": "unauthenticated"}, status=403)

    data = json.loads(request.body)
    username = (data.get("username") or "").strip()
    if not username:
        return JsonResponse({"success": False, "error": "missing_username"}, status=400)

    try:
        target = Users.objects.get(username=username)
    except Users.DoesNotExist:
        return JsonResponse({"success": False, "error": "user_not_found"}, status=404)

    if target.id == user_id:
        return JsonResponse({"success": False, "error": "cannot_add_self"}, status=400)

    # Already friends?
    if Friend.objects.filter(user_id=user_id, friend=target).exists():
        return JsonResponse({"success": True, "status": "friends"})

    fr, created = FriendRequest.objects.get_or_create(
        from_user_id=user_id, to_user=target, defaults={"status": FriendRequest.PENDING}
    )
    if not created and fr.status == FriendRequest.ACCEPTED:
        return JsonResponse({"success": True, "status": "friends"})
    if not created and fr.status == FriendRequest.PENDING:
        return JsonResponse({"success": True, "status": "pending"})

    fr.status = FriendRequest.PENDING
    fr.save()
    return JsonResponse({"success": True, "status": "pending"})


@require_POST
def accept_friend_request(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"success": False, "error": "unauthenticated"}, status=403)

    data = json.loads(request.body)
    username = (data.get("username") or "").strip()
    if not username:
        return JsonResponse({"success": False, "error": "missing_username"}, status=400)

    try:
        sender = Users.objects.get(username=username)
    except Users.DoesNotExist:
        return JsonResponse({"success": False, "error": "user_not_found"}, status=404)

    try:
        fr = FriendRequest.objects.get(from_user=sender, to_user_id=user_id, status=FriendRequest.PENDING)
    except FriendRequest.DoesNotExist:
        return JsonResponse({"success": False, "error": "request_not_found"}, status=404)

    fr.status = FriendRequest.ACCEPTED
    fr.save()

    Friend.objects.get_or_create(user_id=user_id, friend=sender)
    Friend.objects.get_or_create(user=sender, friend_id=user_id)

    return JsonResponse({"success": True, "status": "accepted"})


@require_POST
def decline_friend_request(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"success": False, "error": "unauthenticated"}, status=403)

    data = json.loads(request.body)
    username = (data.get("username") or "").strip()
    if not username:
        return JsonResponse({"success": False, "error": "missing_username"}, status=400)

    try:
        sender = Users.objects.get(username=username)
    except Users.DoesNotExist:
        return JsonResponse({"success": False, "error": "user_not_found"}, status=404)

    try:
        fr = FriendRequest.objects.get(from_user=sender, to_user_id=user_id, status=FriendRequest.PENDING)
    except FriendRequest.DoesNotExist:
        return JsonResponse({"success": False, "error": "request_not_found"}, status=404)

    fr.status = FriendRequest.DECLINED
    fr.save()

    return JsonResponse({"success": True, "status": "declined"})


def friends_api(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"friends": []})
    friends = Friend.objects.filter(user_id=user_id).select_related("friend")
    data = [{
        "username": f.friend.username,
        "avatar": f.friend.avatar.url if f.friend.avatar else None,
        "favourite_genre": f.friend.get_favourite_genre_display(),
        "favorite_game": f.friend.favorite_game or "",
    } for f in friends]
    return JsonResponse({"friends": data})


def friend_requests_api(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"requests": []})
    incoming = FriendRequest.objects.filter(to_user_id=user_id, status=FriendRequest.PENDING).select_related("from_user")
    data = [{
        "username": fr.from_user.username,
        "avatar": fr.from_user.avatar.url if fr.from_user.avatar else None,
        "favourite_genre": fr.from_user.get_favourite_genre_display(),
        "favorite_game": fr.from_user.favorite_game or "",
    } for fr in incoming]
    return JsonResponse({"requests": data})
