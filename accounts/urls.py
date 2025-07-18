from django.urls import path, include
from . import views
from .family_template_views import (
    family_profiles_view, 
    parental_dashboard_view,
    profile_settings_view,
    content_requests_view,
    switch_profile,
    clear_profile,
    family_management_view,
    family_dashboard_view
)

app_name = 'accounts'

urlpatterns = [
    path('settings/', views.settings_view, name='settings'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('test_connections/', views.test_connections, name='test_connections'),
    
    # Family profile management template URLs (legacy)
    path('family-profiles/', family_profiles_view, name='family_profiles'),
    path('parental-dashboard/', parental_dashboard_view, name='parental_dashboard'),
    path('profile-settings/<int:profile_id>/', profile_settings_view, name='profile_settings'),
    path('content-requests/', content_requests_view, name='content_requests'),
    path('switch-profile/<int:profile_id>/', switch_profile, name='switch_profile'),
    path('clear-profile/', clear_profile, name='clear_profile'),
    
    # New family management template URLs
    path('family-management/', family_management_view, name='family_management'),
    path('family-dashboard/', family_dashboard_view, name='family_dashboard'),
    
    # Family profile management API URLs
    path('', include('accounts.family_urls')),
]