import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q, Avg
from tmdbv3api import TMDb, Movie as TMDbMovie, Genre as TMDbGenre
from .models import Movie, UserRating, MovieRecommendation
from core.models import Genre
from integrations.services import JellyfinService, PlexService, RadarrService, SonarrService
from .gemini_service import GeminiService


class MovieService:
    def __init__(self):
        self.tmdb = TMDb()
        self.tmdb.api_key = settings.TMDB_API_KEY
        self.tmdb_movie = TMDbMovie()
        self.tmdb_genre = TMDbGenre()
        
        self.jellyfin_service = JellyfinService()
        self.plex_service = PlexService()
        self.radarr_service = RadarrService()
    
    def sync_genres_from_tmdb(self):
        try:
            tmdb_genres = self.tmdb_genre.movie_list()
            for tmdb_genre in tmdb_genres:
                genre, created = Genre.objects.get_or_create(
                    tmdb_id=tmdb_genre['id'],
                    defaults={'name': tmdb_genre['name']}
                )
                if not created and genre.name != tmdb_genre['name']:
                    genre.name = tmdb_genre['name']
                    genre.save()
            return True
        except Exception as e:
            print(f"Error syncing genres: {e}")
            return False
    
    def sync_popular_movies(self, pages=5):
        try:
            for page in range(1, pages + 1):
                popular_movies = self.tmdb_movie.popular(page=page)
                for tmdb_movie in popular_movies:
                    self.create_or_update_movie_from_tmdb(tmdb_movie)
            return True
        except Exception as e:
            print(f"Error syncing popular movies: {e}")
            return False
    
    def sync_movies_by_genre(self, genre_id, pages=3):
        try:
            for page in range(1, pages + 1):
                movies = self.tmdb_movie.discover(
                    with_genres=genre_id, 
                    page=page, 
                    sort_by='popularity.desc'
                )
                for tmdb_movie in movies:
                    self.create_or_update_movie_from_tmdb(tmdb_movie)
            return True
        except Exception as e:
            print(f"Error syncing movies by genre: {e}")
            return False
    
    def create_or_update_movie_from_tmdb(self, tmdb_movie_data):
        try:
            movie, created = Movie.objects.get_or_create(
                tmdb_id=tmdb_movie_data['id'],
                defaults={
                    'title': tmdb_movie_data.get('title', ''),
                    'original_title': tmdb_movie_data.get('original_title', ''),
                    'overview': tmdb_movie_data.get('overview', ''),
                    'release_date': tmdb_movie_data.get('release_date') or None,
                    'poster_path': tmdb_movie_data.get('poster_path', ''),
                    'backdrop_path': tmdb_movie_data.get('backdrop_path', ''),
                    'vote_average': tmdb_movie_data.get('vote_average', 0),
                    'vote_count': tmdb_movie_data.get('vote_count', 0),
                    'popularity': tmdb_movie_data.get('popularity', 0),
                }
            )
            
            if tmdb_movie_data.get('genre_ids'):
                genres = Genre.objects.filter(tmdb_id__in=tmdb_movie_data['genre_ids'])
                movie.genres.set(genres)
            
            movie.save()
            
            return movie
        except Exception as e:
            print(f"Error creating/updating movie: {e}")
            return None
    
    def request_movie_on_radarr(self, movie, quality_profile_id=None):
        # Get TMDB ID for checking
        tmdb_id = movie.get('id') if isinstance(movie, dict) else getattr(movie, 'tmdb_id', None)
        title = movie.get('title') if isinstance(movie, dict) else getattr(movie, 'title', 'Unknown')
        
        if not tmdb_id:
            print(f"No TMDB ID found for movie {title}")
            return False
        
        # Check if movie already exists in Radarr
        if self.radarr_service.is_movie_in_radarr(tmdb_id):
            print(f"Movie {title} already exists in Radarr, updating local status")
            # Update local database to reflect this
            try:
                # Handle release_date properly
                if isinstance(movie, dict):
                    release_date = movie.get('release_date')
                else:
                    release_date = getattr(movie, 'release_date', None)
                
                # Convert year-only dates to proper format
                if release_date and len(str(release_date)) == 4:
                    try:
                        release_date = f"{release_date}-01-01"
                    except:
                        release_date = None
                elif release_date and not isinstance(release_date, str):
                    release_date = None
                
                movie_obj, created = Movie.objects.get_or_create(
                    tmdb_id=tmdb_id,
                    defaults={
                        'title': movie.get('title') if isinstance(movie, dict) else getattr(movie, 'title', ''),
                        'overview': movie.get('overview', '') if isinstance(movie, dict) else getattr(movie, 'overview', ''),
                        'release_date': release_date,
                        'poster_path': movie.get('poster_path', '') if isinstance(movie, dict) else getattr(movie, 'poster_path', ''),
                        'vote_average': movie.get('vote_average', 0) if isinstance(movie, dict) else getattr(movie, 'vote_average', 0),
                        'vote_count': movie.get('vote_count', 0) if isinstance(movie, dict) else getattr(movie, 'vote_count', 0)
                    }
                )
                movie_obj.requested_on_radarr = True
                movie_obj.save()
            except Exception as e:
                print(f"Error updating movie status: {e}")
            return True  # Return True since movie is already in Radarr
        
        # Movie doesn't exist in Radarr, proceed with request
        success = self.radarr_service.request_movie(movie, quality_profile_id)
        if success:
            # Update or create the movie record to track request status
            try:
                # Handle release_date properly
                if isinstance(movie, dict):
                    release_date = movie.get('release_date')
                else:
                    release_date = getattr(movie, 'release_date', None)
                
                # Convert year-only dates to proper format
                if release_date and len(str(release_date)) == 4:
                    try:
                        release_date = f"{release_date}-01-01"
                    except:
                        release_date = None
                elif release_date and not isinstance(release_date, str):
                    release_date = None
                
                movie_obj, created = Movie.objects.get_or_create(
                    tmdb_id=tmdb_id,
                    defaults={
                        'title': movie.get('title') if isinstance(movie, dict) else getattr(movie, 'title', ''),
                        'overview': movie.get('overview', '') if isinstance(movie, dict) else getattr(movie, 'overview', ''),
                        'release_date': release_date,
                        'poster_path': movie.get('poster_path', '') if isinstance(movie, dict) else getattr(movie, 'poster_path', ''),
                        'vote_average': movie.get('vote_average', 0) if isinstance(movie, dict) else getattr(movie, 'vote_average', 0),
                        'vote_count': movie.get('vote_count', 0) if isinstance(movie, dict) else getattr(movie, 'vote_count', 0)
                    }
                )
                movie_obj.requested_on_radarr = True
                movie_obj.save()
            except Exception as e:
                print(f"Error updating movie request status: {e}")
        return success


