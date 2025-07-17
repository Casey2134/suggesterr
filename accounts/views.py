from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import UserSettings
from .serializers import UserSettingsSerializer
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from integrations.services import RadarrService, SonarrService, JellyfinService, PlexService
import logging

logger = logging.getLogger(__name__)

def settings_view(request):
    """User settings page"""
    return render(request, 'accounts/settings.html')

def login_view(request):
    """Login page"""
    return render(request, 'accounts/login.html')

def logout_view(request):
    """Logout functionality"""
    return render(request, 'accounts/logout.html')

def register_view(request):
    """Registration page"""
    return render(request, 'accounts/register.html')


class UserSettingsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get current user's settings (for GET /api/settings/)"""
        try:
            settings = UserSettings.objects.get(user=request.user)
            serializer = UserSettingsSerializer(settings)
            return Response(serializer.data)
        except UserSettings.DoesNotExist:
            # Return default settings structure if none exist
            return Response({
                'server_type': '',
                'server_url': '',
                'server_api_key': '',
                'preferred_language': 'en',
                'include_adult_content': False
            })
    
    def retrieve(self, request, pk=None):
        """Get user settings (always gets current user's settings regardless of pk)"""
        try:
            settings = UserSettings.objects.get(user=request.user)
            serializer = UserSettingsSerializer(settings)
            return Response(serializer.data)
        except UserSettings.DoesNotExist:
            return Response({'error': 'Settings not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def partial_update(self, request, pk=None):
        """Update user settings (always updates current user's settings regardless of pk)"""
        try:
            settings = UserSettings.objects.get(user=request.user)
        except UserSettings.DoesNotExist:
            return Response({'error': 'Settings not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def create(self, request):
        """Create or update user settings for current user"""
        try:
            # Try to get existing settings
            settings = UserSettings.objects.get(user=request.user)
            # Update existing settings
            serializer = UserSettingsSerializer(settings, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserSettings.DoesNotExist:
            # Create new settings
            serializer = UserSettingsSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
@login_required
def test_connections(request):
    """Test connections to all configured services"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Get user settings
        user_settings = UserSettings.objects.filter(user=request.user).first()
        if not user_settings:
            return JsonResponse({
                'error': 'No settings configured',
                'results': {}
            }, status=400)
        
        results = {}
        
        # Test Radarr connection
        if user_settings.radarr_url and user_settings.radarr_api_key:
            # Override settings temporarily for this user's configuration
            settings.RADARR_URL = user_settings.radarr_url
            settings.RADARR_API_KEY = user_settings.radarr_api_key
            
            radarr = RadarrService()
            success, message = radarr.test_connection()
            results['radarr'] = {
                'status': 'success' if success else 'error',
                'message': message
            }
        else:
            results['radarr'] = {
                'status': 'not_configured',
                'message': 'Radarr not configured'
            }
        
        # Test Sonarr connection
        if user_settings.sonarr_url and user_settings.sonarr_api_key:
            # Override settings temporarily for this user's configuration
            settings.SONARR_URL = user_settings.sonarr_url
            settings.SONARR_API_KEY = user_settings.sonarr_api_key
            
            sonarr = SonarrService()
            # Add test_connection method to Sonarr if it doesn't exist
            try:
                test_url = f"{sonarr.base_url}/api/v3/system/status"
                import requests
                response = requests.get(test_url, headers=sonarr.headers, timeout=10)
                
                if response.status_code == 401:
                    results['sonarr'] = {
                        'status': 'error',
                        'message': 'Authentication failed - check API key'
                    }
                elif response.status_code == 200:
                    results['sonarr'] = {
                        'status': 'success',
                        'message': 'Connection successful'
                    }
                else:
                    results['sonarr'] = {
                        'status': 'error',
                        'message': f'HTTP {response.status_code}: {response.text}'
                    }
            except Exception as e:
                results['sonarr'] = {
                    'status': 'error',
                    'message': f'Connection error: {str(e)}'
                }
        else:
            results['sonarr'] = {
                'status': 'not_configured',
                'message': 'Sonarr not configured'
            }
        
        # Test media server connection (Jellyfin or Plex)
        if user_settings.server_type:
            if user_settings.server_type == 'jellyfin' and user_settings.server_url and user_settings.server_api_key:
                # Override settings temporarily
                settings.JELLYFIN_URL = user_settings.server_url
                settings.JELLYFIN_API_KEY = user_settings.server_api_key
                
                jellyfin = JellyfinService()
                try:
                    # Test by getting library stats
                    stats = jellyfin.get_library_stats()
                    if stats:
                        results['media_server'] = {
                            'status': 'success',
                            'message': 'Jellyfin connection successful',
                            'type': 'jellyfin'
                        }
                    else:
                        results['media_server'] = {
                            'status': 'error',
                            'message': 'Failed to retrieve Jellyfin library stats',
                            'type': 'jellyfin'
                        }
                except Exception as e:
                    results['media_server'] = {
                        'status': 'error',
                        'message': f'Jellyfin connection error: {str(e)}',
                        'type': 'jellyfin'
                    }
            elif user_settings.server_type == 'plex' and user_settings.server_url and user_settings.server_api_key:
                # Override settings temporarily
                settings.PLEX_URL = user_settings.server_url
                settings.PLEX_TOKEN = user_settings.server_api_key
                
                plex = PlexService()
                try:
                    # Test by getting library stats
                    stats = plex.get_library_stats()
                    if stats:
                        results['media_server'] = {
                            'status': 'success',
                            'message': 'Plex connection successful',
                            'type': 'plex'
                        }
                    else:
                        results['media_server'] = {
                            'status': 'error',
                            'message': 'Failed to retrieve Plex library stats',
                            'type': 'plex'
                        }
                except Exception as e:
                    results['media_server'] = {
                        'status': 'error',
                        'message': f'Plex connection error: {str(e)}',
                        'type': 'plex'
                    }
            else:
                results['media_server'] = {
                    'status': 'not_configured',
                    'message': f'{user_settings.server_type.title()} not fully configured',
                    'type': user_settings.server_type
                }
        else:
            results['media_server'] = {
                'status': 'not_configured',
                'message': 'No media server configured',
                'type': None
            }
        
        return JsonResponse({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error testing connections: {e}")
        return JsonResponse({
            'error': f'Server error: {str(e)}',
            'results': {}
        }, status=500)
