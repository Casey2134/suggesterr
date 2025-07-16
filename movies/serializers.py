from rest_framework import serializers
from .models import (
    Movie, Genre, UserRating, UserWatchlist, MovieRecommendation,
    TVShow, TVShowRating, TVShowWatchlist, TVShowRecommendation, UserSettings
)


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


class TVShowSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    
    class Meta:
        model = TVShow
        fields = [
            'id', 'title', 'original_title', 'overview', 'first_air_date',
            'last_air_date', 'number_of_episodes', 'number_of_seasons',
            'episode_run_time', 'status', 'tmdb_id', 'imdb_id',
            'poster_path', 'backdrop_path', 'vote_average', 'vote_count',
            'popularity', 'genres', 'available_on_jellyfin', 'available_on_plex',
            'requested_on_sonarr', 'created_at', 'updated_at'
        ]


class TVShowRatingSerializer(serializers.ModelSerializer):
    tv_show = TVShowSerializer(read_only=True)
    tv_show_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = TVShowRating
        fields = ['id', 'tv_show', 'tv_show_id', 'rating', 'created_at']


class TVShowWatchlistSerializer(serializers.ModelSerializer):
    tv_show = TVShowSerializer(read_only=True)
    tv_show_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = TVShowWatchlist
        fields = ['id', 'tv_show', 'tv_show_id', 'added_at']


class TVShowRecommendationSerializer(serializers.ModelSerializer):
    tv_show = TVShowSerializer(read_only=True)
    
    class Meta:
        model = TVShowRecommendation
        fields = ['id', 'tv_show', 'score', 'reason', 'created_at']


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = [
            'id', 'radarr_url', 'radarr_api_key', 'sonarr_url', 'sonarr_api_key',
            'server_type', 'server_url', 'server_api_key', 'theme', 
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'radarr_api_key': {'write_only': True},
            'sonarr_api_key': {'write_only': True},
            'server_api_key': {'write_only': True},
        }