from django.urls import path
from . import views

app_name = 'smart_recommendations'

urlpatterns = [
    # Main pages
    path('', views.smart_discover_page, name='discover'),
    path('settings/', views.settings_page, name='settings'),
    path('feedback/', views.feedback_page, name='feedback'),
    
    # API endpoints
    path('api/recommendations/', views.get_smart_recommendations, name='api_get_recommendations'),
    path('api/settings/', views.user_recommendation_settings, name='api_settings'),
    path('api/feedback/', views.submit_recommendation_feedback, name='api_submit_feedback'),
    path('api/refresh/', views.refresh_recommendations, name='api_refresh'),
    path('api/stats/', views.recommendation_stats, name='api_stats'),
]
