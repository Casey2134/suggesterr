from django.shortcuts import render, redirect
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import UserSettings
from .serializers import UserSettingsSerializer
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from integrations.services import RadarrService, SonarrService, JellyfinService, PlexService
from django_ratelimit.decorators import ratelimit
import logging

logger = logging.getLogger(__name__)

@login_required
def settings_view(request):
    """User settings page with form handling"""
    # Get or create user settings
    user_settings, created = UserSettings.objects.get_or_create(
        user=request.user,
        defaults={'theme': 'dark'}
    )
    
    if request.method == 'POST':
        from .forms import UserSettingsForm
        form = UserSettingsForm(request.POST, instance=user_settings)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings saved successfully!')
            return redirect('accounts:settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        from .forms import UserSettingsForm
        form = UserSettingsForm(instance=user_settings)
    
    return render(request, 'accounts/settings.html', {
        'form': form,
        'user_settings': user_settings
    })

@csrf_protect
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_view(request):
    """Login page with Django backend authentication"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'accounts/login.html')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next', 'core:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'accounts/login.html')
    
    return render(request, 'accounts/login.html')

def logout_view(request):
    """Logout functionality"""
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')

@csrf_protect
@ratelimit(key='ip', rate='3/m', method='POST', block=True)
def register_view(request):
    """Registration page with Django backend authentication"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        
        # Validation
        if not username or not email or not password:
            messages.error(request, 'All fields are required.')
            return render(request, 'accounts/register.html')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'accounts/register.html')
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'accounts/register.html')
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # Create default user settings
            UserSettings.objects.create(
                user=user,
                theme='dark'  # Set default theme
            )
            
            # Log the user in
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, 'Account created successfully!')
                return redirect('core:dashboard')
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            messages.error(request, 'An error occurred during registration. Please try again.')
            return render(request, 'accounts/register.html')
    
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
        logger.info(f"UserSettingsViewSet.create called for user: {request.user}")
        logger.info(f"Request data: {request.data}")
        
        if not request.user.is_authenticated:
            logger.error("User is not authenticated")
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            # Try to get existing settings
            settings = UserSettings.objects.get(user=request.user)
            logger.info(f"Found existing settings for user {request.user}")
            # Update existing settings
            serializer = UserSettingsSerializer(settings, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                logger.info(f"Successfully updated settings for user {request.user}")
                return Response(serializer.data)
            logger.error(f"Serializer validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserSettings.DoesNotExist:
            logger.info(f"No existing settings found for user {request.user}, creating new ones")
            # Create new settings
            serializer = UserSettingsSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                logger.info(f"Successfully created new settings for user {request.user}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            logger.error(f"Serializer validation failed when creating: {serializer.errors}")
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
