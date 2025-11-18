from django.db import models

GENRE_CHOICES = [
    ('action', 'Action'),
    ('adventure', 'Adventure'),
    ('rpg', 'RPG'),
    ('strategy', 'Strategy'),
    ('simulation', 'Simulation'),
    ('sports', 'Sports'),
    ('racing', 'Racing'),
    ('horror', 'Horror'),
    ('indie', 'Indie'),
]

GENDER_CHOICES = [
    ('M', 'Male'),
    ('F', 'Female'),
]


class Users(models.Model):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=256)
    favourite_genre = models.CharField(max_length=100, choices=GENRE_CHOICES)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)

    # Optional fields used in template profile.html
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.username


class FavoriteGame(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    game_id = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    cover = models.CharField(max_length=500)
    genre = models.CharField(max_length=100, null=True)
    year = models.CharField(max_length=20, null=True)

    def __str__(self):
        return f"{self.title} ({self.user.username})"


class PlayedGame(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    game_id = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    cover = models.CharField(max_length=500)
    genre = models.CharField(max_length=100, null=True)
    year = models.CharField(max_length=20, null=True)

    def __str__(self):
        return f"{self.title} ({self.user.username})"


class Game(models.Model):
    appid = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)

    # Steam metadata
    genre = models.CharField(max_length=255, blank=True, null=True, default="Unknown")
    release_date = models.CharField(max_length=200, blank=True, null=True)

    # Media
    image = models.URLField(blank=True, null=True)
    screenshots = models.JSONField(default=list, blank=True)
    fallback_image = models.URLField(blank=True, null=True)

    # Text
    description = models.TextField(blank=True, null=True)
    detailed_description = models.TextField(blank=True, null=True)

    # Price from Steam Store
    price = models.CharField(max_length=50, blank=True, null=True)

    # SteamSpy voting stats
    positive = models.IntegerField(default=0)
    negative = models.IntegerField(default=0)

    # Calculated score (0–100)
    score = models.FloatField(default=0.0)

    def __str__(self):
        return self.name


class SteamProfile(models.Model):
    user = models.OneToOneField(Users, on_delete=models.CASCADE, related_name="steamprofile")
    steamid = models.CharField(max_length=64, unique=True)
    avatar = models.URLField(null=True, blank=True)
    persona = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return f"Steam: {self.persona or self.user.username} ({self.steamid})"


class Achievement(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="achievements")
    api_name = models.CharField(max_length=200)  # Internal Steam name
    display_name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    icon = models.URLField(null=True, blank=True)
    icon_gray = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.display_name


class UserAchievement(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name="user_achievements")
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked = models.BooleanField(default=False)
    unlock_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.achievement.display_name}"
