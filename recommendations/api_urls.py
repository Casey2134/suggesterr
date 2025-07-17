from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'negative-feedback', views.UserNegativeFeedbackViewSet, basename='negative-feedback')

app_name = 'recommendations_api'

urlpatterns = [
    # ViewSet URLs
    path('', include(router.urls)),
    
    # Chat API endpoints
    path('chat/message/', views.chat_message, name='chat_message'),
    path('chat/history/', views.chat_history, name='chat_history'),
    path('chat/clear/', views.clear_chat, name='clear_chat'),
    
    # Movie/TV Show details
    path('movie/details/', views.get_movie_details, name='get_movie_details'),
    path('tv-show/details/', views.get_tv_show_details, name='get_tv_show_details'),
    
    # Quiz API endpoints
    path('quiz/questions/', views.get_quiz_questions, name='get_quiz_questions'),
    path('quiz/submit/', views.submit_quiz, name='submit_quiz'),
    path('quiz/profile/', views.get_user_profile, name='get_user_profile'),
    path('quiz/retake/', views.retake_quiz, name='retake_quiz'),
]