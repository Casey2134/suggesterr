from rest_framework import serializers
from .models import TVShow, TVShowRating, TVShowWatchlist, TVShowRecommendation
from core.models import Genre


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name', 'tmdb_id']


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