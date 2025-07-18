from django.db import models
from django.contrib.auth.models import User
from core.models import Genre


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
    
    # Content rating for parental controls
    tv_rating = models.CharField(max_length=10, blank=True, choices=[
        ('TV-Y', 'All Children'),
        ('TV-Y7', 'Children 7+'),
        ('TV-G', 'General Audience'),
        ('TV-PG', 'Parental Guidance'),
        ('TV-14', 'Parents Strongly Cautioned'),
        ('TV-MA', 'Mature Audiences'),
    ])
    
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
