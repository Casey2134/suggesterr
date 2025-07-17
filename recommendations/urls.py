from django.urls import path, include
from . import views

app_name = 'recommendations'

urlpatterns = [
    # Template views
    path('', views.recommendations_dashboard, name='dashboard'),
    path('ai/', views.ai_recommendations, name='ai'),
    path('mood/', views.mood_recommendations, name='mood'),
    path('similar/', views.similar_content, name='similar'),
    path('quiz/', views.discovery_quiz, name='discovery_quiz'),
    
    # API endpoints
    path('api/', include('recommendations.api_urls')),
]