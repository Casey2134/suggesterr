from django.db import models
from django.contrib.auth.models import User
from .encryption import EncryptedCharField


class UserSettings(models.Model):
    """Store user API keys and integration settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    
    # Radarr settings
    radarr_url = models.URLField(blank=True, null=True, max_length=500)
    radarr_api_key = EncryptedCharField(max_length=500, blank=True)
    
    # Sonarr settings  
    sonarr_url = models.URLField(blank=True, null=True, max_length=500)
    sonarr_api_key = EncryptedCharField(max_length=500, blank=True)
    
    # Media server settings
    server_type = models.CharField(max_length=20, choices=[
        ('jellyfin', 'Jellyfin'),
        ('plex', 'Plex'),
    ], blank=True)
    server_url = models.URLField(blank=True, null=True, max_length=500)
    server_api_key = EncryptedCharField(max_length=500, blank=True)
    
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


# TODO: Family profile models will be implemented in future versions
