from django.db import models
from django.contrib.auth.models import User
from core.models import Genre


class Movie(models.Model):
    title = models.CharField(max_length=500)
    original_title = models.CharField(max_length=500, blank=True, null=True)
    overview = models.TextField(blank=True, null=True)
    release_date = models.DateField(null=True, blank=True)
    runtime = models.IntegerField(null=True, blank=True)
    budget = models.BigIntegerField(null=True, blank=True)
    revenue = models.BigIntegerField(null=True, blank=True)
    
    # TMDB data
    tmdb_id = models.IntegerField(unique=True, null=True, blank=True)
    imdb_id = models.CharField(max_length=20, blank=True, null=True)
    poster_path = models.CharField(max_length=500, blank=True, null=True)
    backdrop_path = models.CharField(max_length=500, blank=True, null=True)
    vote_average = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    vote_count = models.IntegerField(null=True, blank=True)
    popularity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Content rating for parental controls
    mpaa_rating = models.CharField(max_length=10, blank=True, choices=[
        ('G', 'General Audiences'),
        ('PG', 'Parental Guidance Suggested'),
        ('PG-13', 'Parents Strongly Cautioned'),
        ('R', 'Restricted'),
        ('NC-17', 'Adults Only'),
    ])
    
    # Genres
    genres = models.ManyToManyField(Genre, blank=True)
    
    # Request status
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
