from django.db import models
from django.contrib.auth.models import User
from django.core.validators import URLValidator


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    tmdb_id = models.IntegerField(unique=True, null=True, blank=True)
    
    def __str__(self):
        return self.name


class Movie(models.Model):
    title = models.CharField(max_length=500)
    original_title = models.CharField(max_length=500, blank=True)
    overview = models.TextField(blank=True)
    release_date = models.DateField(null=True, blank=True)
    runtime = models.IntegerField(null=True, blank=True)
    budget = models.BigIntegerField(null=True, blank=True)
    revenue = models.BigIntegerField(null=True, blank=True)
    
    # TMDB data
    tmdb_id = models.IntegerField(unique=True, null=True, blank=True)
    imdb_id = models.CharField(max_length=20, blank=True)
    poster_path = models.CharField(max_length=500, blank=True)
    backdrop_path = models.CharField(max_length=500, blank=True)
    vote_average = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    vote_count = models.IntegerField(null=True, blank=True)
    popularity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Genres
    genres = models.ManyToManyField(Genre, blank=True)
    
    # Availability
    available_on_jellyfin = models.BooleanField(default=False)
    available_on_plex = models.BooleanField(default=False)
    requested_on_radarr = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-popularity', '-vote_average']
    
    def __str__(self):
        return f"{self.title} ({self.release_date.year if self.release_date else 'Unknown'})"


class UserRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 11)])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'movie']
    
    def __str__(self):
        return f"{self.user.username} - {self.movie.title}: {self.rating}/10"


class UserWatchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'movie']
    
    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"


class MovieRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'movie']
        ordering = ['-score', '-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.movie.title}: {self.score}"


class TVShow(models.Model):
    title = models.CharField(max_length=500)
    original_title = models.CharField(max_length=500, blank=True)
    overview = models.TextField(blank=True)
    first_air_date = models.DateField(null=True, blank=True)
    last_air_date = models.DateField(null=True, blank=True)
    number_of_episodes = models.IntegerField(null=True, blank=True)
    number_of_seasons = models.IntegerField(null=True, blank=True)
    episode_run_time = models.JSONField(default=list, blank=True)  # List of episode runtimes
    status = models.CharField(max_length=50, blank=True)  # Returning Series, Ended, etc.
    
    # External IDs
    tmdb_id = models.IntegerField(unique=True, null=True, blank=True)
    imdb_id = models.CharField(max_length=20, blank=True)
    
    # Media
    poster_path = models.CharField(max_length=500, blank=True)
    backdrop_path = models.CharField(max_length=500, blank=True)
    
    # Ratings
    vote_average = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    vote_count = models.IntegerField(null=True, blank=True)
    popularity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Genres
    genres = models.ManyToManyField(Genre, blank=True)
    
    # Availability
    available_on_jellyfin = models.BooleanField(default=False)
    available_on_plex = models.BooleanField(default=False)
    requested_on_sonarr = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-popularity', '-vote_average']
    
    def __str__(self):
        return f"{self.title} ({self.first_air_date.year if self.first_air_date else 'Unknown'})"


class TVShowRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tv_show = models.ForeignKey(TVShow, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 11)])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'tv_show']
    
    def __str__(self):
        return f"{self.user.username} - {self.tv_show.title}: {self.rating}/10"


class TVShowWatchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tv_show = models.ForeignKey(TVShow, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'tv_show']
    
    def __str__(self):
        return f"{self.user.username} - {self.tv_show.title}"


class TVShowRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tv_show = models.ForeignKey(TVShow, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'tv_show']
        ordering = ['-score', '-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.tv_show.title}: {self.score}"


class UserSettings(models.Model):
    """Store user API keys and integration settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    
    # Radarr settings
    radarr_url = models.URLField(blank=True, null=True)
    radarr_api_key = models.CharField(max_length=255, blank=True)
    
    # Sonarr settings  
    sonarr_url = models.URLField(blank=True, null=True)
    sonarr_api_key = models.CharField(max_length=255, blank=True)
    
    # Media server settings
    server_type = models.CharField(max_length=20, choices=[
        ('jellyfin', 'Jellyfin'),
        ('plex', 'Plex'),
    ], blank=True)
    server_url = models.URLField(blank=True, null=True)
    server_api_key = models.CharField(max_length=255, blank=True)
    
    # Preferences
    theme = models.CharField(max_length=20, default='dark', choices=[
        ('dark', 'Dark'),
        ('light', 'Light'),
        ('blue', 'Blue'),
        ('green', 'Green'),
    ])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} Settings"
