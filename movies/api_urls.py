from django.urls import path
from .views import (
    GenreViewSet, MovieViewSet, UserRatingViewSet,
    UserWatchlistViewSet, RecommendationViewSet,
    auth_login, auth_register, auth_logout, auth_current_user
)
from tv_shows.views import TVShowViewSet, TVShowRatingViewSet, TVShowWatchlistViewSet, TVShowRecommendationViewSet
from accounts.views import UserSettingsViewSet
from recommendations.views import UserNegativeFeedbackViewSet

urlpatterns = [
    # Genre endpoints
    path('genres/', GenreViewSet.as_view({'get': 'list'}), name='genre-list'),
    path('genres/<int:pk>/', GenreViewSet.as_view({'get': 'retrieve'}), name='genre-detail'),
    
    # Movie endpoints
    path('movies/', MovieViewSet.as_view({'get': 'list'}), name='movie-list'),
    path('movies/<int:pk>/', MovieViewSet.as_view({'get': 'retrieve'}), name='movie-detail'),
    
    # Movie custom actions
    path('movies/popular/', MovieViewSet.as_view({'get': 'popular'}), name='movie-popular'),
    path('movies/top_rated/', MovieViewSet.as_view({'get': 'top_rated'}), name='movie-top-rated'),
    path('movies/by_genre/', MovieViewSet.as_view({'get': 'by_genre'}), name='movie-by-genre'),
    path('movies/now_playing/', MovieViewSet.as_view({'get': 'now_playing'}), name='movie-now-playing'),
    path('movies/upcoming/', MovieViewSet.as_view({'get': 'upcoming'}), name='movie-upcoming'),
    path('movies/search/', MovieViewSet.as_view({'get': 'search'}), name='movie-search'),
    path('movies/ai_recommendations/', MovieViewSet.as_view({'get': 'ai_recommendations'}), name='movie-ai-recommendations'),
    path('movies/mood_recommendations/', MovieViewSet.as_view({'get': 'mood_recommendations'}), name='movie-mood-recommendations'),
    path('movies/similar_movies/', MovieViewSet.as_view({'get': 'similar_movies'}), name='movie-similar'),
    path('movies/recently_added/', MovieViewSet.as_view({'get': 'recently_added'}), name='movie-recently-added'),
    path('movies/quality_profiles/', MovieViewSet.as_view({'get': 'quality_profiles'}), name='movie-quality-profiles'),
    path('movies/<int:pk>/request_movie/', MovieViewSet.as_view({'post': 'request_movie'}), name='movie-request'),
    
    # Rating endpoints
    path('ratings/', UserRatingViewSet.as_view({'get': 'list'}), name='userrating-list'),
    path('ratings/<int:pk>/', UserRatingViewSet.as_view({'get': 'retrieve'}), name='userrating-detail'),
    
    # Watchlist endpoints
    path('watchlist/', UserWatchlistViewSet.as_view({'get': 'list'}), name='userwatchlist-list'),
    path('watchlist/<int:pk>/', UserWatchlistViewSet.as_view({'get': 'retrieve'}), name='userwatchlist-detail'),
    
    # Recommendation endpoints
    path('recommendations/', RecommendationViewSet.as_view({'get': 'list'}), name='recommendation-list'),
    path('recommendations/<int:pk>/', RecommendationViewSet.as_view({'get': 'retrieve'}), name='recommendation-detail'),
    path('recommendations/generate/', RecommendationViewSet.as_view({'post': 'generate'}), name='recommendation-generate'),
    
    # TV Show endpoints
    path('tv-shows/', TVShowViewSet.as_view({'get': 'list'}), name='tvshow-list'),
    path('tv-shows/<int:pk>/', TVShowViewSet.as_view({'get': 'retrieve'}), name='tvshow-detail'),
    
    # TV Show custom actions
    path('tv-shows/popular/', TVShowViewSet.as_view({'get': 'popular'}), name='tvshow-popular'),
    path('tv-shows/top_rated/', TVShowViewSet.as_view({'get': 'top_rated'}), name='tvshow-top-rated'),
    path('tv-shows/by_genre/', TVShowViewSet.as_view({'get': 'by_genre'}), name='tvshow-by-genre'),
    path('tv-shows/airing_today/', TVShowViewSet.as_view({'get': 'airing_today'}), name='tvshow-airing-today'),
    path('tv-shows/on_the_air/', TVShowViewSet.as_view({'get': 'on_the_air'}), name='tvshow-on-the-air'),
    path('tv-shows/search/', TVShowViewSet.as_view({'get': 'search'}), name='tvshow-search'),
    path('tv-shows/ai_recommendations/', TVShowViewSet.as_view({'get': 'ai_recommendations'}), name='tvshow-ai-recommendations'),
    path('tv-shows/mood_recommendations/', TVShowViewSet.as_view({'get': 'mood_recommendations'}), name='tvshow-mood-recommendations'),
    path('tv-shows/similar_tv_shows/', TVShowViewSet.as_view({'get': 'similar_tv_shows'}), name='tvshow-similar'),
    path('tv-shows/quality_profiles/', TVShowViewSet.as_view({'get': 'quality_profiles'}), name='tvshow-quality-profiles'),
    path('tv-shows/<int:pk>/seasons/', TVShowViewSet.as_view({'get': 'seasons'}), name='tvshow-seasons'),
    path('tv-shows/<int:pk>/request_tv_show/', TVShowViewSet.as_view({'post': 'request_tv_show'}), name='tvshow-request'),
    
    # TV Show Rating endpoints
    path('tv-ratings/', TVShowRatingViewSet.as_view({'get': 'list'}), name='tvshowrating-list'),
    path('tv-ratings/<int:pk>/', TVShowRatingViewSet.as_view({'get': 'retrieve'}), name='tvshowrating-detail'),
    
    # TV Show Watchlist endpoints
    path('tv-watchlist/', TVShowWatchlistViewSet.as_view({'get': 'list'}), name='tvshowwatchlist-list'),
    path('tv-watchlist/<int:pk>/', TVShowWatchlistViewSet.as_view({'get': 'retrieve'}), name='tvshowwatchlist-detail'),
    
    # TV Show Recommendation endpoints
    path('tv-recommendations/', TVShowRecommendationViewSet.as_view({'get': 'list'}), name='tvshowrecommendation-list'),
    path('tv-recommendations/<int:pk>/', TVShowRecommendationViewSet.as_view({'get': 'retrieve'}), name='tvshowrecommendation-detail'),
    
    # Negative Feedback endpoints
    path('negative-feedback/', UserNegativeFeedbackViewSet.as_view({'get': 'list'}), name='negativefeedback-list'),
    path('negative-feedback/<int:pk>/', UserNegativeFeedbackViewSet.as_view({'get': 'retrieve'}), name='negativefeedback-detail'),
    
    # Settings endpoints
    path('settings/', UserSettingsViewSet.as_view({'get': 'list', 'post': 'create'}), name='usersettings-list'),
    path('settings/<int:pk>/', UserSettingsViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update'}), name='usersettings-detail'),
    
    # Auth endpoints
    path('auth/login/', auth_login, name='auth_login'),
    path('auth/register/', auth_register, name='auth_register'),
    path('auth/logout/', auth_logout, name='auth_logout'),
    path('auth/current_user/', auth_current_user, name='auth_current_user'),
]