from rest_framework import serializers
from .models import Game,FavoriteGame


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = '__all__'
class FavouriteGameSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteGame
        fields = '__all__'