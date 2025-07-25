from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import json
import hashlib


class UserRecommendationSettings(models.Model):
    """User customization settings for the smart recommendation algorithm"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='smart_settings')
    
    # Algorithm preference controls (0.0 - 1.0)
    popular_vs_niche_balance = models.FloatField(default=0.5, help_text="0=all niche, 1=all popular")
    genre_diversity = models.FloatField(default=0.7, help_text="How much to vary genres")
    release_year_preference = models.FloatField(default=0.5, help_text="0=older, 1=newer")
    runtime_flexibility = models.FloatField(default=0.6, help_text="Strict vs flexible runtime matching")
    
    # Content type preferences
    movie_weight = models.FloatField(default=0.5, help_text="0=TV only, 1=Movies only")
    include_rewatches = models.BooleanField(default=False, help_text="Include already watched")
    
    # Refresh settings
    auto_refresh_days = models.IntegerField(default=7, help_text="Auto-refresh recommendations")
    last_refreshed = models.DateTimeField(auto_now_add=True)
    
    # Advanced preferences
    minimum_rating = models.FloatField(default=6.0, help_text="Minimum TMDB rating")
    prefer_recent_releases = models.BooleanField(default=True)
    prefer_highly_rated = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - Smart Recommendation Settings"
    
    def settings_hash(self):
        """Generate hash of current settings for cache invalidation"""
        settings_data = {
            'popular_vs_niche_balance': self.popular_vs_niche_balance,
            'genre_diversity': self.genre_diversity,
            'release_year_preference': self.release_year_preference,
            'runtime_flexibility': self.runtime_flexibility,
            'movie_weight': self.movie_weight,
            'include_rewatches': self.include_rewatches,
            'minimum_rating': self.minimum_rating,
            'prefer_recent_releases': self.prefer_recent_releases,
            'prefer_highly_rated': self.prefer_highly_rated,
        }
        return hashlib.md5(json.dumps(settings_data, sort_keys=True).encode()).hexdigest()


class RecommendationProfile(models.Model):
    """Cached user preference analysis for efficient recommendations"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='recommendation_profile')
    
    # Genre preferences (JSON field storing genre_id: weight pairs)
    genre_preferences = models.JSONField(default=dict, help_text="Genre preferences based on user behavior")
    
    # Actor/Director preferences
    preferred_actors = models.JSONField(default=list, help_text="List of preferred actor names")
    preferred_directors = models.JSONField(default=list, help_text="List of preferred director names")
    
    # Runtime preferences
    avg_preferred_runtime_movie = models.IntegerField(null=True, blank=True)
    avg_preferred_runtime_tv = models.IntegerField(null=True, blank=True)
    
    # Rating patterns
    avg_user_rating = models.FloatField(default=0.0)
    rating_count = models.IntegerField(default=0)
    
    # Release year preferences
    preferred_decade_start = models.IntegerField(null=True, blank=True)
    preferred_decade_end = models.IntegerField(null=True, blank=True)
    
    # Behavior patterns
    total_movies_watched = models.IntegerField(default=0)
    total_tv_shows_watched = models.IntegerField(default=0)
    watchlist_size = models.IntegerField(default=0)
    
    # Profile analysis timestamp
    last_analyzed = models.DateTimeField(auto_now=True)
    analysis_version = models.CharField(max_length=10, default="1.0")
    
    def __str__(self):
        return f"{self.user.username} - Recommendation Profile"
    
    def needs_refresh(self):
        """Check if profile needs to be refreshed"""
        return timezone.now() - self.last_analyzed > timedelta(days=7)


class MovieSimilarity(models.Model):
    """Precomputed movie similarity scores for efficient recommendations"""
    movie1_tmdb_id = models.IntegerField(db_index=True)
    movie2_tmdb_id = models.IntegerField(db_index=True)
    similarity_score = models.FloatField(help_text="Cosine similarity score (0.0 - 1.0)")
    
    # Similarity factors
    genre_similarity = models.FloatField(default=0.0)
    cast_similarity = models.FloatField(default=0.0)
    director_similarity = models.FloatField(default=0.0)
    rating_similarity = models.FloatField(default=0.0)
    
    # Metadata
    computed_at = models.DateTimeField(auto_now_add=True)
    algorithm_version = models.CharField(max_length=10, default="1.0")
    
    class Meta:
        unique_together = ['movie1_tmdb_id', 'movie2_tmdb_id']
        indexes = [
            models.Index(fields=['movie1_tmdb_id', 'similarity_score']),
            models.Index(fields=['movie2_tmdb_id', 'similarity_score']),
        ]
    
    def __str__(self):
        return f"Similarity: {self.movie1_tmdb_id} <-> {self.movie2_tmdb_id} ({self.similarity_score:.3f})"


