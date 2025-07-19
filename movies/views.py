from django.shortcuts import render
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
import logging
from .models import (
    Movie, UserRating, UserWatchlist, MovieRecommendation
)
from core.models import Genre
from accounts.models import UserSettings
from recommendations.models import UserNegativeFeedback
from .serializers import (
    MovieSerializer, GenreSerializer, UserRatingSerializer,
    UserWatchlistSerializer, MovieRecommendationSerializer
)
from .services import MovieService, RecommendationService, TVShowService
from .tmdb_service import TMDBService
from .tmdb_tv_service import TMDBTVService
from .gemini_service import GeminiService
from integrations.services import JellyfinService, PlexService, RadarrService

logger = logging.getLogger(__name__)


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
        # Configure with user's settings
        jellyfin_service.configure(user_settings.server_url, user_settings.server_api_key)
        library_movies = jellyfin_service.get_library_movies(limit=limit)
    
    elif user_settings.server_type == 'plex':
        plex_service = PlexService()
        # Temporarily override settings for the service
        plex_service.base_url = user_settings.server_url
        plex_service.token = user_settings.server_api_key
        library_movies = plex_service.get_library_movies(limit=limit)
    
    return library_movies


def get_user_negative_feedback(user, content_type=None):
    """Get user's negative feedback (not interested items) for filtering"""
    queryset = UserNegativeFeedback.objects.filter(user=user)
    if content_type:
        queryset = queryset.filter(content_type=content_type)
    return list(queryset.values_list('tmdb_id', flat=True))


