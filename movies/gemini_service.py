import requests
import json
from django.conf import settings
from typing import List, Dict, Optional
from .tmdb_service import TMDBService
from .tmdb_tv_service import TMDBTVService


class GeminiService:
    """Service for AI-powered movie recommendations using Google Gemini API"""
    
    def __init__(self):
        self.api_key = settings.GOOGLE_GEMINI_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        self.tmdb_service = TMDBService()
        self.tmdb_tv_service = TMDBTVService()
    
    def _make_request(self, prompt: str) -> Optional[str]:
        """Make a request to the Gemini API"""
        headers = {
            'Content-Type': 'application/json',
        }
        
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        try:
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                return result['candidates'][0]['content']['parts'][0]['text']
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Gemini API error: {e}")
            return None
    
    def get_personalized_recommendations(self, user_preferences: Dict = None, library_context: List[Dict] = None) -> List[Dict]:
        """Get personalized movie recommendations based on user preferences and library context"""
        if user_preferences is None:
            user_preferences = {}
        
        genres = user_preferences.get('genres', ['action', 'comedy', 'drama'])
        mood = user_preferences.get('mood', 'entertaining')
        year_range = user_preferences.get('year_range', '2015-2024')
        
        # Build library context string
        library_context_str = ""
        if library_context and len(library_context) > 0:
            library_titles = [f"'{movie['title']} ({movie.get('year', 'N/A')})'" for movie in library_context[:50]]  # Limit to avoid token limits
            library_context_str = f"\n\nIMPORTANT: The user has access to these movies in their personal library: {', '.join(library_titles)}. Try to recommend movies that complement this collection or fill gaps in similar genres/themes, but avoid recommending movies they already have."
        
        prompt = f"""
        Recommend 10 popular movies that are {mood} and fall into these genres: {', '.join(genres)}.
        Focus on movies from {year_range}.{library_context_str}
        
        Please provide your recommendations in exactly this JSON format:
        {{
            "recommendations": [
                {{
                    "title": "Movie Title",
                    "year": 2023,
                    "reason": "Brief reason why you recommend this movie"
                }}
            ]
        }}
        
        Only return the JSON, no additional text.
        """
        
        response = self._make_request(prompt)
        if not response:
            return []
        
        try:
            # Clean the response - remove markdown code blocks if present
            clean_response = response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]  # Remove ```json
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]  # Remove ```
            clean_response = clean_response.strip()
            
            # Parse the JSON response
            data = json.loads(clean_response)
            recommendations = data.get('recommendations', [])
            
            # Enhance recommendations with TMDB data
            enhanced_recommendations = []
            for rec in recommendations:
                movie_data = self._search_movie_on_tmdb(rec['title'], rec.get('year'))
                if movie_data:
                    movie_data['ai_reason'] = rec.get('reason', 'AI recommended')
                    enhanced_recommendations.append(movie_data)
            
            return enhanced_recommendations
            
        except json.JSONDecodeError:
            print("Failed to parse Gemini API response as JSON")
            return []
    
    def get_mood_based_recommendations(self, mood: str, library_context: List[Dict] = None) -> List[Dict]:
        """Get movie recommendations based on user's mood and library context"""
        mood_prompts = {
            'happy': 'uplifting, feel-good movies that will make me smile',
            'sad': 'emotionally healing movies that are comforting',
            'excited': 'thrilling, action-packed movies with lots of energy',
            'relaxed': 'calm, peaceful movies perfect for unwinding',
            'romantic': 'romantic movies perfect for date night',
            'adventurous': 'adventure movies with exciting journeys',
            'thoughtful': 'thought-provoking, intellectual movies',
            'nostalgic': 'classic movies that evoke nostalgia'
        }
        
        mood_description = mood_prompts.get(mood.lower(), 'entertaining')
        
        # Build library context string
        library_context_str = ""
        if library_context and len(library_context) > 0:
            library_titles = [f"'{movie['title']} ({movie.get('year', 'N/A')})'" for movie in library_context[:50]]
            library_context_str = f"\n\nIMPORTANT: The user has access to these movies in their personal library: {', '.join(library_titles)}. Try to recommend movies that complement this collection but avoid duplicating movies they already have."
        
        prompt = f"""
        Recommend 8 {mood_description} movies from the last 10 years.{library_context_str}
        
        Please provide your recommendations in exactly this JSON format:
        {{
            "recommendations": [
                {{
                    "title": "Movie Title",
                    "year": 2023,
                    "reason": "Brief reason why this fits the {mood} mood"
                }}
            ]
        }}
        
        Only return the JSON, no additional text.
        """
        
        response = self._make_request(prompt)
        if not response:
            return []
        
        try:
            # Clean the response - remove markdown code blocks if present
            clean_response = response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]  # Remove ```json
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]  # Remove ```
            clean_response = clean_response.strip()
            
            data = json.loads(clean_response)
            recommendations = data.get('recommendations', [])
            
            enhanced_recommendations = []
            for rec in recommendations:
                movie_data = self._search_movie_on_tmdb(rec['title'], rec.get('year'))
                if movie_data:
                    movie_data['ai_reason'] = rec.get('reason', f'Perfect for {mood} mood')
                    enhanced_recommendations.append(movie_data)
            
            return enhanced_recommendations
            
        except json.JSONDecodeError:
            print("Failed to parse Gemini API response as JSON")
            return []
    
    def get_similar_movies(self, movie_title: str, library_context: List[Dict] = None) -> List[Dict]:
        """Get movies similar to a given movie, considering library context"""
        # Build library context string
        library_context_str = ""
        if library_context and len(library_context) > 0:
            library_titles = [f"'{movie['title']} ({movie.get('year', 'N/A')})'" for movie in library_context[:50]]
            library_context_str = f"\n\nNote: The user has these movies in their library: {', '.join(library_titles)}. Avoid recommending movies they already have, but consider their collection when suggesting similar films."
        
        prompt = f"""
        Recommend 6 movies similar to "{movie_title}".
        Focus on movies with similar themes, genres, or storytelling style.{library_context_str}
        
        Please provide your recommendations in exactly this JSON format:
        {{
            "recommendations": [
                {{
                    "title": "Movie Title",
                    "year": 2023,
                    "reason": "Brief reason why this is similar to {movie_title}"
                }}
            ]
        }}
        
        Only return the JSON, no additional text.
        """
        
        response = self._make_request(prompt)
        if not response:
            return []
        
        try:
            # Clean the response - remove markdown code blocks if present
            clean_response = response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]  # Remove ```json
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]  # Remove ```
            clean_response = clean_response.strip()
            
            data = json.loads(clean_response)
            recommendations = data.get('recommendations', [])
            
            enhanced_recommendations = []
            for rec in recommendations:
                movie_data = self._search_movie_on_tmdb(rec['title'], rec.get('year'))
                if movie_data:
                    movie_data['ai_reason'] = rec.get('reason', f'Similar to {movie_title}')
                    enhanced_recommendations.append(movie_data)
            
            return enhanced_recommendations
            
        except json.JSONDecodeError:
            print("Failed to parse Gemini API response as JSON")
            return []
    
    def _search_movie_on_tmdb(self, title: str, year: int = None) -> Optional[Dict]:
        """Search for a movie on TMDB and return detailed information"""
        try:
            movies = self.tmdb_service.search_movies(title)
            if not movies:
                return None
            
            # Find the best match (preferably by year if provided)
            best_match = movies[0]
            if year:
                for movie in movies:
                    movie_year = None
                    if movie.get('release_date'):
                        try:
                            movie_year = int(movie['release_date'][:4])
                        except:
                            continue
                    
                    if movie_year and abs(movie_year - year) < abs(int(best_match.get('release_date', '0000')[:4]) - year):
                        best_match = movie
            
            # Get detailed information
            detailed_movie = self.tmdb_service.get_movie_details(best_match['id'])
            return detailed_movie or best_match
            
        except Exception as e:
            print(f"Error searching movie on TMDB: {e}")
            return None
    
    def get_tv_mood_based_recommendations(self, mood: str) -> List[Dict]:
        """Get TV show recommendations based on user's mood"""
        mood_prompts = {
            'happy': 'uplifting, feel-good TV shows that will make me smile',
            'sad': 'emotionally healing TV shows that are comforting',
            'excited': 'thrilling, action-packed TV shows with lots of energy',
            'relaxed': 'calm, peaceful TV shows perfect for unwinding',
            'romantic': 'romantic TV shows perfect for date night',
            'adventurous': 'adventure TV shows with exciting journeys',
            'thoughtful': 'thought-provoking, intellectual TV shows',
            'nostalgic': 'classic TV shows that evoke nostalgia'
        }
        
        mood_description = mood_prompts.get(mood.lower(), 'entertaining')
        
        prompt = f"""
        Recommend 8 {mood_description} TV shows from the last 10 years.
        
        Please provide your recommendations in exactly this JSON format:
        {{
            "recommendations": [
                {{
                    "title": "TV Show Title",
                    "year": 2023,
                    "reason": "Brief reason why this fits the {mood} mood"
                }}
            ]
        }}
        
        Only return the JSON, no additional text.
        """
        
        response = self._make_request(prompt)
        if not response:
            return []
        
        try:
            # Clean the response - remove markdown code blocks if present
            clean_response = response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]  # Remove ```json
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]  # Remove ```
            clean_response = clean_response.strip()
            
            data = json.loads(clean_response)
            recommendations = data.get('recommendations', [])
            
            enhanced_recommendations = []
            for rec in recommendations:
                tv_show_data = self._search_tv_show_on_tmdb(rec['title'], rec.get('year'))
                if tv_show_data:
                    tv_show_data['ai_reason'] = rec.get('reason', f'Perfect for {mood} mood')
                    enhanced_recommendations.append(tv_show_data)
            
            return enhanced_recommendations
            
        except json.JSONDecodeError:
            print("Failed to parse Gemini API response as JSON")
            return []
    
    def get_personalized_tv_recommendations(self, user_preferences: Dict = None) -> List[Dict]:
        """Get personalized TV show recommendations based on user preferences"""
        if user_preferences is None:
            user_preferences = {}
        
        genres = user_preferences.get('genres', ['drama', 'comedy', 'thriller'])
        mood = user_preferences.get('mood', 'entertaining')
        year_range = user_preferences.get('year_range', '2015-2024')
        
        prompt = f"""
        Recommend 10 popular TV shows that are {mood} and fall into these genres: {', '.join(genres)}.
        Focus on TV shows from {year_range}.
        
        Please provide your recommendations in exactly this JSON format:
        {{
            "recommendations": [
                {{
                    "title": "TV Show Title",
                    "year": 2023,
                    "reason": "Brief reason why you recommend this TV show"
                }}
            ]
        }}
        
        Only return the JSON, no additional text.
        """
        
        response = self._make_request(prompt)
        if not response:
            return []
        
        try:
            # Clean the response - remove markdown code blocks if present
            clean_response = response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]  # Remove ```json
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]  # Remove ```
            clean_response = clean_response.strip()
            
            data = json.loads(clean_response)
            recommendations = data.get('recommendations', [])
            
            # Enhance recommendations with TMDB data
            enhanced_recommendations = []
            for rec in recommendations:
                tv_show_data = self._search_tv_show_on_tmdb(rec['title'], rec.get('year'))
                if tv_show_data:
                    tv_show_data['ai_reason'] = rec.get('reason', 'AI recommended')
                    enhanced_recommendations.append(tv_show_data)
            
            return enhanced_recommendations
            
        except json.JSONDecodeError:
            print("Failed to parse Gemini API response as JSON")
            return []
    
    def get_similar_tv_shows(self, tv_show_title: str) -> List[Dict]:
        """Get TV shows similar to a given TV show"""
        prompt = f"""
        Recommend 6 TV shows similar to "{tv_show_title}".
        Focus on TV shows with similar themes, genres, or storytelling style.
        
        Please provide your recommendations in exactly this JSON format:
        {{
            "recommendations": [
                {{
                    "title": "TV Show Title",
                    "year": 2023,
                    "reason": "Brief reason why this is similar to {tv_show_title}"
                }}
            ]
        }}
        
        Only return the JSON, no additional text.
        """
        
        response = self._make_request(prompt)
        if not response:
            return []
        
        try:
            # Clean the response - remove markdown code blocks if present
            clean_response = response.strip()
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]  # Remove ```json
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]  # Remove ```
            clean_response = clean_response.strip()
            
            data = json.loads(clean_response)
            recommendations = data.get('recommendations', [])
            
            enhanced_recommendations = []
            for rec in recommendations:
                tv_show_data = self._search_tv_show_on_tmdb(rec['title'], rec.get('year'))
                if tv_show_data:
                    tv_show_data['ai_reason'] = rec.get('reason', f'Similar to {tv_show_title}')
                    enhanced_recommendations.append(tv_show_data)
            
            return enhanced_recommendations
            
        except json.JSONDecodeError:
            print("Failed to parse Gemini API response as JSON")
            return []
    
    def _search_tv_show_on_tmdb(self, title: str, year: int = None) -> Optional[Dict]:
        """Search for a TV show on TMDB and return detailed information"""
        try:
            tv_shows = self.tmdb_tv_service.search_tv_shows(title)
            if not tv_shows:
                return None
            
            # Find the best match (preferably by year if provided)
            best_match = tv_shows[0]
            if year:
                for tv_show in tv_shows:
                    tv_show_year = None
                    if tv_show.get('first_air_date'):
                        try:
                            tv_show_year = int(tv_show['first_air_date'][:4])
                        except:
                            continue
                    
                    if tv_show_year and abs(tv_show_year - year) < abs(int(best_match.get('first_air_date', '0000')[:4]) - year):
                        best_match = tv_show
            
            # Get detailed information
            detailed_tv_show = self.tmdb_tv_service.get_tv_show_details(best_match['id'])
            return detailed_tv_show or best_match
            
        except Exception as e:
            print(f"Error searching TV show on TMDB: {e}")
            return None