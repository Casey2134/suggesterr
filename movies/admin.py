from django.contrib import admin
from .models import Movie, Genre, UserRating, UserWatchlist, MovieRecommendation


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'tmdb_id')
    search_fields = ('name',)


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'release_date', 'vote_average', 'popularity', 'available_on_jellyfin', 'available_on_plex')
    list_filter = ('release_date', 'available_on_jellyfin', 'available_on_plex', 'requested_on_radarr', 'genres')
    search_fields = ('title', 'overview')
    filter_horizontal = ('genres',)
    readonly_fields = ('tmdb_id', 'created_at', 'updated_at')


@admin.register(UserRating)
class UserRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'movie__title')


@admin.register(UserWatchlist)
class UserWatchlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'movie__title')


@admin.register(MovieRecommendation)
class MovieRecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'score', 'created_at')
    list_filter = ('score', 'created_at')
    search_fields = ('user__username', 'movie__title')
    readonly_fields = ('created_at',)
