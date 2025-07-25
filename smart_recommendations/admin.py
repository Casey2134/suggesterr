from django.contrib import admin
from .models import (
    UserRecommendationSettings,
    RecommendationProfile,
    CachedRecommendation,
    RecommendationFeedback,
    RecommendationQuality,
    UserPreferenceLearning,
    ContentFeatures,
    MovieSimilarity,
    TVShowSimilarity
)


@admin.register(UserRecommendationSettings)
class UserRecommendationSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'popular_vs_niche_balance', 'movie_weight', 'minimum_rating', 'last_refreshed']
    list_filter = ['prefer_recent_releases', 'prefer_highly_rated', 'include_rewatches']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(RecommendationProfile)
class RecommendationProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'avg_user_rating', 'rating_count', 'total_movies_watched', 'total_tv_shows_watched', 'last_analyzed']
    search_fields = ['user__username']
    readonly_fields = ['last_analyzed']


@admin.register(CachedRecommendation)
class CachedRecommendationAdmin(admin.ModelAdmin):
    list_display = ['user', 'content_type', 'tmdb_id', 'score', 'recommendation_type', 'created_at', 'expires_at']
    list_filter = ['content_type', 'recommendation_type', 'viewed', 'clicked', 'added_to_watchlist', 'requested']
    search_fields = ['user__username', 'tmdb_id']
    readonly_fields = ['created_at']


@admin.register(RecommendationFeedback)
class RecommendationFeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'content_type', 'tmdb_id', 'feedback_type', 'detailed_reason', 'created_at']
    list_filter = ['feedback_type', 'detailed_reason', 'content_type']
    search_fields = ['user__username', 'tmdb_id']
    readonly_fields = ['created_at']


@admin.register(RecommendationQuality)
class RecommendationQualityAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_date', 'total_recommendations', 'success_rate', 'avg_recommendation_score']
    list_filter = ['session_date']
    search_fields = ['user__username']
    readonly_fields = ['session_date']


@admin.register(UserPreferenceLearning)
class UserPreferenceLearningAdmin(admin.ModelAdmin):
    list_display = ['user', 'learning_confidence', 'data_points_analyzed', 'rating_threshold_learned', 'last_learning_update']
    search_fields = ['user__username']
    readonly_fields = ['last_learning_update']


@admin.register(ContentFeatures)
class ContentFeaturesAdmin(admin.ModelAdmin):
    list_display = ['content_type', 'tmdb_id', 'popularity_percentile', 'rating_percentile', 'niche_score', 'runtime_category', 'release_era']
    list_filter = ['content_type', 'runtime_category', 'release_era']
    search_fields = ['tmdb_id']
    readonly_fields = ['features_computed_at']


@admin.register(MovieSimilarity)
class MovieSimilarityAdmin(admin.ModelAdmin):
    list_display = ['movie1_tmdb_id', 'movie2_tmdb_id', 'similarity_score', 'genre_similarity', 'cast_similarity', 'computed_at']
    search_fields = ['movie1_tmdb_id', 'movie2_tmdb_id']
    readonly_fields = ['computed_at']


@admin.register(TVShowSimilarity)
class TVShowSimilarityAdmin(admin.ModelAdmin):
    list_display = ['show1_tmdb_id', 'show2_tmdb_id', 'similarity_score', 'genre_similarity', 'cast_similarity', 'computed_at']
    search_fields = ['show1_tmdb_id', 'show2_tmdb_id']
    readonly_fields = ['computed_at']
