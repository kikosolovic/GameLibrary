from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
import json
from ..models import Users, FavoriteGame, PlayedGame


def profile_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    user = Users.objects.get(id=user_id)
    favorite_games_qs = FavoriteGame.objects.filter(user=user)
    played_games_qs = PlayedGame.objects.filter(user=user)

    favorite_games = list(favorite_games_qs)
    played_games = list(played_games_qs)

    def attach_appid(obj):
        gid = (obj.game_id or "").strip()
        try:
            obj.appid = int(gid)
        except (ValueError, TypeError):
            obj.appid = None
        return obj

    favorite_games = [attach_appid(g) for g in favorite_games]
    played_games = [attach_appid(g) for g in played_games]

    return render(request, "profile.html", {
        "user": user,
        "favorite_games": favorite_games,
        "played_games": played_games,
        "favorites_count": len(favorite_games),
        "played_count": len(played_games),
    })


def edit_profile_view(request):
    return HttpResponse("Edit profile page here")


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


from django.views.decorators.http import require_POST


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
