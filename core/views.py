from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from django.db.models import Q
from integrations.services import RadarrService, SonarrService, JellyfinService, PlexService
from accounts.models import UserSettings
from movies.models import Movie
from tv_shows.models import TVShow
from recommendations.models import UserNegativeFeedback
from movies.tmdb_service import TMDBService
from movies.tmdb_tv_service import TMDBTVService
import logging

def get_poster_url(poster_path, size='w300'):
    """Get TMDB poster URL following the same logic as JavaScript"""
    if not poster_path:
        return 'https://via.placeholder.com/300x450?text=No+Poster'
    
    if poster_path.startswith('https://'):
        return poster_path
    else:
        return f'https://image.tmdb.org/t/p/{size}{poster_path}'

logger = logging.getLogger(__name__)

def dashboard(request):
    """Main dashboard view - Modularized SPA with extracted JavaScript"""
    context = {
        'page_title': 'Suggesterr - Movie Recommendations',
    }
    return render(request, 'core/dashboard.html', context)

def health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({'status': 'healthy'})

@login_required
def search(request):
    """Unified search view for movies and TV shows"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return render(request, 'core/search.html', {
            'query': '',
            'movies': [],
            'tv_shows': [],
            'page_title': 'Search Results'
        })
    
    # Get user's negative feedback TMDB IDs
    negative_movie_tmdb_ids = []
    negative_tv_tmdb_ids = []
    
    if request.user.is_authenticated:
        negative_feedback = UserNegativeFeedback.objects.filter(user=request.user)
        negative_movie_tmdb_ids = list(negative_feedback.filter(content_type='movie').values_list('tmdb_id', flat=True))
        negative_tv_tmdb_ids = list(negative_feedback.filter(content_type='tv').values_list('tmdb_id', flat=True))
    
    # Initialize TMDB services
    tmdb_movie_service = TMDBService()
    tmdb_tv_service = TMDBTVService()
    
    # Search movies via TMDB API
    movie_results = tmdb_movie_service.search_movies(query, page=1)
    movies = []
    
    for movie in movie_results.get('results', [])[:20]:  # Limit to 20 results
        if movie.get('id') not in negative_movie_tmdb_ids:
            movies.append({
                'tmdb_id': movie.get('id'),
                'title': movie.get('title', ''),
                'original_title': movie.get('original_title', ''),
                'overview': movie.get('overview', ''),
                'poster_path': movie.get('poster_path'),
                'release_date': movie.get('release_date'),
                'vote_average': movie.get('vote_average', 0),
                'popularity': movie.get('popularity', 0)
            })
    
    # Search TV shows via TMDB API
    tv_results = tmdb_tv_service.search_tv_shows(query, page=1)
    tv_shows = []
    
    for tv_show in tv_results[:20]:  # Limit to 20 results
        if tv_show.get('id') not in negative_tv_tmdb_ids:
            tv_shows.append({
                'tmdb_id': tv_show.get('id'),
                'title': tv_show.get('name', ''),
                'original_title': tv_show.get('original_name', ''),
                'overview': tv_show.get('overview', ''),
                'poster_path': tv_show.get('poster_path'),
                'first_air_date': tv_show.get('first_air_date'),
                'vote_average': tv_show.get('vote_average', 0),
                'popularity': tv_show.get('popularity', 0)
            })
    
    context = {
        'query': query,
        'movies': movies,
        'tv_shows': tv_shows,
        'page_title': f'Search Results for "{query}"'
    }
    
    return render(request, 'core/search.html', context)

@login_required  
def search_api(request):
    """AJAX API endpoint for real-time search suggestions"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'movies': [], 'tv_shows': []})
    
    # Get user's negative feedback TMDB IDs
    negative_movie_tmdb_ids = []
    negative_tv_tmdb_ids = []
    
    if request.user.is_authenticated:
        negative_feedback = UserNegativeFeedback.objects.filter(user=request.user)
        negative_movie_tmdb_ids = list(negative_feedback.filter(content_type='movie').values_list('tmdb_id', flat=True))
        negative_tv_tmdb_ids = list(negative_feedback.filter(content_type='tv').values_list('tmdb_id', flat=True))
    
    # Limit to 5 results each for real-time suggestions
    movie_filter = Q(title__icontains=query) | Q(original_title__icontains=query)
    if negative_movie_tmdb_ids:
        movie_filter = movie_filter & ~Q(tmdb_id__in=negative_movie_tmdb_ids)
    
    movies = Movie.objects.filter(movie_filter).order_by('-popularity')[:5]
    
    tv_filter = Q(title__icontains=query) | Q(original_title__icontains=query)
    if negative_tv_tmdb_ids:
        tv_filter = tv_filter & ~Q(tmdb_id__in=negative_tv_tmdb_ids)
    
    tv_shows = TVShow.objects.filter(tv_filter).order_by('-popularity')[:5]
    
    # Serialize the data
    movies_data = [{
        'id': movie.tmdb_id,
        'title': movie.title,
        'poster_path': movie.poster_path,
        'release_date': movie.release_date.strftime('%Y') if movie.release_date else '',
        'vote_average': float(movie.vote_average) if movie.vote_average else 0
    } for movie in movies]
    
    tv_shows_data = [{
        'id': tv.tmdb_id,
        'title': tv.title,
        'poster_path': tv.poster_path,
        'first_air_date': tv.first_air_date.strftime('%Y') if tv.first_air_date else '',
        'vote_average': float(tv.vote_average) if tv.vote_average else 0
    } for tv in tv_shows]
    
    return JsonResponse({
        'movies': movies_data,
        'tv_shows': tv_shows_data
    })

