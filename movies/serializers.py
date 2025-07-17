from rest_framework import serializers
from .models import (
    Movie, UserRating, UserWatchlist, MovieRecommendation
)
from core.models import Genre


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name', 'tmdb_id']


class MovieSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    
    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'original_title', 'overview', 'release_date',
            'runtime', 'budget', 'revenue', 'tmdb_id', 'imdb_id',
            'poster_path', 'backdrop_path', 'vote_average', 'vote_count',
            'popularity', 'genres', 'available_on_jellyfin', 'available_on_plex',
            'requested_on_radarr', 'created_at', 'updated_at'
        ]


class UserRatingSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)
    movie_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = UserRating
        fields = ['id', 'movie', 'movie_id', 'rating', 'created_at']


class UserWatchlistSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)
    movie_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = UserWatchlist
        fields = ['id', 'movie', 'movie_id', 'added_at']


class MovieRecommendationSerializer(serializers.ModelSerializer):
    movie = MovieSerializer(read_only=True)
    
    class Meta:
        model = MovieRecommendation
        fields = ['id', 'movie', 'score', 'reason', 'created_at']


