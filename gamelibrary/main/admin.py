from django.contrib import admin
from .models import Game, Users, FavoriteGame, PlayedGame, WishlistGame, FriendRequest, Friend


# ---------------------------------------------
#   THUMBNAIL RENDER (small image preview)
# ---------------------------------------------
from django.utils.html import format_html

class GameAdmin(admin.ModelAdmin):
    # Columns visible in the list view
    list_display = (
        "appid",
        "name",
        "genre",
        "price",
        "positive",
        "negative",
        "score",
        "release_date",
        "image_preview",
    )

    # Fields searchable
    search_fields = ("name", "appid", "genre")

    # Filters on right side
    list_filter = ("genre",)

    # Default sorting (score descending)
    ordering = ("-score",)

    # Make fields read-only to avoid breaking DB accidentally
    readonly_fields = (
        "image_preview_large",
        "appid",
        "positive",
        "negative",
        "score",
    )

    # Fields in the edit page
    fieldsets = (
        ("Basic Info", {
            "fields": ("appid", "name", "genre", "release_date", "price")
        }),
        ("Descriptions", {
            "fields": ("description", "detailed_description")
        }),
        ("Images", {
            "fields": ("image", "fallback_image", "image_preview_large")
        }),
        ("Data Sources (SteamSpy)", {
            "fields": ("positive", "negative", "score")
        }),
        ("Screenshots", {
            "fields": ("screenshots",)
        }),
    )

    # Mini preview inside list view
    def image_preview(self, obj):
        if obj.image:
            return format_html(f'<img src="{obj.image}" style="height:60px;border-radius:4px"/>')
        return "No image"
    image_preview.short_description = "Cover"

    # Large preview inside detail page
    def image_preview_large(self, obj):
        if obj.image:
            return format_html(f'<img src="{obj.image}" style="height:250px;border-radius:6px"/>')
        return "No image"
    image_preview_large.short_description = "Preview"


# Register Admin Panels
admin.site.register(Game, GameAdmin)
admin.site.register(Users)
admin.site.register(FavoriteGame)
admin.site.register(PlayedGame)
admin.site.register(WishlistGame)
admin.site.register(FriendRequest)
admin.site.register(Friend)
