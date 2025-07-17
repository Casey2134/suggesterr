from django.db import models
from django.contrib.auth.models import User


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


# Import family profile models (legacy)
from .family_models import (
    FamilyProfile,
    ContentFilter,
    ContentRequest,
    ProfileLimits,
    ProfileActivity,
    ParentApprovedContent,
)

# Import new family group models
from .family_group_models import (
    FamilyGroup,
    FamilyMembership,
    UserContentFilter,
    UserLimits,
    UserActivity,
    ApprovedContent,
    FamilyInvitation,
)