class TVShowSimilarity(models.Model):
    """Precomputed TV show similarity scores for efficient recommendations"""
    show1_tmdb_id = models.IntegerField(db_index=True)
    show2_tmdb_id = models.IntegerField(db_index=True)
    similarity_score = models.FloatField(help_text="Cosine similarity score (0.0 - 1.0)")
    
    # Similarity factors
    genre_similarity = models.FloatField(default=0.0)
    cast_similarity = models.FloatField(default=0.0)
    creator_similarity = models.FloatField(default=0.0)
    rating_similarity = models.FloatField(default=0.0)
    
    # Metadata
    computed_at = models.DateTimeField(auto_now_add=True)
    algorithm_version = models.CharField(max_length=10, default="1.0")
    
    class Meta:
        unique_together = ['show1_tmdb_id', 'show2_tmdb_id']
        indexes = [
            models.Index(fields=['show1_tmdb_id', 'similarity_score']),
            models.Index(fields=['show2_tmdb_id', 'similarity_score']),
        ]
    
    def __str__(self):
        return f"TV Similarity: {self.show1_tmdb_id} <-> {self.show2_tmdb_id} ({self.similarity_score:.3f})"


class CachedRecommendation(models.Model):
    """Cached smart recommendations with expiration"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cached_recommendations')
    content_type = models.CharField(max_length=10, choices=[('movie', 'Movie'), ('tv', 'TV Show')])
    tmdb_id = models.IntegerField()
    
    # Recommendation details
    score = models.DecimalField(max_digits=5, decimal_places=3, help_text="Final recommendation score")
    explanation = models.TextField(help_text="Why this was recommended")
    recommendation_type = models.CharField(max_length=20, choices=[
        ('popular', 'Popular Pick'),
        ('niche', 'Hidden Gem'),
        ('similar', 'Similar to Your Taste'),
        ('trending', 'Trending Now'),
        ('classic', 'Classic Pick'),
        ('recent', 'New Release'),
    ])
    
    # Scoring breakdown (for debugging and improvement)
    content_score = models.FloatField(default=0.0, help_text="Content-based similarity score")
    popularity_score = models.FloatField(default=0.0, help_text="Popularity-based score")
    user_preference_score = models.FloatField(default=0.0, help_text="User preference alignment score")
    diversity_bonus = models.FloatField(default=0.0, help_text="Diversity injection bonus")
    
    # Cache metadata
    algorithm_version = models.CharField(max_length=50, default="1.0")
    user_settings_hash = models.CharField(max_length=64, help_text="Hash of user settings when generated")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(help_text="When this recommendation expires")
    
    # User interaction tracking
    viewed = models.BooleanField(default=False)
    clicked = models.BooleanField(default=False)
    added_to_watchlist = models.BooleanField(default=False)
    requested = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['user', 'tmdb_id', 'content_type']
        indexes = [
            models.Index(fields=['user', 'expires_at']),
            models.Index(fields=['user', 'score']),
            models.Index(fields=['user', 'content_type', 'recommendation_type']),
        ]
        ordering = ['-score', '-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.content_type} {self.tmdb_id} ({self.score})"
    
    def is_expired(self):
        """Check if this cached recommendation has expired"""
        return timezone.now() > self.expires_at


class RecommendationFeedback(models.Model):
    """Track user feedback on recommendations for algorithm improvement"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendation_feedback')
    content_type = models.CharField(max_length=10, choices=[('movie', 'Movie'), ('tv', 'TV Show')])
    tmdb_id = models.IntegerField()
    
    # Feedback types
    feedback_type = models.CharField(max_length=20, choices=[
        ('positive', 'Liked'),
        ('negative', 'Disliked'),
        ('not_interested', 'Not Interested'),
        ('added_to_watchlist', 'Added to Watchlist'),
        ('requested', 'Requested'),
        ('watched', 'Watched'),
    ])
    
    # Detailed feedback reasons (for negative feedback)
    detailed_reason = models.CharField(max_length=50, choices=[
        ('not_my_genre', 'Not My Genre'),
        ('already_seen', 'Already Seen'),
        ('poor_quality', 'Poor Quality/Rating'),
        ('wrong_mood', 'Wrong Mood'),
        ('too_old', 'Too Old'),
        ('too_new', 'Too New'),
        ('runtime', 'Runtime Issue'),
        ('inappropriate', 'Inappropriate Content'),
        ('language', 'Language Preference'),
        ('availability', 'Not Available'),
    ], null=True, blank=True)
    
    # Additional context
    additional_feedback = models.TextField(blank=True, help_text="Optional user comment")
    recommendation_explanation = models.TextField(help_text="Why it was recommended (for analysis)")
    recommendation_score = models.FloatField(help_text="Original recommendation score")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    user_settings_at_time = models.JSONField(default=dict, help_text="User settings when feedback given")
    
    class Meta:
        unique_together = ['user', 'tmdb_id', 'content_type']
        indexes = [
            models.Index(fields=['user', 'feedback_type']),
            models.Index(fields=['tmdb_id', 'content_type', 'feedback_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.feedback_type} - {self.content_type} {self.tmdb_id}"


class RecommendationQuality(models.Model):
    """Track overall recommendation session quality and success metrics"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendation_quality')
    session_date = models.DateTimeField(auto_now_add=True)
    
    # Session metrics
    total_recommendations = models.IntegerField(help_text="Total recommendations shown")
    positive_feedback = models.IntegerField(default=0)
    negative_feedback = models.IntegerField(default=0)
    items_added_to_watchlist = models.IntegerField(default=0)
    items_requested = models.IntegerField(default=0)
    items_clicked = models.IntegerField(default=0)
    
    # Algorithm performance
    avg_recommendation_score = models.FloatField(default=0.0)
    algorithm_settings_snapshot = models.JSONField(help_text="Settings used for this session")
    algorithm_version = models.CharField(max_length=50, default="1.0")
    
    # Quality metrics
    success_rate = models.FloatField(default=0.0, help_text="Percentage of positive interactions")
    diversity_score = models.FloatField(default=0.0, help_text="Genre/content diversity in recommendations")
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'session_date']),
            models.Index(fields=['success_rate']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.session_date.date()} - {self.success_rate:.1%} success"
    
    def calculate_success_rate(self):
        """Calculate and update success rate"""
        total_interactions = self.positive_feedback + self.negative_feedback + self.items_added_to_watchlist + self.items_requested
        if total_interactions > 0:
            successful_interactions = self.positive_feedback + self.items_added_to_watchlist + self.items_requested
            self.success_rate = successful_interactions / total_interactions
        else:
            self.success_rate = 0.0
        return self.success_rate


class UserPreferenceLearning(models.Model):
    """Track and learn from user preferences over time"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='preference_learning')
    
    # Learning categories
    genre_weights = models.JSONField(default=dict, help_text="Learned genre preference weights")
    actor_preferences = models.JSONField(default=dict, help_text="Actor preference scores")
    director_preferences = models.JSONField(default=dict, help_text="Director preference scores")
    
    # Temporal preferences
    runtime_preferences = models.JSONField(default=dict, help_text="Preferred runtime ranges by content type")
    release_year_preferences = models.JSONField(default=dict, help_text="Release year preference patterns")
    
    # Quality preferences
    rating_threshold_learned = models.FloatField(default=6.0, help_text="Learned minimum rating preference")
    popularity_preference = models.FloatField(default=0.5, help_text="Learned popular vs niche preference")
    
    # Learning metadata
    learning_confidence = models.FloatField(default=0.0, help_text="Confidence in learned preferences (0-1)")
    data_points_analyzed = models.IntegerField(default=0, help_text="Number of data points used for learning")
    last_learning_update = models.DateTimeField(auto_now=True)
    
    # Version tracking
    learning_algorithm_version = models.CharField(max_length=10, default="1.0")
    
    def __str__(self):
        return f"{self.user.username} - Preference Learning (confidence: {self.learning_confidence:.2f})"
    
    def needs_update(self):
        """Check if preference learning needs to be updated"""
        return timezone.now() - self.last_learning_update > timedelta(days=3)


class ContentFeatures(models.Model):
    """Extracted and computed features for content items"""
    content_type = models.CharField(max_length=10, choices=[('movie', 'Movie'), ('tv', 'TV Show')])
    tmdb_id = models.IntegerField()
    
    # Basic features
    genre_vector = models.JSONField(default=dict, help_text="Genre representation vector")
    cast_features = models.JSONField(default=list, help_text="Main cast members")
    crew_features = models.JSONField(default=dict, help_text="Director, writer, etc.")
    
    # Computed features
    popularity_percentile = models.FloatField(default=0.0, help_text="Popularity percentile (0-100)")
    rating_percentile = models.FloatField(default=0.0, help_text="Rating percentile (0-100)")
    niche_score = models.FloatField(default=0.0, help_text="How niche/hidden gem this content is")
    
    # Content characteristics
    runtime_category = models.CharField(max_length=20, choices=[
        ('short', 'Short (<90 min)'),
        ('medium', 'Medium (90-150 min)'),
        ('long', 'Long (>150 min)'),
    ], null=True, blank=True)
    
    release_era = models.CharField(max_length=20, choices=[
        ('classic', 'Classic (<1980)'),
        ('retro', 'Retro (1980-1999)'),
        ('modern', 'Modern (2000-2010)'),
        ('contemporary', 'Contemporary (2010+)'),
    ], null=True, blank=True)
    
    # Feature extraction metadata
    features_computed_at = models.DateTimeField(auto_now=True)
    feature_version = models.CharField(max_length=10, default="1.0")
    
    class Meta:
        unique_together = ['content_type', 'tmdb_id']
        indexes = [
            models.Index(fields=['content_type', 'popularity_percentile']),
            models.Index(fields=['content_type', 'rating_percentile']),
            models.Index(fields=['content_type', 'niche_score']),
        ]
    
    def __str__(self):
        return f"{self.content_type} {self.tmdb_id} - Features"