class TVShowService:
    def __init__(self):
        self.sonarr_service = SonarrService()
    
    def request_tv_show_on_sonarr(self, tv_show_data, quality_profile_id=None, selected_seasons=None):
        """Request a TV show on Sonarr using TMDB data"""
        if not tv_show_data:
            return False
        
        title = tv_show_data.get('name') or tv_show_data.get('title', '')
        if not title:
            return False
        
        tmdb_id = tv_show_data.get('id')
        return self.sonarr_service.request_series(
            title, 
            tmdb_id=tmdb_id, 
            quality_profile_id=quality_profile_id,
            selected_seasons=selected_seasons
        )


class RecommendationService:
    def __init__(self):
        self.movie_service = MovieService()
        self.gemini_service = GeminiService()
    
    def generate_recommendations(self, user, limit=10, library_context=None):
        # Get user's ratings and preferences
        user_ratings = UserRating.objects.filter(user=user).select_related('movie')
        
        if not user_ratings.exists():
            # Return popular movies for new users - fetch directly from TMDB
            from movies.tmdb_service import TMDBService
            tmdb_service = TMDBService()
            popular_data = tmdb_service.get_popular_movies(page=1)
            if popular_data and popular_data.get('results'):
                # Return TMDB data directly instead of creating database recommendations
                popular_movies = popular_data['results'][:limit]
                # Add recommendation metadata to each movie
                for movie in popular_movies:
                    movie['recommendation_reason'] = "Popular movies"
                    movie['recommendation_score'] = 85.0
                return popular_movies
            else:
                # Fallback to empty recommendations if TMDB fails
                return []
        
        # Analyze user preferences
        high_rated_movies = user_ratings.filter(rating__gte=8)
        preferred_genres = self._get_preferred_genres(high_rated_movies)
        
        # Get recommendations based on collaborative filtering
        collaborative_recommendations = self._get_collaborative_recommendations(user, preferred_genres)
        
        # Get AI-powered recommendations using Gemini
        if settings.GOOGLE_GEMINI_API_KEY:
            ai_recommendations = self._get_gemini_recommendations(
                user, 
                high_rated_movies.values_list('movie__title', flat=True),
                library_context
            )
            collaborative_recommendations.extend(ai_recommendations)
        
        # Remove duplicates and movies user has already rated
        rated_movie_ids = user_ratings.values_list('movie_id', flat=True)
        recommendations = []
        seen_ids = set()
        
        for movie, reason in collaborative_recommendations:
            if movie.id not in rated_movie_ids and movie.id not in seen_ids:
                recommendations.append((movie, reason))
                seen_ids.add(movie.id)
                if len(recommendations) >= limit:
                    break
        
        return self._create_recommendations(user, [r[0] for r in recommendations], 
                                          [r[1] for r in recommendations])
    
    def _get_preferred_genres(self, high_rated_movies):
        genre_counts = {}
        for rating in high_rated_movies:
            for genre in rating.movie.genres.all():
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        return sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    def _get_collaborative_recommendations(self, user, preferred_genres):
        recommendations = []
        
        # Find similar users
        user_ratings = UserRating.objects.filter(user=user)
        user_movie_ratings = {r.movie_id: r.rating for r in user_ratings}
        
        similar_users = []
        all_users = User.objects.exclude(id=user.id)
        
        for other_user in all_users:
            other_ratings = UserRating.objects.filter(user=other_user)
            other_movie_ratings = {r.movie_id: r.rating for r in other_ratings}
            
            # Calculate similarity (simplified Pearson correlation)
            common_movies = set(user_movie_ratings.keys()) & set(other_movie_ratings.keys())
            if len(common_movies) >= 3:
                similarity = self._calculate_similarity(
                    user_movie_ratings, other_movie_ratings, common_movies
                )
                if similarity > 0.5:
                    similar_users.append((other_user, similarity))
        
        # Get recommendations from similar users
        similar_users.sort(key=lambda x: x[1], reverse=True)
        for similar_user, similarity in similar_users[:5]:
            high_rated_by_similar = UserRating.objects.filter(
                user=similar_user, rating__gte=8
            ).exclude(movie_id__in=user_movie_ratings.keys())
            
            for rating in high_rated_by_similar:
                recommendations.append((
                    rating.movie,
                    f"Recommended by similar user (similarity: {similarity:.2f})"
                ))
        
        # Add movies from preferred genres
        for genre, count in preferred_genres:
            genre_movies = Movie.objects.filter(genres=genre).order_by('-vote_average')[:5]
            for movie in genre_movies:
                if movie.id not in user_movie_ratings:
                    recommendations.append((movie, f"Based on your interest in {genre.name}"))
        
        return recommendations
    
    def _calculate_similarity(self, user1_ratings, user2_ratings, common_movies):
        if not common_movies:
            return 0
        
        sum1 = sum(user1_ratings[movie] for movie in common_movies)
        sum2 = sum(user2_ratings[movie] for movie in common_movies)
        
        sum1_sq = sum(user1_ratings[movie] ** 2 for movie in common_movies)
        sum2_sq = sum(user2_ratings[movie] ** 2 for movie in common_movies)
        
        sum_products = sum(user1_ratings[movie] * user2_ratings[movie] for movie in common_movies)
        
        n = len(common_movies)
        numerator = sum_products - (sum1 * sum2 / n)
        denominator = ((sum1_sq - sum1 ** 2 / n) * (sum2_sq - sum2 ** 2 / n)) ** 0.5
        
        if denominator == 0:
            return 0
        
        return numerator / denominator
    
    def _get_gemini_recommendations(self, user, high_rated_titles, library_context=None):
        try:
            # Use Gemini service for personalized recommendations based on user's highly rated movies
            # If the user has highly rated movies, include them in the mood description
            if high_rated_titles:
                mood_description = f"similar to movies like {', '.join(list(high_rated_titles)[:5])}"
            else:
                mood_description = "entertaining and well-rated"
            
            preferences = {
                'genres': ['drama', 'action', 'comedy'],  # Default genres
                'mood': mood_description,
                'year_range': '1980-2024'
            }
            
            # Get recommendations from Gemini using the user's preferences and library context
            gemini_recommendations = self.gemini_service.get_personalized_recommendations(
                preferences, library_context
            )
            
            # Convert Gemini recommendations to the format expected by collaborative filtering
            recommendations = []
            for rec in gemini_recommendations:
                # Try to find the movie in our database
                movie = Movie.objects.filter(title__icontains=rec['title']).first()
                if movie:
                    reason = rec.get('ai_reason', 'AI recommended based on your preferences')
                    recommendations.append((movie, reason))
            
            return recommendations
        except Exception as e:
            print(f"Error getting Gemini recommendations: {e}")
            return []
    
    def _create_recommendations(self, user, movies, reasons=None):
        if reasons is None:
            reasons = ["Recommended for you"] * len(movies)
        
        recommendations = []
        for i, movie in enumerate(movies):
            reason = reasons[i] if i < len(reasons) else "Recommended for you"
            recommendation, created = MovieRecommendation.objects.get_or_create(
                user=user,
                movie=movie,
                defaults={
                    'score': 85.0,  # Default score
                    'reason': reason
                }
            )
            recommendations.append(recommendation)
        
        return recommendations