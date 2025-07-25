import math
import random
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Set
from django.contrib.auth.models import User
from django.db.models import Q, Count, Avg, F, Case, When, FloatField
from django.utils import timezone
from movies.models import Movie, UserWatchlist as MovieWatchlist, UserRating, MovieRecommendation
from tv_shows.models import TVShow
from recommendations.models import UserNegativeFeedback
from .models import (
    UserRecommendationSettings, 
    RecommendationProfile, 
    CachedRecommendation,
    RecommendationFeedback,
    MovieSimilarity,
    TVShowSimilarity,
    ContentFeatures,
    UserPreferenceLearning
)


class SmartRecommendationEngine:
    """
    Advanced recommendation engine that combines content-based filtering,
    collaborative filtering, popularity analysis, and niche discovery.
    """
    
    def __init__(self, user: User):
        self.user = user
        self.settings = self._get_or_create_settings()
        self.profile = self._get_or_create_profile()
        
    def _get_or_create_settings(self) -> UserRecommendationSettings:
        """Get or create user recommendation settings"""
        settings, created = UserRecommendationSettings.objects.get_or_create(
            user=self.user,
            defaults={
                'popular_vs_niche_balance': 0.5,
                'genre_diversity': 0.7,
                'release_year_preference': 0.5,
                'runtime_flexibility': 0.6,
                'movie_weight': 0.5,
                'include_rewatches': False,
                'minimum_rating': 6.0,
                'prefer_recent_releases': True,
                'prefer_highly_rated': True,
            }
        )
        return settings
    
    def _get_or_create_profile(self) -> RecommendationProfile:
        """Get or create user recommendation profile"""
        profile, created = RecommendationProfile.objects.get_or_create(
            user=self.user,
            defaults={
                'genre_preferences': {},
                'preferred_actors': [],
                'preferred_directors': [],
                'avg_user_rating': 0.0,
                'rating_count': 0,
                'total_movies_watched': 0,
                'total_tv_shows_watched': 0,
                'watchlist_size': 0,
            }
        )
        
        if created or profile.needs_refresh():
            self._analyze_user_preferences(profile)
            
        return profile
    
    def get_smart_recommendations(self, limit: int = 20, refresh: bool = False) -> List[Dict]:
        """
        Get smart recommendations for the user with 50/50 popular/niche balance
        """
        # Check if we need to refresh or have valid cached recommendations
        if not refresh:
            cached_recs = self._get_valid_cached_recommendations(limit)
            if len(cached_recs) >= limit:
                return self._format_recommendations(cached_recs)
        
        # Generate new recommendations
        recommendations = self._generate_recommendations(limit)
        
        # Cache the recommendations
        self._cache_recommendations(recommendations)
        
        return recommendations
    
    def _get_valid_cached_recommendations(self, limit: int) -> List[CachedRecommendation]:
        """Get valid cached recommendations that haven't expired"""
        current_settings_hash = self.settings.settings_hash()
        
        return list(CachedRecommendation.objects.filter(
            user=self.user,
            expires_at__gt=timezone.now(),
            user_settings_hash=current_settings_hash
        ).order_by('-score')[:limit])
    
    def _generate_recommendations(self, limit: int) -> List[Dict]:
        """Generate fresh recommendations using the hybrid algorithm"""
        # Calculate split between movies and TV shows
        movie_limit = int(limit * self.settings.movie_weight)
        tv_limit = limit - movie_limit
        
        # Calculate split between popular and niche (50/50 as requested)
        popular_movie_limit = int(movie_limit * 0.5)
        niche_movie_limit = movie_limit - popular_movie_limit
        popular_tv_limit = int(tv_limit * 0.5)
        niche_tv_limit = tv_limit - popular_tv_limit
        
        recommendations = []
        
        # Get movie recommendations
        if movie_limit > 0:
            popular_movies = self._get_popular_recommendations('movie', popular_movie_limit)
            niche_movies = self._get_niche_recommendations('movie', niche_movie_limit)
            recommendations.extend(popular_movies + niche_movies)
        
        # Get TV show recommendations
        if tv_limit > 0:
            popular_tv = self._get_popular_recommendations('tv', popular_tv_limit)
            niche_tv = self._get_niche_recommendations('tv', niche_tv_limit)
            recommendations.extend(popular_tv + niche_tv)
        
        # Shuffle to mix popular and niche
        random.shuffle(recommendations)
        
        # Apply diversity injection and final scoring
        recommendations = self._apply_diversity_injection(recommendations)
        recommendations = self._apply_final_scoring(recommendations)
        
        # Sort by final score and return top recommendations
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:limit]
    
    def _get_popular_recommendations(self, content_type: str, limit: int) -> List[Dict]:
        """Get popular recommendations based on user preferences"""
        if content_type == 'movie':
            return self._get_popular_movies(limit)
        else:
            return self._get_popular_tv_shows(limit)
    
    def _get_niche_recommendations(self, content_type: str, limit: int) -> List[Dict]:
        """Get niche/hidden gem recommendations"""
        if content_type == 'movie':
            return self._get_niche_movies(limit)
        else:
            return self._get_niche_tv_shows(limit)
    
    def _get_popular_movies(self, limit: int) -> List[Dict]:
        """Get popular movie recommendations"""
        # Get user's excluded content
        excluded_ids = self._get_excluded_movie_ids()
        
        # Base query for popular movies
        movies = Movie.objects.filter(
            vote_average__gte=self.settings.minimum_rating,
            popularity__gte=50.0  # Popular threshold
        ).exclude(tmdb_id__in=excluded_ids)
        
        # Apply genre preferences
        movies = self._apply_genre_filter(movies, 'movie')
        
        # Apply release year preferences
        movies = self._apply_release_year_filter(movies)
        
        # Order by popularity and rating combination
        movies = movies.annotate(
            score=F('popularity') * 0.7 + F('vote_average') * 0.3
        ).order_by('-score')[:limit * 3]  # Get more to allow for diversity
        
        # Convert to recommendation format
        recommendations = []
        for movie in movies:
            score = self._calculate_content_based_score(movie, 'movie')
            recommendations.append({
                'content_type': 'movie',
                'tmdb_id': movie.tmdb_id,
                'title': movie.title,
                'poster_path': movie.poster_path,
                'overview': movie.overview,
                'vote_average': float(movie.vote_average) if movie.vote_average else 0.0,
                'popularity': float(movie.popularity) if movie.popularity else 0.0,
                'release_date': movie.release_date,
                'score': score,
                'recommendation_type': 'popular',
                'explanation': self._generate_explanation(movie, 'movie', 'popular'),
                'genres': [genre.name for genre in movie.genres.all()],
            })
        
        return recommendations[:limit]
    
    def _get_niche_movies(self, limit: int) -> List[Dict]:
        """Get niche/hidden gem movie recommendations"""
        excluded_ids = self._get_excluded_movie_ids()
        
        # Niche movies: high rating, lower popularity
        movies = Movie.objects.filter(
            vote_average__gte=self.settings.minimum_rating + 0.5,  # Higher rating threshold
            popularity__lt=50.0,  # Lower popularity
            vote_count__gte=100   # But still have some votes for credibility
        ).exclude(tmdb_id__in=excluded_ids)
        
        # Apply genre preferences
        movies = self._apply_genre_filter(movies, 'movie')
        
        # Apply release year preferences
        movies = self._apply_release_year_filter(movies)
        
        # Order by rating with some randomness for discovery
        movies = movies.annotate(
            niche_score=F('vote_average') * 0.8 + (50.0 - F('popularity')) * 0.2
        ).order_by('-niche_score')[:limit * 3]
        
        recommendations = []
        for movie in movies:
            score = self._calculate_content_based_score(movie, 'movie')
            recommendations.append({
                'content_type': 'movie',
                'tmdb_id': movie.tmdb_id,
                'title': movie.title,
                'poster_path': movie.poster_path,
                'overview': movie.overview,
                'vote_average': float(movie.vote_average) if movie.vote_average else 0.0,
                'popularity': float(movie.popularity) if movie.popularity else 0.0,
                'release_date': movie.release_date,
                'score': score,
                'recommendation_type': 'niche',
                'explanation': self._generate_explanation(movie, 'movie', 'niche'),
                'genres': [genre.name for genre in movie.genres.all()],
            })
        
        return recommendations[:limit]
    
    def _get_popular_tv_shows(self, limit: int) -> List[Dict]:
        """Get popular TV show recommendations"""
        excluded_ids = self._get_excluded_tv_ids()
        
        tv_shows = TVShow.objects.filter(
            vote_average__gte=self.settings.minimum_rating,
            popularity__gte=30.0  # TV shows generally have lower popularity scores
        ).exclude(tmdb_id__in=excluded_ids)
        
        tv_shows = self._apply_genre_filter(tv_shows, 'tv')
        tv_shows = self._apply_release_year_filter(tv_shows, date_field='first_air_date')
        
        tv_shows = tv_shows.annotate(
            score=F('popularity') * 0.7 + F('vote_average') * 0.3
        ).order_by('-score')[:limit * 3]
        
        recommendations = []
        for show in tv_shows:
            score = self._calculate_content_based_score(show, 'tv')
            recommendations.append({
                'content_type': 'tv',
                'tmdb_id': show.tmdb_id,
                'title': show.name,
                'poster_path': show.poster_path,
                'overview': show.overview,
                'vote_average': float(show.vote_average) if show.vote_average else 0.0,
                'popularity': float(show.popularity) if show.popularity else 0.0,
                'release_date': show.first_air_date,
                'score': score,
                'recommendation_type': 'popular',
                'explanation': self._generate_explanation(show, 'tv', 'popular'),
                'genres': [genre.name for genre in show.genres.all()],
            })
        
        return recommendations[:limit]
    
    def _get_niche_tv_shows(self, limit: int) -> List[Dict]:
        """Get niche/hidden gem TV show recommendations"""
        excluded_ids = self._get_excluded_tv_ids()
        
        tv_shows = TVShow.objects.filter(
            vote_average__gte=self.settings.minimum_rating + 0.5,
            popularity__lt=30.0,
            vote_count__gte=50
        ).exclude(tmdb_id__in=excluded_ids)
        
        tv_shows = self._apply_genre_filter(tv_shows, 'tv')
        tv_shows = self._apply_release_year_filter(tv_shows, date_field='first_air_date')
        
        tv_shows = tv_shows.annotate(
            niche_score=F('vote_average') * 0.8 + (30.0 - F('popularity')) * 0.2
        ).order_by('-niche_score')[:limit * 3]
        
        recommendations = []
        for show in tv_shows:
            score = self._calculate_content_based_score(show, 'tv')
            recommendations.append({
                'content_type': 'tv',
                'tmdb_id': show.tmdb_id,
                'title': show.name,
                'poster_path': show.poster_path,
                'overview': show.overview,
                'vote_average': float(show.vote_average) if show.vote_average else 0.0,
                'popularity': float(show.popularity) if show.popularity else 0.0,
                'release_date': show.first_air_date,
                'score': score,
                'recommendation_type': 'niche',
                'explanation': self._generate_explanation(show, 'tv', 'niche'),
                'genres': [genre.name for genre in show.genres.all()],
            })
        
        return recommendations[:limit]
    
    def _get_excluded_movie_ids(self) -> Set[int]:
        """Get movie IDs that should be excluded from recommendations"""
        excluded = set()
        
        # Exclude movies in watchlist
        excluded.update(
            MovieWatchlist.objects.filter(user=self.user).values_list('movie__tmdb_id', flat=True)
        )
        
        # Exclude movies marked as not interested
        excluded.update(
            UserNegativeFeedback.objects.filter(
                user=self.user, content_type='movie'
            ).values_list('tmdb_id', flat=True)
        )
        
        # Exclude movies with negative feedback
        excluded.update(
            RecommendationFeedback.objects.filter(
                user=self.user, 
                content_type='movie',
                feedback_type__in=['negative', 'not_interested']
            ).values_list('tmdb_id', flat=True)
        )
        
        return excluded
    
    def _get_excluded_tv_ids(self) -> Set[int]:
        """Get TV show IDs that should be excluded from recommendations"""
        excluded = set()
        
        # Exclude TV shows marked as not interested
        excluded.update(
            UserNegativeFeedback.objects.filter(
                user=self.user, content_type='tv'
            ).values_list('tmdb_id', flat=True)
        )
        
        # Exclude TV shows with negative feedback
        excluded.update(
            RecommendationFeedback.objects.filter(
                user=self.user, 
                content_type='tv',
                feedback_type__in=['negative', 'not_interested']
            ).values_list('tmdb_id', flat=True)
        )
        
        return excluded
    
    def _apply_genre_filter(self, queryset, content_type: str):
        """Apply genre preferences to filter content"""
        if not self.profile.genre_preferences:
            return queryset
        
        # Get preferred genres (positive weights)
        preferred_genres = [
            int(genre_id) for genre_id, weight in self.profile.genre_preferences.items() 
            if weight > 0.1
        ]
        
        if preferred_genres:
            return queryset.filter(genres__id__in=preferred_genres).distinct()
        
        return queryset
    
    def _apply_release_year_filter(self, queryset, date_field: str = 'release_date'):
        """Apply release year preferences"""
        current_year = datetime.now().year
        
        if self.settings.prefer_recent_releases:
            # Prefer content from last 10 years
            min_year = current_year - 10
            return queryset.filter(**{f'{date_field}__year__gte': min_year})
        
        return queryset
    
    def _calculate_content_based_score(self, content, content_type: str) -> float:
        """Calculate content-based similarity score"""
        score = 0.0
        
        # Base rating score (40% weight)
        if hasattr(content, 'vote_average') and content.vote_average:
            score += float(content.vote_average) * 0.4
        
        # Popularity score (20% weight)
        if hasattr(content, 'popularity') and content.popularity:
            popularity_score = min(float(content.popularity) / 100.0, 1.0)  # Normalize to 0-1
            score += popularity_score * 0.2
        
        # Genre preference score (30% weight)
        genre_score = self._calculate_genre_preference_score(content)
        score += genre_score * 0.3
        
        # Recency bonus (10% weight)
        recency_score = self._calculate_recency_score(content, content_type)
        score += recency_score * 0.1
        
        return min(score, 10.0)  # Cap at 10.0
    
    def _calculate_genre_preference_score(self, content) -> float:
        """Calculate how well content matches user's genre preferences"""
        if not self.profile.genre_preferences:
            return 0.5  # Neutral score if no preferences
        
        content_genres = set(content.genres.values_list('id', flat=True))
        if not content_genres:
            return 0.3  # Slight penalty for no genre info
        
        total_weight = 0.0
        total_score = 0.0
        
        for genre_id in content_genres:
            weight = self.profile.genre_preferences.get(str(genre_id), 0.5)
            total_weight += 1.0
            total_score += weight
        
        return total_score / total_weight if total_weight > 0 else 0.5
    
    def _calculate_recency_score(self, content, content_type: str) -> float:
        """Calculate recency score based on release date and user preferences"""
        date_field = 'release_date' if content_type == 'movie' else 'first_air_date'
        release_date = getattr(content, date_field, None)
        
        if not release_date:
            return 0.5  # Neutral score for unknown dates
        
        current_year = datetime.now().year
        release_year = release_date.year
        years_ago = current_year - release_year
        
        if self.settings.prefer_recent_releases:
            # Exponential decay for older content
            return max(0.1, 1.0 - (years_ago / 20.0))
        else:
            # Flat score regardless of age
            return 0.5
    
    def _apply_diversity_injection(self, recommendations: List[Dict]) -> List[Dict]:
        """Apply diversity injection to prevent echo chambers"""
        if len(recommendations) <= 1:
            return recommendations
        
        # Group by genres
        genre_counts = defaultdict(int)
        for rec in recommendations:
            for genre in rec.get('genres', []):
                genre_counts[genre] += 1
        
        # Apply diversity bonus/penalty
        for rec in recommendations:
            diversity_bonus = 0.0
            for genre in rec.get('genres', []):
                # Reduce score for over-represented genres
                if genre_counts[genre] > 3:
                    diversity_bonus -= 0.5
                # Boost score for under-represented genres
                elif genre_counts[genre] == 1:
                    diversity_bonus += 0.3
            
            rec['diversity_bonus'] = diversity_bonus
            rec['score'] += diversity_bonus
        
        return recommendations
    
    def _apply_final_scoring(self, recommendations: List[Dict]) -> List[Dict]:
        """Apply final scoring adjustments"""
        for rec in recommendations:
            # Apply user preference adjustments
            preference_adjustment = self._calculate_user_preference_adjustment(rec)
            rec['user_preference_score'] = preference_adjustment
            rec['score'] += preference_adjustment
            
            # Ensure score is within reasonable bounds
            rec['score'] = max(0.0, min(10.0, rec['score']))
        
        return recommendations
    
    def _calculate_user_preference_adjustment(self, recommendation: Dict) -> float:
        """Calculate user-specific preference adjustment"""
        adjustment = 0.0
        
        # Boost based on user's rating history
        if self.profile.avg_user_rating > 7.0:
            # User likes high-quality content
            if recommendation['vote_average'] > 8.0:
                adjustment += 0.5
        
        # Boost based on recommendation type preference
        rec_type = recommendation['recommendation_type']
        if rec_type == 'popular' and self.settings.popular_vs_niche_balance > 0.6:
            adjustment += 0.3
        elif rec_type == 'niche' and self.settings.popular_vs_niche_balance < 0.4:
            adjustment += 0.3
        
        return adjustment
    
    def _generate_explanation(self, content, content_type: str, rec_type: str) -> str:
        """Generate explanation for why content was recommended"""
        explanations = []
        
        if rec_type == 'popular':
            explanations.append("Popular among users like you")
        elif rec_type == 'niche':
            explanations.append("Hidden gem with great ratings")
        
        # Add genre-based explanation
        if hasattr(content, 'genres'):
            genres = [genre.name for genre in content.genres.all()[:2]]
            if genres and self.profile.genre_preferences:
                preferred_genres = [
                    genre for genre, weight in self.profile.genre_preferences.items() 
                    if weight > 0.6
                ]
                if preferred_genres:
                    explanations.append(f"Matches your interest in {', '.join(genres)}")
        
        # Add rating explanation
        if hasattr(content, 'vote_average') and content.vote_average and content.vote_average >= 8.0:
            explanations.append("Highly rated by critics and audiences")
        
        return "; ".join(explanations) if explanations else "Recommended for you"
    
    def _analyze_user_preferences(self, profile: RecommendationProfile):
        """Analyze user's behavior to update preference profile"""
        # Analyze genre preferences from ratings and watchlist
        genre_analysis = self._analyze_genre_preferences()
        profile.genre_preferences = genre_analysis
        
        # Analyze rating patterns
        user_ratings = UserRating.objects.filter(user=self.user)
        if user_ratings.exists():
            profile.avg_user_rating = user_ratings.aggregate(Avg('rating'))['rating__avg'] or 0.0
            profile.rating_count = user_ratings.count()
        
        # Update viewing statistics
        profile.total_movies_watched = MovieWatchlist.objects.filter(user=self.user).count()
        profile.watchlist_size = profile.total_movies_watched
        
        profile.save()
    
    def _analyze_genre_preferences(self) -> Dict[str, float]:
        """Analyze user's genre preferences from ratings and watchlist"""
        genre_weights = defaultdict(float)
        genre_counts = defaultdict(int)
        
        # Analyze from user ratings
        rated_movies = UserRating.objects.filter(user=self.user).select_related('movie')
        for rating in rated_movies:
            weight = (rating.rating - 5.0) / 5.0  # Convert 1-10 scale to -0.8 to 1.0
            for genre in rating.movie.genres.all():
                genre_weights[str(genre.id)] += weight
                genre_counts[str(genre.id)] += 1
        
        # Analyze from watchlist (positive signal)
        watchlist_movies = MovieWatchlist.objects.filter(user=self.user).select_related('movie')
        for item in watchlist_movies:
            for genre in item.movie.genres.all():
                genre_weights[str(genre.id)] += 0.3  # Moderate positive signal
                genre_counts[str(genre.id)] += 1
        
        # Analyze from negative feedback (negative signal)
        negative_feedback = UserNegativeFeedback.objects.filter(
            user=self.user, 
            reason='not_my_genre'
        )
        for feedback in negative_feedback:
            try:
                if feedback.content_type == 'movie':
                    movie = Movie.objects.get(tmdb_id=feedback.tmdb_id)
                    for genre in movie.genres.all():
                        genre_weights[str(genre.id)] -= 0.5  # Strong negative signal
                        genre_counts[str(genre.id)] += 1
            except Movie.DoesNotExist:
                continue
        
        # Normalize weights
        normalized_weights = {}
        for genre_id, total_weight in genre_weights.items():
            count = genre_counts[genre_id]
            if count > 0:
                avg_weight = total_weight / count
                # Normalize to 0-1 scale
                normalized_weight = max(0.0, min(1.0, (avg_weight + 1.0) / 2.0))
                normalized_weights[genre_id] = normalized_weight
        
        return normalized_weights
    
    def _cache_recommendations(self, recommendations: List[Dict]):
        """Cache recommendations for future use"""
        # Clear existing cached recommendations
        CachedRecommendation.objects.filter(user=self.user).delete()
        
        # Create new cached recommendations
        cached_recs = []
        expire_time = timezone.now() + timedelta(days=self.settings.auto_refresh_days)
        settings_hash = self.settings.settings_hash()
        
        for rec in recommendations:
            cached_recs.append(CachedRecommendation(
                user=self.user,
                content_type=rec['content_type'],
                tmdb_id=rec['tmdb_id'],
                score=rec['score'],
                explanation=rec['explanation'],
                recommendation_type=rec['recommendation_type'],
                content_score=rec.get('content_score', 0.0),
                popularity_score=rec.get('popularity_score', 0.0),
                user_preference_score=rec.get('user_preference_score', 0.0),
                diversity_bonus=rec.get('diversity_bonus', 0.0),
                user_settings_hash=settings_hash,
                expires_at=expire_time,
            ))
        
        CachedRecommendation.objects.bulk_create(cached_recs)
    
    def _format_recommendations(self, cached_recs: List[CachedRecommendation]) -> List[Dict]:
        """Format cached recommendations for API response"""
        recommendations = []
        
        for cached_rec in cached_recs:
            # Get the actual content object
            try:
                if cached_rec.content_type == 'movie':
                    content = Movie.objects.get(tmdb_id=cached_rec.tmdb_id)
                    title = content.title
                    poster_path = content.poster_path
                    overview = content.overview
                    vote_average = float(content.vote_average) if content.vote_average else 0.0
                    popularity = float(content.popularity) if content.popularity else 0.0
                    release_date = content.release_date
                    genres = [genre.name for genre in content.genres.all()]
                else:
                    content = TVShow.objects.get(tmdb_id=cached_rec.tmdb_id)
                    title = content.name
                    poster_path = content.poster_path
                    overview = content.overview
                    vote_average = float(content.vote_average) if content.vote_average else 0.0
                    popularity = float(content.popularity) if content.popularity else 0.0
                    release_date = content.first_air_date
                    genres = [genre.name for genre in content.genres.all()]
                
                recommendations.append({
                    'content_type': cached_rec.content_type,
                    'tmdb_id': cached_rec.tmdb_id,
                    'title': title,
                    'poster_path': poster_path,
                    'overview': overview,
                    'vote_average': vote_average,
                    'popularity': popularity,
                    'release_date': release_date,
                    'score': float(cached_rec.score),
                    'recommendation_type': cached_rec.recommendation_type,
                    'explanation': cached_rec.explanation,
                    'genres': genres,
                })
            
            except (Movie.DoesNotExist, TVShow.DoesNotExist):
                # Content no longer exists, skip
                continue
        
        return recommendations
    
    def update_settings(self, **kwargs):
        """Update user recommendation settings"""
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        
        self.settings.last_refreshed = timezone.now()
        self.settings.save()
        
        # Clear cached recommendations since settings changed
        CachedRecommendation.objects.filter(user=self.user).delete()
    
    def record_feedback(self, tmdb_id: int, content_type: str, feedback_type: str, 
                       detailed_reason: str = None, additional_feedback: str = ""):
        """Record user feedback on a recommendation"""
        RecommendationFeedback.objects.update_or_create(
            user=self.user,
            tmdb_id=tmdb_id,
            content_type=content_type,
            defaults={
                'feedback_type': feedback_type,
                'detailed_reason': detailed_reason,
                'additional_feedback': additional_feedback,
                'recommendation_explanation': "",  # Could be populated from cached rec
                'recommendation_score': 0.0,
                'user_settings_at_time': {
                    'popular_vs_niche_balance': self.settings.popular_vs_niche_balance,
                    'genre_diversity': self.settings.genre_diversity,
                }
            }
        )
        
        # Update cached recommendation interaction tracking
        CachedRecommendation.objects.filter(
            user=self.user,
            tmdb_id=tmdb_id,
            content_type=content_type
        ).update(
            clicked=feedback_type in ['positive', 'added_to_watchlist', 'requested'],
            added_to_watchlist=feedback_type == 'added_to_watchlist',
            requested=feedback_type == 'requested'
        )
