from django.contrib import admin
from .models import UserSettings

@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'server_type', 'theme', 'created_at', 'updated_at')
    list_filter = ('server_type', 'theme', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Radarr Settings', {
            'fields': ('radarr_url', 'radarr_api_key'),
            'classes': ('collapse',)
        }),
        ('Sonarr Settings', {
            'fields': ('sonarr_url', 'sonarr_api_key'),
            'classes': ('collapse',)
        }),
        ('Media Server Settings', {
            'fields': ('server_type', 'server_url', 'server_api_key'),
            'classes': ('collapse',)
        }),
        ('Preferences', {
            'fields': ('theme',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
