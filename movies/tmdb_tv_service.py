import requests
from django.conf import settings
from typing import Dict, List, Optional


class TMDBTVService:
    """Service for interacting with The Movie Database TV API"""
    
    def __init__(self):
        # Require TMDB API key from environment
        self.api_key = settings.TMDB_API_KEY
        if not self.api_key:
            raise ValueError("TMDB_API_KEY environment variable is required")
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
            print(f"TMDB TV API error: {e}")
            return None
    
    def get_popular_tv_shows(self, page: int = 1) -> List[dict]:
        """Get popular TV shows from TMDB"""
        data = self._make_request("tv/popular", {"page": page})
        return self._format_tv_shows(data.get('results', []) if data else [])
    
    def get_top_rated_tv_shows(self, page: int = 1) -> List[dict]:
        """Get top rated TV shows from TMDB"""
        data = self._make_request("tv/top_rated", {"page": page})
        return self._format_tv_shows(data.get('results', []) if data else [])
    
    def get_airing_today_tv_shows(self, page: int = 1) -> List[dict]:
        """Get TV shows airing today from TMDB"""
        data = self._make_request("tv/airing_today", {"page": page})
        return self._format_tv_shows(data.get('results', []) if data else [])
    
    def get_on_the_air_tv_shows(self, page: int = 1) -> List[dict]:
        """Get TV shows currently on the air from TMDB"""
        data = self._make_request("tv/on_the_air", {"page": page})
        return self._format_tv_shows(data.get('results', []) if data else [])
    
    def search_tv_shows(self, query: str, page: int = 1) -> List[dict]:
        """Search TV shows by query"""
        data = self._make_request("search/tv", {"query": query, "page": page})
        return self._format_tv_shows(data.get('results', []) if data else [])
    
    def get_tv_show_details(self, tv_show_id: int) -> Optional[dict]:
        """Get detailed information about a specific TV show"""
        data = self._make_request(f"tv/{tv_show_id}")
        return self._format_tv_show(data) if data else None
    
    def get_tv_shows_by_genre(self, genre_id: int, page: int = 1) -> List[dict]:
        """Get TV shows by genre ID"""
        data = self._make_request("discover/tv", {
            "with_genres": genre_id,
            "page": page,
            "sort_by": "popularity.desc"
        })
        return self._format_tv_shows(data.get('results', []) if data else [])
    
    def get_tv_genres(self) -> List[dict]:
        """Get all available TV genres"""
        data = self._make_request("genre/tv/list")
        return data.get('genres', []) if data else []
    
    def _format_tv_shows(self, tv_shows: List[dict]) -> List[dict]:
        """Format TV show data for consistent API response"""
        return [self._format_tv_show(tv_show) for tv_show in tv_shows]
    
    def _format_tv_show(self, tv_show: dict) -> dict:
        """Format a single TV show object"""
        return {
            'id': tv_show.get('id'),
            'title': tv_show.get('name', ''),  # TV shows use 'name' instead of 'title'
            'original_title': tv_show.get('original_name', ''),
            'overview': tv_show.get('overview', ''),
            'first_air_date': tv_show.get('first_air_date'),
            'last_air_date': tv_show.get('last_air_date'),
            'number_of_episodes': tv_show.get('number_of_episodes'),
            'number_of_seasons': tv_show.get('number_of_seasons'),
            'episode_run_time': tv_show.get('episode_run_time', []),
            'status': tv_show.get('status', ''),
            'tmdb_id': tv_show.get('id'),
            'imdb_id': tv_show.get('external_ids', {}).get('imdb_id') if 'external_ids' in tv_show else None,
            'poster_path': f"{self.image_base_url}{tv_show.get('poster_path')}" if tv_show.get('poster_path') else None,
            'backdrop_path': f"{self.image_base_url}{tv_show.get('backdrop_path')}" if tv_show.get('backdrop_path') else None,
            'vote_average': tv_show.get('vote_average'),
            'vote_count': tv_show.get('vote_count'),
            'popularity': tv_show.get('popularity'),
            'genres': [{'id': g.get('id'), 'name': g.get('name')} for g in tv_show.get('genres', [])] if 'genres' in tv_show else [],
            'genre_ids': tv_show.get('genre_ids', []),
            'adult': tv_show.get('adult', False),
            'available_on_jellyfin': False,  # Will be checked separately
            'available_on_plex': False,      # Will be checked separately
            'requested_on_sonarr': False,    # Will be checked separately
        }