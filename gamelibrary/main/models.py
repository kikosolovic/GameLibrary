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
    role = models.CharField(max_length=20, default='user')
    favourite_genre = models.CharField(max_length=100, choices=GENRE_CHOICES)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)
    totp_secret = models.CharField(max_length=16, blank=True, null=True)
    totp_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.username

class FavoriteGame(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    game_id = models.CharField(max_length=100)  
    title = models.CharField(max_length=200)
    cover = models.CharField(max_length=500)
    genre = models.CharField(max_length=100, null=True)
    year = models.CharField(max_length=20, null=True)

class PlayedGame(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    game_id = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    cover = models.CharField(max_length=500)
    genre = models.CharField(max_length=100, null=True)
    year = models.CharField(max_length=20, null=True)


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

    # NEW: Price from Steam Store
    price = models.CharField(max_length=50, blank=True, null=True)

    # NEW: SteamSpy voting stats
    positive = models.IntegerField(default=0)
    negative = models.IntegerField(default=0)

    # NEW: Calculated score (0–100)
    score = models.FloatField(default=0.0)

    def __str__(self):
        return self.name
