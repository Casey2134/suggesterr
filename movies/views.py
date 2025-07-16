from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q, Avg
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import (
    Movie, Genre, UserRating, UserWatchlist, MovieRecommendation,
    TVShow, TVShowRating, TVShowWatchlist, TVShowRecommendation, UserSettings
)
from .serializers import (
    MovieSerializer, GenreSerializer, UserRatingSerializer,
    UserWatchlistSerializer, MovieRecommendationSerializer,
    TVShowSerializer, TVShowRatingSerializer, TVShowWatchlistSerializer,
    TVShowRecommendationSerializer, UserSettingsSerializer
)
from .services import MovieService, RecommendationService, TVShowService
from .tmdb_service import TMDBService
from .tmdb_tv_service import TMDBTVService
from .gemini_service import GeminiService
from integrations.services import JellyfinService, PlexService


def get_user_library_context(user, limit=100):
    """Get user's media library context from their configured Plex/Jellyfin servers"""
    try:
        user_settings = UserSettings.objects.get(user=user)
    except UserSettings.DoesNotExist:
        return []
    
    library_movies = []
    
    # Check if user has a media server configured
    if not user_settings.server_url or not user_settings.server_api_key:
        return []
    
    # Get library based on server type
    if user_settings.server_type == 'jellyfin':
        jellyfin_service = JellyfinService()
        # Temporarily override settings for the service
        jellyfin_service.base_url = user_settings.server_url
        jellyfin_service.api_key = user_settings.server_api_key
        library_movies = jellyfin_service.get_library_movies(limit=limit)
    
    elif user_settings.server_type == 'plex':
        plex_service = PlexService()
        # Temporarily override settings for the service
        plex_service.base_url = user_settings.server_url
        plex_service.token = user_settings.server_api_key
        library_movies = plex_service.get_library_movies(limit=limit)
    
    return library_movies


class GenreViewSet(viewsets.ViewSet):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tmdb_service = TMDBService()
    
    def list(self, request):
        """Get all available genres from TMDB"""
        genres = self.tmdb_service.get_genres()
        return Response(genres)


