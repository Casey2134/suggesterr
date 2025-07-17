from rest_framework import serializers
from .models import UserSettings


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = [
            'id', 'radarr_url', 'radarr_api_key', 'sonarr_url', 'sonarr_api_key',
            'server_type', 'server_url', 'server_api_key', 'theme', 
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'radarr_api_key': {'write_only': True},
            'sonarr_api_key': {'write_only': True},
            'server_api_key': {'write_only': True},
        }