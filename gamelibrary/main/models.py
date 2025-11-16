from django.db import models

# Create your models here.
GENRE_CHOICES =[
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

class Game(models.Model):
    appid = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    genre = models.CharField(max_length=255, blank=True, null=True)
    image = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
