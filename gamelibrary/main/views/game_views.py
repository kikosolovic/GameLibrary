from django.shortcuts import render
from ..models import Game
from .fetch_views import fetch_steamstore
from django.http import JsonResponse

def library_view(request):
    def extract_price(p):
        try:
            return float(p.split()[0])
        except Exception:
            return None

    games = Game.objects.all()
    prices = [extract_price(g.price) for g in games if extract_price(g.price) is not None]
    price_min = int(min(prices)) if prices else 0
    price_max = int(max(prices)) if prices else 100

    scores = list(games.values_list("score", flat=True))
    scores = [s for s in scores if s is not None]
    score_min = int(min(scores)) if scores else 0
    score_max = int(max(scores)) if scores else 100

    return render(request, "library.html", {
        "price_min": price_min,
        "price_max": price_max,
        "score_min": score_min,
        "score_max": score_max,
    })


def normalize_requirements(req):
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
                "name": "Unknown Game",
                "description": "No data available.",
                "fallback_image": "/static/images/no-cover.png",
            }
        })

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
        first = movies[0]
        mp4 = first.get("mp4") or {}
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
        }
    }

    return render(request, "gamecard.html", context)


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

    search = request.GET.get("search")
    if search:
        qs = qs.filter(name__icontains=search)

    genre = request.GET.get("genre")
    if genre:
        qs = qs.filter(genre__icontains=genre)

    score_min = request.GET.get("score_min")
    score_max = request.GET.get("score_max")
    if score_min:
        qs = qs.filter(score__gte=float(score_min))
    if score_max:
        qs = qs.filter(score__lte=float(score_max))

    def extract_price(p):
        try:
            return float(p.split()[0])
        except Exception:
            return None

    price_min = request.GET.get("price_min")
    price_max = request.GET.get("price_max")

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
