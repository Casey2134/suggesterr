"""
URL configuration for suggesterr project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Core application (dashboard/home)
    path('', include('core.urls')),
    
    # App-specific URLs
    path('movies/', include('movies.urls')),
    path('tv-shows/', include('tv_shows.urls')),
    path('accounts/', include('accounts.urls')),
    path('recommendations/', include('recommendations.urls')),
    path('smart-discover/', include('smart_recommendations.urls')),
    
    # API endpoints  
    path('api/', include('movies.api_urls')),
    path('api/auth/', include('rest_framework.urls')),
    
    # Admin
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