@login_required
def tmdb_search_api(request):
    """TMDB API endpoint for real-time search using TMDB database"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'movies': [], 'tv_shows': []})
    
    # Get user's negative feedback TMDB IDs for filtering
    negative_movie_tmdb_ids = []
    negative_tv_tmdb_ids = []
    
    if request.user.is_authenticated:
        negative_feedback = UserNegativeFeedback.objects.filter(user=request.user)
        negative_movie_tmdb_ids = list(negative_feedback.filter(content_type='movie').values_list('tmdb_id', flat=True))
        negative_tv_tmdb_ids = list(negative_feedback.filter(content_type='tv').values_list('tmdb_id', flat=True))
    
    # Initialize TMDB services
    tmdb_movie_service = TMDBService()
    tmdb_tv_service = TMDBTVService()
    
    # Search movies via TMDB API
    movie_results = tmdb_movie_service.search_movies(query, page=1)
    movies_data = []
    
    for movie in movie_results.get('results', [])[:5]:  # Limit to 5 results
        if movie.get('id') not in negative_movie_tmdb_ids:
            movies_data.append({
                'id': movie.get('id'),
                'title': movie.get('title', ''),
                'poster_path': movie.get('poster_path'),
                'release_date': movie.get('release_date', '').split('-')[0] if movie.get('release_date') else '',
                'vote_average': movie.get('vote_average', 0)
            })
    
    # Search TV shows via TMDB API
    tv_results = tmdb_tv_service.search_tv_shows(query, page=1)
    tv_shows_data = []
    
    for tv_show in tv_results[:5]:  # Limit to 5 results
        if tv_show.get('id') not in negative_tv_tmdb_ids:
            tv_shows_data.append({
                'id': tv_show.get('id'),
                'title': tv_show.get('name', ''),
                'poster_path': tv_show.get('poster_path'),
                'first_air_date': tv_show.get('first_air_date', '').split('-')[0] if tv_show.get('first_air_date') else '',
                'vote_average': tv_show.get('vote_average', 0)
            })
    
    return JsonResponse({
        'movies': movies_data,
        'tv_shows': tv_shows_data
    })
