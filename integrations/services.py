import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class JellyfinService:
    def __init__(self):
        self.base_url = settings.JELLYFIN_URL
        self.api_key = settings.JELLYFIN_API_KEY
        self.headers = {
            'X-MediaBrowser-Token': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def is_movie_available(self, movie):
        if not self.base_url or not self.api_key:
            return False
        
        try:
            # Search for movie in Jellyfin library
            search_url = f"{self.base_url}/Items"
            params = {
                'searchTerm': movie.title,
                'IncludeItemTypes': 'Movie',
                'Recursive': 'true'
            }
            
            response = requests.get(search_url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            items = data.get('Items', [])
            
            # Check if any item matches our movie
            for item in items:
                if self._movie_matches(item, movie):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking Jellyfin availability for {movie.title}: {e}")
            return False
    
    def _movie_matches(self, jellyfin_item, movie):
        # Basic matching logic - can be improved
        title_match = jellyfin_item.get('Name', '').lower() == movie.title.lower()
        
        # Check year if available
        if movie.release_date and jellyfin_item.get('ProductionYear'):
            year_match = jellyfin_item['ProductionYear'] == movie.release_date.year
            return title_match and year_match
        
        return title_match
    
    def get_library_stats(self):
        try:
            url = f"{self.base_url}/Items/Counts"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting Jellyfin library stats: {e}")
            return {}
    
    def get_library_movies(self, limit=None):
        """Fetch all movies from Jellyfin library for recommendation context"""
        if not self.base_url or not self.api_key:
            return []
        
        try:
            url = f"{self.base_url}/Items"
            params = {
                'IncludeItemTypes': 'Movie',
                'Recursive': 'true',
                'Fields': 'Genres,ProductionYear,Overview,CommunityRating,OfficialRating',
                'SortBy': 'DateAdded,SortName',
                'SortOrder': 'Descending'
            }
            
            if limit:
                params['Limit'] = limit
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            items = data.get('Items', [])
            
            # Format movie data for AI context
            library_movies = []
            for item in items:
                movie_info = {
                    'title': item.get('Name', ''),
                    'year': item.get('ProductionYear'),
                    'genres': [genre.get('Name', '') for genre in item.get('Genres', [])],
                    'overview': item.get('Overview', ''),
                    'rating': item.get('CommunityRating'),
                    'content_rating': item.get('OfficialRating')
                }
                library_movies.append(movie_info)
            
            logger.info(f"Retrieved {len(library_movies)} movies from Jellyfin library")
            return library_movies
            
        except Exception as e:
            logger.error(f"Error fetching Jellyfin library movies: {e}")
            return []


class PlexService:
    def __init__(self):
        self.base_url = settings.PLEX_URL
        self.token = settings.PLEX_TOKEN
        self.headers = {
            'X-Plex-Token': self.token,
            'Accept': 'application/json'
        }
    
    def is_movie_available(self, movie):
        if not self.base_url or not self.token:
            return False
        
        try:
            # Search for movie in Plex library
            search_url = f"{self.base_url}/search"
            params = {
                'query': movie.title,
                'type': 1  # 1 = Movies
            }
            
            response = requests.get(search_url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            media_container = data.get('MediaContainer', {})
            metadata = media_container.get('Metadata', [])
            
            # Check if any item matches our movie
            for item in metadata:
                if self._movie_matches(item, movie):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking Plex availability for {movie.title}: {e}")
            return False
    
    def _movie_matches(self, plex_item, movie):
        # Basic matching logic
        title_match = plex_item.get('title', '').lower() == movie.title.lower()
        
        # Check year if available
        if movie.release_date and plex_item.get('year'):
            year_match = plex_item['year'] == movie.release_date.year
            return title_match and year_match
        
        return title_match
    
    def get_library_stats(self):
        try:
            url = f"{self.base_url}/library/sections"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            sections = data.get('MediaContainer', {}).get('Directory', [])
            
            movie_sections = [s for s in sections if s.get('type') == 'movie']
            total_movies = sum(s.get('totalSize', 0) for s in movie_sections)
            
            return {'total_movies': total_movies}
        except Exception as e:
            logger.error(f"Error getting Plex library stats: {e}")
            return {}
    
    def get_library_movies(self, limit=None):
        """Fetch all movies from Plex library for recommendation context"""
        if not self.base_url or not self.token:
            return []
        
        try:
            # First get all movie library sections
            sections_url = f"{self.base_url}/library/sections"
            response = requests.get(sections_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            sections = data.get('MediaContainer', {}).get('Directory', [])
            movie_sections = [s for s in sections if s.get('type') == 'movie']
            
            if not movie_sections:
                logger.warning("No movie sections found in Plex library")
                return []
            
            # Fetch movies from all movie sections
            all_movies = []
            for section in movie_sections:
                section_key = section.get('key')
                movies_url = f"{self.base_url}/library/sections/{section_key}/all"
                
                params = {
                    'type': '1',  # Movies
                    'sort': 'addedAt:desc'
                }
                
                if limit and len(all_movies) >= limit:
                    break
                
                response = requests.get(movies_url, headers=self.headers, params=params, timeout=30)
                response.raise_for_status()
                
                section_data = response.json()
                metadata = section_data.get('MediaContainer', {}).get('Metadata', [])
                
                # Format movie data for AI context
                for item in metadata:
                    if limit and len(all_movies) >= limit:
                        break
                        
                    movie_info = {
                        'title': item.get('title', ''),
                        'year': item.get('year'),
                        'genres': [genre.get('tag', '') for genre in item.get('Genre', [])],
                        'overview': item.get('summary', ''),
                        'rating': item.get('rating'),
                        'content_rating': item.get('contentRating'),
                        'studio': item.get('studio')
                    }
                    all_movies.append(movie_info)
            
            logger.info(f"Retrieved {len(all_movies)} movies from Plex library")
            return all_movies
            
        except Exception as e:
            logger.error(f"Error fetching Plex library movies: {e}")
            return []


class RadarrService:
    def __init__(self):
        self.base_url = settings.RADARR_URL.rstrip('/') if settings.RADARR_URL else None
        self.api_key = settings.RADARR_API_KEY
        self.headers = {
            'X-Api-Key': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def request_movie(self, movie_data):
        if not self.base_url or not self.api_key:
            logger.error(f"Radarr not configured - URL: {self.base_url}, API Key: {'Present' if self.api_key else 'Missing'}")
            return False
        
        try:
            # Handle both model objects and TMDB data dictionaries
            if hasattr(movie_data, 'tmdb_id'):
                # Movie model object
                tmdb_id = movie_data.tmdb_id
                title = movie_data.title
            else:
                # TMDB data dictionary
                tmdb_id = movie_data.get('id')
                title = movie_data.get('title', 'Unknown')
            
            if not tmdb_id:
                logger.error(f"No TMDB ID found for movie {title}")
                return False
            
            # First, search for the movie
            search_url = f"{self.base_url}/api/v3/movie/lookup"
            params = {'term': f"tmdb:{tmdb_id}"}
            
            logger.info(f"Requesting Radarr lookup for {title} (TMDB ID: {tmdb_id})")
            logger.info(f"URL: {search_url}")
            logger.info(f"Headers: {dict(self.headers)}")
            
            response = requests.get(search_url, headers=self.headers, params=params, timeout=10)
            
            # Log the response details for debugging
            logger.info(f"Radarr response status: {response.status_code}")
            if response.status_code == 401:
                logger.error("Radarr authentication failed - check API key")
                logger.error(f"Response: {response.text}")
                return False
            
            response.raise_for_status()
            
            search_results = response.json()
            if not search_results:
                logger.error(f"Movie {title} not found in Radarr lookup")
                return False
            
            # Get the first result
            radarr_movie_data = search_results[0]
            
            # Add movie to Radarr
            add_url = f"{self.base_url}/api/v3/movie"
            add_data = {
                'title': radarr_movie_data.get('title'),
                'year': radarr_movie_data.get('year'),
                'tmdbId': radarr_movie_data.get('tmdbId'),
                'qualityProfileId': 1,  # Default quality profile
                'rootFolderPath': self._get_root_folder(),
                'monitored': True,
                'searchForMovie': True
            }
            
            logger.info(f"Sending add request to Radarr: {add_url}")
            logger.info(f"Add data: {add_data}")
            
            response = requests.post(add_url, json=add_data, headers=self.headers, timeout=10)
            
            logger.info(f"Add response status: {response.status_code}")
            if response.status_code >= 400:
                logger.error(f"Add response error: {response.text}")
                
            response.raise_for_status()
            
            logger.info(f"Movie {title} requested successfully on Radarr")
            return True
            
        except Exception as e:
            logger.error(f"Error requesting movie {title}: {e}")
            return False
    
    def test_connection(self):
        """Test Radarr API connection"""
        if not self.base_url or not self.api_key:
            return False, "Radarr not configured"
        
        try:
            test_url = f"{self.base_url}/api/v3/system/status"
            response = requests.get(test_url, headers=self.headers, timeout=10)
            
            if response.status_code == 401:
                return False, "Authentication failed - check API key"
            elif response.status_code == 200:
                return True, "Connection successful"
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
        except Exception as e:
            return False, f"Connection error: {e}"
    
    def _get_root_folder(self):
        try:
            url = f"{self.base_url}/api/v3/rootfolder"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            root_folders = response.json()
            if root_folders:
                return root_folders[0]['path']
            return '/movies'  # Default fallback
        except Exception as e:
            logger.error(f"Error getting Radarr root folder: {e}")
            return '/movies'
    
    def get_queue_status(self):
        try:
            url = f"{self.base_url}/api/v3/queue"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return {
                'total': data.get('totalRecords', 0),
                'items': data.get('records', [])
            }
        except Exception as e:
            logger.error(f"Error getting Radarr queue status: {e}")
            return {'total': 0, 'items': []}


class SonarrService:
    def __init__(self):
        self.base_url = settings.SONARR_URL.rstrip('/') if settings.SONARR_URL else None
        self.api_key = settings.SONARR_API_KEY
        self.headers = {
            'X-Api-Key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def request_series(self, series_title, tmdb_id=None, tvdb_id=None):
        if not self.base_url or not self.api_key:
            return False
        
        try:
            # Search for the series - try TMDB first, then fallback to title search
            search_url = f"{self.base_url}/api/v3/series/lookup"
            
            # Try searching by TMDB ID first if available
            if tmdb_id:
                params = {'term': f"tmdb:{tmdb_id}"}
            else:
                params = {'term': series_title}
            
            response = requests.get(search_url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            
            search_results = response.json()
            if not search_results:
                # If TMDB search failed, try title search as fallback
                if tmdb_id:
                    params = {'term': series_title}
                    response = requests.get(search_url, headers=self.headers, params=params, timeout=10)
                    response.raise_for_status()
                    search_results = response.json()
                    
                if not search_results:
                    logger.error(f"Series {series_title} not found in Sonarr lookup")
                    return False
            
            # Get the first result
            series_data = search_results[0]
            
            # Add series to Sonarr
            add_url = f"{self.base_url}/api/v3/series"
            add_data = {
                'title': series_data.get('title'),
                'year': series_data.get('year'),
                'tvdbId': series_data.get('tvdbId'),
                'qualityProfileId': 1,  # Default quality profile
                'rootFolderPath': self._get_root_folder(),
                'monitored': True,
                'searchForMissingEpisodes': True,
                'seasons': series_data.get('seasons', [])
            }
            
            response = requests.post(add_url, json=add_data, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Series {series_title} requested successfully on Sonarr")
            return True
            
        except Exception as e:
            logger.error(f"Error requesting series {series_title} on Sonarr: {e}")
            return False
    
    def _get_root_folder(self):
        try:
            url = f"{self.base_url}/api/v3/rootfolder"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            root_folders = response.json()
            if root_folders:
                return root_folders[0]['path']
            return '/tv'  # Default fallback
        except Exception as e:
            logger.error(f"Error getting Sonarr root folder: {e}")
            return '/tv'
    
    def get_queue_status(self):
        try:
            url = f"{self.base_url}/api/v3/queue"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return {
                'total': data.get('totalRecords', 0),
                'items': data.get('records', [])
            }
        except Exception as e:
            logger.error(f"Error getting Sonarr queue status: {e}")
            return {'total': 0, 'items': []}