def filter_negative_feedback(items, user, content_type):
    """Filter out items that user marked as 'not interested'"""
    if not user.is_authenticated:
        return items
    
    negative_tmdb_ids = get_user_negative_feedback(user, content_type)
    if not negative_tmdb_ids:
        return items
    
    # Filter out items with TMDB IDs in the negative feedback list
    filtered_items = []
    for item in items:
        item_tmdb_id = item.get('id') or item.get('tmdb_id')
        if item_tmdb_id not in negative_tmdb_ids:
            filtered_items.append(item)
    
    return filtered_items


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
        
        # Filter out negative feedback items for authenticated users
        if movies and 'results' in movies:
            movies['results'] = filter_negative_feedback(movies['results'], request.user, 'movie')
            # Add local status information (availability and request status)
            movies['results'] = self._add_local_status(movies['results'])
        
        return Response(movies)
    
    def retrieve(self, request, pk=None):
        """Get a specific movie by ID"""
        try:
            movie_id = int(pk)
            movie = self.tmdb_service.get_movie_details(movie_id)
            if movie:
                # Add local status information for consistency with other endpoints
                movie_with_status = self._add_local_status([movie])
                return Response(movie_with_status[0] if movie_with_status else movie)
            else:
                return Response({'error': 'Movie not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({'error': 'Invalid movie ID'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'Server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        page = int(request.query_params.get('page', 1))
        movies = self.tmdb_service.get_popular_movies(page)
        
        # Filter out negative feedback items
        if movies and 'results' in movies:
            movies['results'] = filter_negative_feedback(movies['results'], request.user, 'movie')
            movies['results'] = self._add_local_status(movies['results'])
        
        return Response(movies)
    
    @action(detail=False, methods=['get'])
    def top_rated(self, request):
        page = int(request.query_params.get('page', 1))
        movies = self.tmdb_service.get_top_rated_movies(page)
        
        # Filter out negative feedback items
        if movies and 'results' in movies:
            movies['results'] = filter_negative_feedback(movies['results'], request.user, 'movie')
            movies['results'] = self._add_local_status(movies['results'])
        
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
            
            # Filter out negative feedback items and add local status
            if movies and 'results' in movies:
                movies['results'] = filter_negative_feedback(movies['results'], request.user, 'movie')
                movies['results'] = self._add_local_status(movies['results'])
            
            return Response(movies)
        except ValueError:
            return Response({'error': 'Invalid genre ID'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def now_playing(self, request):
        page = int(request.query_params.get('page', 1))
        movies = self.tmdb_service.get_now_playing_movies(page)
        
        # Filter out negative feedback items and add local status
        if movies and 'results' in movies:
            movies['results'] = filter_negative_feedback(movies['results'], request.user, 'movie')
            movies['results'] = self._add_local_status(movies['results'])
        
        return Response(movies)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        page = int(request.query_params.get('page', 1))
        movies = self.tmdb_service.get_upcoming_movies(page)
        
        # Filter out negative feedback items and add local status
        if movies and 'results' in movies:
            movies['results'] = filter_negative_feedback(movies['results'], request.user, 'movie')
            movies['results'] = self._add_local_status(movies['results'])
        
        return Response(movies)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        page = int(request.query_params.get('page', 1))
        movies = self.tmdb_service.search_movies(query, page)
        
        # Filter out negative feedback items and add local status
        if movies and 'results' in movies:
            movies['results'] = filter_negative_feedback(movies['results'], request.user, 'movie')
            movies['results'] = self._add_local_status(movies['results'])
        
        return Response(movies)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def request_movie(self, request, pk=None):
        try:
            movie_id = int(pk)
            movie = self.tmdb_service.get_movie_details(movie_id)
            if not movie:
                return Response({'error': 'Movie not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Get quality profile from request data
            quality_profile_id = request.data.get('quality_profile_id')
            if quality_profile_id:
                try:
                    quality_profile_id = int(quality_profile_id)
                except ValueError:
                    return Response({'error': 'Invalid quality profile ID'}, status=status.HTTP_400_BAD_REQUEST)
            
            movie_service = MovieService()
            success = movie_service.request_movie_on_radarr(movie, quality_profile_id)
            
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
        
        # Get library context and negative feedback if user is authenticated
        library_context = []
        negative_feedback_context = []
        if request.user.is_authenticated:
            library_context = get_user_library_context(request.user)
            negative_feedback_context = get_user_negative_feedback(request.user, 'movie')
        
        movies = gemini_service.get_personalized_recommendations(
            preferences, library_context, negative_feedback_context
        )
        
        # Additional client-side filtering in case AI doesn't fully exclude them
        movies = filter_negative_feedback(movies, request.user, 'movie')
        return Response(movies)
    
    @action(detail=False, methods=['get'])
    def mood_recommendations(self, request):
        """Get mood-based movie recommendations with library context"""
        mood = request.query_params.get('mood', 'happy')
        gemini_service = GeminiService()
        
        # Get library context and negative feedback if user is authenticated
        library_context = []
        negative_feedback_context = []
        if request.user.is_authenticated:
            library_context = get_user_library_context(request.user)
            negative_feedback_context = get_user_negative_feedback(request.user, 'movie')
        
        movies = gemini_service.get_mood_based_recommendations(mood, library_context, negative_feedback_context)
        
        # Filter out negative feedback items
        movies = filter_negative_feedback(movies, request.user, 'movie')
        return Response(movies)
    
    @action(detail=False, methods=['get'])
    def similar_movies(self, request):
        """Get movies similar to a given movie with library context"""
        movie_title = request.query_params.get('title')
        if not movie_title:
            return Response({'error': 'Movie title is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        gemini_service = GeminiService()
        
        # Get library context and negative feedback if user is authenticated
        library_context = []
        negative_feedback_context = []
        if request.user.is_authenticated:
            library_context = get_user_library_context(request.user)
            negative_feedback_context = get_user_negative_feedback(request.user, 'movie')
        
        movies = gemini_service.get_similar_movies(movie_title, library_context, negative_feedback_context)
        
        # Filter out negative feedback items
        movies = filter_negative_feedback(movies, request.user, 'movie')
        return Response(movies)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def recently_added(self, request):
        """Get recently added movies from user's media server"""
        # Get recently added movies from user's library
        recently_added = get_user_library_context(request.user, limit=50)
        
        if not recently_added:
            return Response([])
        
        # Convert library context format to movie card format
        movies = []
        for movie in recently_added:
            # Create a movie object that matches expected format
            movie_data = {
                'id': movie.get('tmdb_id'),
                'tmdb_id': movie.get('tmdb_id'),
                'title': movie.get('title'),
                'overview': movie.get('overview', ''),
                'poster_path': movie.get('poster_path'),
                'backdrop_path': movie.get('backdrop_path', ''),
                'release_date': movie.get('release_date') or str(movie.get('year', '')),
                'vote_average': movie.get('vote_average', 0),
                'vote_count': movie.get('vote_count', 0),
                'genres': movie.get('genres', []),
                'date_added': movie.get('date_added'),
                'recently_added': True
            }
            
            # Only add movies that have a TMDB ID (needed for proper display)
            if movie_data['tmdb_id']:
                movies.append(movie_data)
        
        # Filter out negative feedback items and add local status
        movies = filter_negative_feedback(movies, request.user, 'movie')
        movies = self._add_local_status(movies)
        return Response(movies)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def quality_profiles(self, request):
        """Get available quality profiles from Radarr"""
        radarr_service = RadarrService()
        profiles = radarr_service.get_quality_profiles()
        return Response(profiles)
    
    def _add_local_status(self, movies_list):
        """Add local database status (requested/available) to movie objects"""
        if not movies_list:
            return movies_list
        
        # Get TMDB IDs from the movie list (handle both 'id' and 'tmdb_id' fields)
        tmdb_ids = []
        for movie in movies_list:
            tmdb_id = movie.get('id') or movie.get('tmdb_id')
            if tmdb_id:
                tmdb_ids.append(tmdb_id)
        
        # Fetch local movie records
        local_movies = {}
        if tmdb_ids:
            movie_queryset = Movie.objects.filter(tmdb_id__in=tmdb_ids)
            local_movies = {movie.tmdb_id: movie for movie in movie_queryset}
        
        # Check Radarr for existing movies (batch check for efficiency)
        radarr_service = RadarrService()
        radarr_movies = radarr_service.get_radarr_movies_by_tmdb_ids(tmdb_ids)
        
        # Add local status to each movie
        for movie in movies_list:
            tmdb_id = movie.get('id') or movie.get('tmdb_id')
            
            # Check if movie is in Radarr (either from local DB or direct Radarr check)
            requested_on_radarr = False
            if tmdb_id and tmdb_id in local_movies:
                local_movie = local_movies[tmdb_id]
                requested_on_radarr = local_movie.requested_on_radarr
            
            # If not in local DB but exists in Radarr, update local DB
            if not requested_on_radarr and tmdb_id in radarr_movies:
                requested_on_radarr = True
                # Update local database
                try:
                    # Handle release_date properly - convert year to date or set to None
                    release_date = movie.get('release_date')
                    if release_date and len(str(release_date)) == 4:  # Just a year
                        try:
                            release_date = f"{release_date}-01-01"  # Convert year to YYYY-01-01
                        except:
                            release_date = None
                    elif release_date and not isinstance(release_date, str):
                        release_date = None
                    
                    movie_obj, created = Movie.objects.get_or_create(
                        tmdb_id=tmdb_id,
                        defaults={
                            'title': movie.get('title', ''),
                            'overview': movie.get('overview', ''),
                            'release_date': release_date,
                            'poster_path': movie.get('poster_path', ''),
                            'vote_average': movie.get('vote_average', 0),
                            'vote_count': movie.get('vote_count', 0)
                        }
                    )
                    movie_obj.requested_on_radarr = True
                    movie_obj.save()
                except Exception as e:
                    logger.error(f"Error updating movie status from Radarr: {e}")
            
            movie['requested_on_radarr'] = requested_on_radarr
        
        return movies_list


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






# Standalone auth views
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


# Template rendering views
def movie_list(request):
    """Movies listing page"""
    return render(request, 'movies/list.html')

def movie_detail(request, movie_id):
    """Movie detail page"""
    context = {'movie_id': movie_id}
    return render(request, 'movies/detail.html', context)

def popular_movies(request):
    """Popular movies page"""
    return render(request, 'movies/popular.html')

def top_rated_movies(request):
    """Top rated movies page"""
    return render(request, 'movies/top_rated.html')
