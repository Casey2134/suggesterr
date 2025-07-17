import requests
from django.conf import settings
from typing import Dict, List, Optional


class TMDBService:
    """Service for interacting with The Movie Database API"""
    
    def __init__(self):
        # Use environment API key if available, otherwise use the provided API key
        self.api_key = settings.TMDB_API_KEY or "26abd1c9264622709687e6f61139791c"
        self.base_url = "https://api.themoviedb.org/3"
        self.image_base_url = "https://image.tmdb.org/t/p/w500"
    
    def _make_request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """Make a request to the TMDB API"""
        if not self.api_key:
            return None
            
        if params is None:
            params = {}
        
        params['api_key'] = self.api_key
        
        try:
            response = requests.get(f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"TMDB API error: {e}")
            return None
    
    def get_popular_movies(self, page: int = 1) -> dict:
        """Get popular movies from TMDB"""
        data = self._make_request("movie/popular", {"page": page})
        if data:
            return {
                'page': data.get('page', page),
                'results': self._format_movies(data.get('results', [])),
                'total_pages': data.get('total_pages', 1),
                'total_results': data.get('total_results', 0)
            }
        return {'page': page, 'results': [], 'total_pages': 1, 'total_results': 0}
    
    def get_top_rated_movies(self, page: int = 1) -> dict:
        """Get top rated movies from TMDB"""
        data = self._make_request("movie/top_rated", {"page": page})
        if data:
            return {
                'page': data.get('page', page),
                'results': self._format_movies(data.get('results', [])),
                'total_pages': data.get('total_pages', 1),
                'total_results': data.get('total_results', 0)
            }
        return {'page': page, 'results': [], 'total_pages': 1, 'total_results': 0}
    
    def get_now_playing_movies(self, page: int = 1) -> dict:
        """Get now playing movies from TMDB"""
        data = self._make_request("movie/now_playing", {"page": page})
        if data:
            return {
                'page': data.get('page', page),
                'results': self._format_movies(data.get('results', [])),
                'total_pages': data.get('total_pages', 1),
                'total_results': data.get('total_results', 0)
            }
        return {'page': page, 'results': [], 'total_pages': 1, 'total_results': 0}
    
    def get_upcoming_movies(self, page: int = 1) -> dict:
        """Get upcoming movies from TMDB"""
        data = self._make_request("movie/upcoming", {"page": page})
        if data:
            return {
                'page': data.get('page', page),
                'results': self._format_movies(data.get('results', [])),
                'total_pages': data.get('total_pages', 1),
                'total_results': data.get('total_results', 0)
            }
        return {'page': page, 'results': [], 'total_pages': 1, 'total_results': 0}
    
    def search_movies(self, query: str, page: int = 1) -> dict:
        """Search movies by query"""
        data = self._make_request("search/movie", {"query": query, "page": page})
        if data:
            return {
                'page': data.get('page', page),
                'results': self._format_movies(data.get('results', [])),
                'total_pages': data.get('total_pages', 1),
                'total_results': data.get('total_results', 0)
            }
        return {'page': page, 'results': [], 'total_pages': 1, 'total_results': 0}
    
    def get_movie_details(self, movie_id: int) -> Optional[dict]:
        """Get detailed information about a specific movie"""
        data = self._make_request(f"movie/{movie_id}")
        return self._format_movie(data) if data else None
    
    def get_movies_by_genre(self, genre_id: int, page: int = 1) -> dict:
        """Get movies by genre ID"""
        data = self._make_request("discover/movie", {
            "with_genres": genre_id,
            "page": page,
            "sort_by": "popularity.desc"
        })
        if data:
            return {
                'page': data.get('page', page),
                'results': self._format_movies(data.get('results', [])),
                'total_pages': data.get('total_pages', 1),
                'total_results': data.get('total_results', 0)
            }
        return {'page': page, 'results': [], 'total_pages': 1, 'total_results': 0}
    
    def get_genres(self) -> List[dict]:
        """Get all available movie genres"""
        data = self._make_request("genre/movie/list")
        return data.get('genres', []) if data else []
    
    def _format_movies(self, movies: List[dict]) -> List[dict]:
        """Format movie data for consistent API response"""
        return [self._format_movie(movie) for movie in movies]
    
    def _format_movie(self, movie: dict) -> dict:
        """Format a single movie object"""
        return {
            'id': movie.get('id'),
            'title': movie.get('title', ''),
            'original_title': movie.get('original_title', ''),
            'overview': movie.get('overview', ''),
            'release_date': movie.get('release_date'),
            'runtime': movie.get('runtime'),
            'budget': movie.get('budget'),
            'revenue': movie.get('revenue'),
            'tmdb_id': movie.get('id'),
            'imdb_id': movie.get('imdb_id'),
            'poster_path': f"{self.image_base_url}{movie.get('poster_path')}" if movie.get('poster_path') else None,
            'backdrop_path': f"{self.image_base_url}{movie.get('backdrop_path')}" if movie.get('backdrop_path') else None,
            'vote_average': movie.get('vote_average'),
            'vote_count': movie.get('vote_count'),
            'popularity': movie.get('popularity'),
            'genres': [{'id': g.get('id'), 'name': g.get('name')} for g in movie.get('genres', [])] if 'genres' in movie else [],
            'genre_ids': movie.get('genre_ids', []),
            'adult': movie.get('adult', False),
            'requested_on_radarr': False,    # Will be checked separately
        }