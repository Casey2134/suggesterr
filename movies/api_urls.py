from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GenreViewSet, MovieViewSet, UserRatingViewSet,
    UserWatchlistViewSet, RecommendationViewSet,
    auth_login, auth_register, auth_logout, auth_current_user
)
from tv_shows.views import TVShowViewSet, TVShowRatingViewSet, TVShowWatchlistViewSet, TVShowRecommendationViewSet
from accounts.views import UserSettingsViewSet
from recommendations.views import UserNegativeFeedbackViewSet

# API Router
router = DefaultRouter()
router.register('genres', GenreViewSet, basename='genre')
router.register('movies', MovieViewSet, basename='movie')
router.register('ratings', UserRatingViewSet, basename='userrating')
router.register('watchlist', UserWatchlistViewSet, basename='userwatchlist')
router.register('recommendations', RecommendationViewSet, basename='recommendation')
router.register('tv-shows', TVShowViewSet, basename='tvshow')
router.register('tv-ratings', TVShowRatingViewSet, basename='tvshowrating')
router.register('tv-watchlist', TVShowWatchlistViewSet, basename='tvshowwatchlist')
router.register('tv-recommendations', TVShowRecommendationViewSet, basename='tvshowrecommendation')
router.register('negative-feedback', UserNegativeFeedbackViewSet, basename='negativefeedback')
router.register('settings', UserSettingsViewSet, basename='usersettings')

urlpatterns = [
    path('', include(router.urls)),
    # Auth endpoints
    path('auth/login/', auth_login, name='auth_login'),
    path('auth/register/', auth_register, name='auth_register'),
    path('auth/logout/', auth_logout, name='auth_logout'),
    path('auth/current_user/', auth_current_user, name='auth_current_user'),
]