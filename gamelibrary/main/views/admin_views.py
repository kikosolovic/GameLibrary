from django.http import JsonResponse
from ..models import Users
import json

def get_users(request):
    # Get current user
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"success": False, "error": "unauthenticated"}, status=403)

    try:
        user = Users.objects.get(id=user_id)
    except Users.DoesNotExist:
        return JsonResponse({"success": False, "error": "User not found"}, status=404)

    # Check admin role
    if user.role != "admin":
        return JsonResponse({"success": False, "error": "forbidden"}, status=403)

    # Fetch all users
    users = Users.objects.all().values("id", "username", "email", "role")
    return JsonResponse({"success": True, "users": list(users)})


def delete_user(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request"}, status=405)

    # Get current user
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"success": False, "error": "unauthenticated"}, status=403)

    try:
        admin_user = Users.objects.get(id=user_id)
    except Users.DoesNotExist:
        return JsonResponse({"success": False, "error": "User not found"}, status=404)

    # Only admins can delete users
    if admin_user.role != "admin":
        return JsonResponse({"success": False, "error": "forbidden"}, status=403)

    # Get target user id
    try:
        data = json.loads(request.body)
        target_user_id = data.get("user_id")
        target_user = Users.objects.get(id=target_user_id)
    except Users.DoesNotExist:
        return JsonResponse({"success": False, "error": "User not found"}, status=404)
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

    # Prevent deleting other admins
    if target_user.role == "admin":
        return JsonResponse({"success": False, "error": "Cannot delete admin"}, status=403)

    target_user.delete()
    return JsonResponse({"success": True})
