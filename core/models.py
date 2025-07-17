from django.db import models

class Genre(models.Model):
    """Shared genre model for both movies and TV shows"""
    name = models.CharField(max_length=100, unique=True)
    tmdb_id = models.IntegerField(unique=True, null=True, blank=True)
    
    def __str__(self):
        return self.name
