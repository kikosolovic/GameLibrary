from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Game,
    Users,
    FavoriteGame,
    PlayedGame,
    SteamProfile,
    Achievement,
    UserAchievement
)

# ---------------------------------------------
# GAME ADMIN
# ---------------------------------------------
class GameAdmin(admin.ModelAdmin):
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
    search_fields = ("name", "appid", "genre")
    list_filter = ("genre",)
    ordering = ("-score",)

    readonly_fields = (
        "image_preview_large",
        "appid",
        "positive",
        "negative",
        "score",
    )

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

    def image_preview(self, obj):
        if obj.image:
            return format_html(f'<img src="{obj.image}" style="height:60px;border-radius:4px"/>')
        return "No image"
    image_preview.short_description = "Cover"

    def image_preview_large(self, obj):
        if obj.image:
            return format_html(f'<img src="{obj.image}" style="height:250px;border-radius:6px"/>')
        return "No image"
    image_preview_large.short_description = "Preview"


# ---------------------------------------------
# STEAM SYNC MODELS
# ---------------------------------------------
class SteamProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "steamid", "persona")
    search_fields = ("steamid", "persona", "user__username")


class AchievementAdmin(admin.ModelAdmin):
    list_display = ("game", "display_name", "api_name")
    search_fields = ("display_name", "api_name", "game__name")
    list_filter = ("game",)


class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ("user", "achievement", "unlocked")
    search_fields = ("user__username", "achievement__display_name")
    list_filter = ("unlocked",)


# ---------------------------------------------
# REGISTER ADMIN MODELS
# ---------------------------------------------
admin.site.register(Game, GameAdmin)
admin.site.register(Users)
admin.site.register(FavoriteGame)
admin.site.register(PlayedGame)
admin.site.register(SteamProfile, SteamProfileAdmin)
admin.site.register(Achievement, AchievementAdmin)
admin.site.register(UserAchievement, UserAchievementAdmin)
