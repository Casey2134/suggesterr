from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import TVShow, TVShowRating, TVShowWatchlist, TVShowRecommendation
from .serializers import TVShowSerializer, TVShowRatingSerializer, TVShowWatchlistSerializer, TVShowRecommendationSerializer
from movies.tmdb_tv_service import TMDBTVService
from movies.gemini_service import GeminiService
from movies.services import TVShowService
from movies.views import filter_negative_feedback
from integrations.services import SonarrService


def tv_show_list(request):
    """TV shows listing page"""
    return render(request, 'tv_shows/list.html')

def tv_show_detail(request, tv_show_id):
    """TV show detail page"""
    context = {'tv_show_id': tv_show_id}
    return render(request, 'tv_shows/detail.html', context)

def popular_tv_shows(request):
    """Popular TV shows page"""
    return render(request, 'tv_shows/popular.html')

def top_rated_tv_shows(request):
    """Top rated TV shows page"""
    return render(request, 'tv_shows/top_rated.html')


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
        
        # Filter out negative feedback items for authenticated users
        if tv_shows and 'results' in tv_shows:
            tv_shows['results'] = filter_negative_feedback(tv_shows['results'], request.user, 'tv')
        
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
        except Exception as e:
            return Response({'error': f'Server error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
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
    
    @action(detail=True, methods=['get'])
    def seasons(self, request, pk=None):
        """Get seasons information for a TV show"""
        try:
            tv_show_id = int(pk)
            tv_show = self.tmdb_tv_service.get_tv_show_details(tv_show_id)
            if not tv_show:
                return Response({'error': 'TV show not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Get detailed season information
            seasons = []
            for i in range(1, tv_show.get('number_of_seasons', 0) + 1):
                season_data = self.tmdb_tv_service._make_request(f"tv/{tv_show_id}/season/{i}")
                if season_data:
                    seasons.append({
                        'season_number': season_data.get('season_number'),
                        'name': season_data.get('name'),
                        'overview': season_data.get('overview', ''),
                        'episode_count': len(season_data.get('episodes', [])),
                        'air_date': season_data.get('air_date'),
                        'poster_path': f"{self.tmdb_tv_service.image_base_url}{season_data.get('poster_path')}" if season_data.get('poster_path') else None
                    })
            
            return Response(seasons)
        except ValueError:
            return Response({'error': 'Invalid TV show ID'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def request_tv_show(self, request, pk=None):
        try:
            tv_show_id = int(pk)
            tv_show = self.tmdb_tv_service.get_tv_show_details(tv_show_id)
            if not tv_show:
                return Response({'error': 'TV show not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Get request data
            quality_profile_id = request.data.get('quality_profile_id')
            selected_seasons = request.data.get('seasons', [])
            
            if quality_profile_id:
                try:
                    quality_profile_id = int(quality_profile_id)
                except ValueError:
                    return Response({'error': 'Invalid quality profile ID'}, status=status.HTTP_400_BAD_REQUEST)
            
            tv_show_service = TVShowService()
            success = tv_show_service.request_tv_show_on_sonarr(
                tv_show, 
                quality_profile_id=quality_profile_id,
                selected_seasons=selected_seasons
            )
            
            if success:
                return Response({'message': 'TV show requested successfully'})
            else:
                return Response({'error': 'Failed to request TV show'}, 
                              status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except ValueError:
            return Response({'error': 'Invalid TV show ID'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def quality_profiles(self, request):
        """Get available quality profiles from Sonarr"""
        sonarr_service = SonarrService()
        profiles = sonarr_service.get_quality_profiles()
        return Response(profiles)
    
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
        
        # Filter out negative feedback items
        tv_shows = filter_negative_feedback(tv_shows, request.user, 'tv')
        return Response(tv_shows)
    
    @action(detail=False, methods=['get'])
    def mood_recommendations(self, request):
        """Get mood-based TV show recommendations"""
        mood = request.query_params.get('mood', 'happy')
        gemini_service = GeminiService()
        
        tv_shows = gemini_service.get_tv_mood_based_recommendations(mood)
        
        # Filter out negative feedback items
        tv_shows = filter_negative_feedback(tv_shows, request.user, 'tv')
        return Response(tv_shows)
    
    @action(detail=False, methods=['get'])
    def similar_tv_shows(self, request):
        """Get TV shows similar to a given TV show"""
        tv_show_title = request.query_params.get('title')
        if not tv_show_title:
            return Response({'error': 'TV show title is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        gemini_service = GeminiService()
        tv_shows = gemini_service.get_similar_tv_shows(tv_show_title)
        
        # Filter out negative feedback items
        tv_shows = filter_negative_feedback(tv_shows, request.user, 'tv')
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
