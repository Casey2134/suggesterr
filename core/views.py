from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings
from integrations.services import RadarrService, SonarrService, JellyfinService, PlexService
from accounts.models import UserSettings
import logging

logger = logging.getLogger(__name__)

def dashboard(request):
    """Main dashboard view - Modularized SPA with extracted JavaScript"""
    context = {
        'page_title': 'Suggesterr - Movie Recommendations',
    }
    return render(request, 'core/dashboard.html', context)

def health_check(request):
    """Simple health check endpoint"""
    return JsonResponse({'status': 'healthy'})