class MovieViewSet(viewsets.ViewSet):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tmdb_service = TMDBService()
    
    def list(self, request):
        """Get all movies (popular by default)"""
        page = int(request.query_params.get('page', 1))
        search = request.query_params.get('search')
        
        if search:
            movies = self.tmdb_service.search_movies(search, page)
        else:
            movies = self.tmdb_service.get_popular_movies(page)
        
        return Response(movies)
    
    def retrieve(self, request, pk=None):
        """Get a specific movie by ID"""
        try:
            movie_id = int(pk)
            movie = self.tmdb_service.get_movie_details(movie_id)
            if movie:
                return Response(movie)
            else:
                return Response({'error': 'Movie not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({'error': 'Invalid movie ID'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        page = int(request.query_params.get('page', 1))
        movies = self.tmdb_service.get_popular_movies(page)
        return Response(movies)
    
    @action(detail=False, methods=['get'])
    def top_rated(self, request):
        page = int(request.query_params.get('page', 1))
        movies = self.tmdb_service.get_top_rated_movies(page)
        return Response(movies)
    
    @action(detail=False, methods=['get'])
    def by_genre(self, request):
        genre_id = request.query_params.get('genre_id')
        if not genre_id:
            return Response({'error': 'Genre ID parameter is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            genre_id = int(genre_id)
            page = int(request.query_params.get('page', 1))
            movies = self.tmdb_service.get_movies_by_genre(genre_id, page)
            return Response(movies)
        except ValueError:
            return Response({'error': 'Invalid genre ID'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def now_playing(self, request):
        page = int(request.query_params.get('page', 1))
        movies = self.tmdb_service.get_now_playing_movies(page)
        return Response(movies)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        page = int(request.query_params.get('page', 1))
        movies = self.tmdb_service.get_upcoming_movies(page)
        return Response(movies)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        page = int(request.query_params.get('page', 1))
        movies = self.tmdb_service.search_movies(query, page)
        return Response(movies)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def request_movie(self, request, pk=None):
        try:
            movie_id = int(pk)
            movie = self.tmdb_service.get_movie_details(movie_id)
            if not movie:
                return Response({'error': 'Movie not found'}, status=status.HTTP_404_NOT_FOUND)
            
            movie_service = MovieService()
            success = movie_service.request_movie_on_radarr(movie)
            
            if success:
                return Response({'message': 'Movie requested successfully'})
            else:
                return Response({'error': 'Failed to request movie'}, 
                              status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ValueError:
            return Response({'error': 'Invalid movie ID'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def ai_recommendations(self, request):
        """Get AI-powered movie recommendations with library context"""
        gemini_service = GeminiService()
        
        # Get user preferences from query parameters
        preferences = {
            'genres': request.query_params.get('genres', 'action,comedy,drama').split(','),
            'mood': request.query_params.get('mood', 'entertaining'),
            'year_range': request.query_params.get('year_range', '2015-2024')
        }
        
        # Get library context if user is authenticated
        library_context = []
        if request.user.is_authenticated:
            library_context = get_user_library_context(request.user)
        
        movies = gemini_service.get_personalized_recommendations(preferences, library_context)
        return Response(movies)
    
    @action(detail=False, methods=['get'])
    def mood_recommendations(self, request):
        """Get mood-based movie recommendations with library context"""
        mood = request.query_params.get('mood', 'happy')
        gemini_service = GeminiService()
        
        # Get library context if user is authenticated
        library_context = []
        if request.user.is_authenticated:
            library_context = get_user_library_context(request.user)
        
        movies = gemini_service.get_mood_based_recommendations(mood, library_context)
        return Response(movies)
    
    @action(detail=False, methods=['get'])
    def similar_movies(self, request):
        """Get movies similar to a given movie with library context"""
        movie_title = request.query_params.get('title')
        if not movie_title:
            return Response({'error': 'Movie title is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        gemini_service = GeminiService()
        
        # Get library context if user is authenticated
        library_context = []
        if request.user.is_authenticated:
            library_context = get_user_library_context(request.user)
        
        movies = gemini_service.get_similar_movies(movie_title, library_context)
        return Response(movies)


class UserRatingViewSet(viewsets.ModelViewSet):
    serializer_class = UserRatingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserRating.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserWatchlistViewSet(viewsets.ModelViewSet):
    serializer_class = UserWatchlistSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserWatchlist.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MovieRecommendationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return MovieRecommendation.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        recommendation_service = RecommendationService()
        
        # Get library context for improved recommendations
        library_context = get_user_library_context(request.user)
        
        recommendations = recommendation_service.generate_recommendations(
            request.user, library_context=library_context
        )
        
        serializer = self.get_serializer(recommendations, many=True)
        return Response(serializer.data)


class TVShowViewSet(viewsets.ViewSet):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tmdb_tv_service = TMDBTVService()
    
    def list(self, request):
        """Get all TV shows (popular by default)"""
        page = int(request.query_params.get('page', 1))
        search = request.query_params.get('search')
        
        if search:
            tv_shows = self.tmdb_tv_service.search_tv_shows(search, page)
        else:
            tv_shows = self.tmdb_tv_service.get_popular_tv_shows(page)
        
        return Response(tv_shows)
    
    def retrieve(self, request, pk=None):
        """Get a specific TV show by ID"""
        try:
            tv_show_id = int(pk)
            tv_show = self.tmdb_tv_service.get_tv_show_details(tv_show_id)
            if tv_show:
                return Response(tv_show)
            else:
                return Response({'error': 'TV show not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({'error': 'Invalid TV show ID'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        page = int(request.query_params.get('page', 1))
        tv_shows = self.tmdb_tv_service.get_popular_tv_shows(page)
        return Response(tv_shows)
    
    @action(detail=False, methods=['get'])
    def top_rated(self, request):
        page = int(request.query_params.get('page', 1))
        tv_shows = self.tmdb_tv_service.get_top_rated_tv_shows(page)
        return Response(tv_shows)
    
    @action(detail=False, methods=['get'])
    def by_genre(self, request):
        genre_id = request.query_params.get('genre_id')
        if not genre_id:
            return Response({'error': 'Genre ID parameter is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            genre_id = int(genre_id)
            page = int(request.query_params.get('page', 1))
            tv_shows = self.tmdb_tv_service.get_tv_shows_by_genre(genre_id, page)
            return Response(tv_shows)
        except ValueError:
            return Response({'error': 'Invalid genre ID'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def airing_today(self, request):
        page = int(request.query_params.get('page', 1))
        tv_shows = self.tmdb_tv_service.get_airing_today_tv_shows(page)
        return Response(tv_shows)
    
    @action(detail=False, methods=['get'])
    def on_the_air(self, request):
        page = int(request.query_params.get('page', 1))
        tv_shows = self.tmdb_tv_service.get_on_the_air_tv_shows(page)
        return Response(tv_shows)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        page = int(request.query_params.get('page', 1))
        tv_shows = self.tmdb_tv_service.search_tv_shows(query, page)
        return Response(tv_shows)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def request_tv_show(self, request, pk=None):
        try:
            tv_show_id = int(pk)
            tv_show = self.tmdb_tv_service.get_tv_show_details(tv_show_id)
            if not tv_show:
                return Response({'error': 'TV show not found'}, status=status.HTTP_404_NOT_FOUND)
            
            tv_show_service = TVShowService()
            success = tv_show_service.request_tv_show_on_sonarr(tv_show)
            
            if success:
                return Response({'message': 'TV show requested successfully'})
            else:
                return Response({'error': 'Failed to request TV show'}, 
                              status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except ValueError:
            return Response({'error': 'Invalid TV show ID'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def ai_recommendations(self, request):
        """Get AI-powered TV show recommendations"""
        gemini_service = GeminiService()
        
        # Get user preferences from query parameters
        preferences = {
            'genres': request.query_params.get('genres', 'drama,comedy,thriller').split(','),
            'mood': request.query_params.get('mood', 'entertaining'),
            'year_range': request.query_params.get('year_range', '2015-2024')
        }
        
        tv_shows = gemini_service.get_personalized_tv_recommendations(preferences)
        return Response(tv_shows)
    
    @action(detail=False, methods=['get'])
    def mood_recommendations(self, request):
        """Get mood-based TV show recommendations"""
        mood = request.query_params.get('mood', 'happy')
        gemini_service = GeminiService()
        
        tv_shows = gemini_service.get_tv_mood_based_recommendations(mood)
        return Response(tv_shows)
    
    @action(detail=False, methods=['get'])
    def similar_tv_shows(self, request):
        """Get TV shows similar to a given TV show"""
        tv_show_title = request.query_params.get('title')
        if not tv_show_title:
            return Response({'error': 'TV show title is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        gemini_service = GeminiService()
        tv_shows = gemini_service.get_similar_tv_shows(tv_show_title)
        return Response(tv_shows)


class TVShowRatingViewSet(viewsets.ModelViewSet):
    serializer_class = TVShowRatingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return TVShowRating.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TVShowWatchlistViewSet(viewsets.ModelViewSet):
    serializer_class = TVShowWatchlistSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return TVShowWatchlist.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TVShowRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TVShowRecommendationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return TVShowRecommendation.objects.filter(user=self.request.user)


class UserSettingsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get user settings"""
        settings, created = UserSettings.objects.get_or_create(user=request.user)
        serializer = UserSettingsSerializer(settings)
        return Response(serializer.data)
    
    def create(self, request):
        """Create or update user settings"""
        settings, created = UserSettings.objects.get_or_create(user=request.user)
        serializer = UserSettingsSerializer(settings, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """Update user settings"""
        settings = get_object_or_404(UserSettings, user=request.user)
        serializer = UserSettingsSerializer(settings, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Standalone auth views (CSRF exempt)
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def auth_login(request):
    """User login"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if username and password:
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return Response({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def auth_register(request):
    """User registration"""
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not all([username, email, password]):
        return Response({'error': 'Username, email, and password are required'}, 
                      status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
    
    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.create_user(username=username, email=email, password=password)
    login(request, user)
    
    return Response({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    })

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def auth_logout(request):
    """User logout"""
    logout(request)
    return Response({'success': True})

@api_view(['GET'])
@permission_classes([AllowAny])
def auth_current_user(request):
    """Get current authenticated user"""
    if request.user.is_authenticated:
        return Response({
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'email': request.user.email
            }
        })
    return Response({'user': None})
