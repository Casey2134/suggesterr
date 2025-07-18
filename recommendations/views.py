from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import UserNegativeFeedback, ChatConversation, ChatMessage, UserProfile, PersonalityQuiz
from .serializers import (
    UserNegativeFeedbackSerializer, ChatConversationSerializer, ChatMessageSerializer,
    UserProfileSerializer, PersonalityQuizSerializer, QuizSubmissionSerializer
)
from .chat_service import ChatService
from core.error_handlers import SecureErrorHandler
from core.validators import ContentFilter, InputSanitizer
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


def recommendations_dashboard(request):
    """Recommendations dashboard page"""
    return render(request, 'recommendations/dashboard.html')

def ai_recommendations(request):
    """AI-powered recommendations page"""
    return render(request, 'recommendations/dashboard.html')

def mood_recommendations(request):
    """Mood-based recommendations page"""
    return render(request, 'recommendations/mood.html')

def similar_content(request):
    """Similar content recommendations page"""
    return render(request, 'recommendations/similar.html')

def discovery_quiz(request):
    """Discovery quiz page for personality-based recommendations"""
    if not request.user.is_authenticated:
        from django.contrib.auth.decorators import login_required
        from django.shortcuts import redirect
        return redirect('/accounts/login/?next=/recommendations/quiz/')
    return render(request, 'recommendations/discovery_quiz.html')


class UserNegativeFeedbackViewSet(viewsets.ModelViewSet):
    serializer_class = UserNegativeFeedbackSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserNegativeFeedback.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def mark_not_interested(self, request):
        """Mark a movie/TV show as not interested"""
        tmdb_id = request.data.get('tmdb_id')
        content_type = request.data.get('content_type', 'movie')
        reason = request.data.get('reason', 'not_interested')
        
        if not tmdb_id:
            return Response({'error': 'tmdb_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create or get existing feedback
        feedback, created = UserNegativeFeedback.objects.get_or_create(
            user=request.user,
            tmdb_id=tmdb_id,
            content_type=content_type,
            defaults={'reason': reason}
        )
        
        if not created:
            # Update reason if feedback already exists
            feedback.reason = reason
            feedback.save()
        
        serializer = self.get_serializer(feedback)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['delete'])
    def remove_feedback(self, request):
        """Remove negative feedback (undo not interested)"""
        tmdb_id = request.query_params.get('tmdb_id')
        content_type = request.query_params.get('content_type', 'movie')
        
        if not tmdb_id:
            return Response({'error': 'tmdb_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            feedback = UserNegativeFeedback.objects.get(
                user=request.user,
                tmdb_id=tmdb_id,
                content_type=content_type
            )
            feedback.delete()
            return Response({'message': 'Feedback removed successfully'}, status=status.HTTP_204_NO_CONTENT)
        except UserNegativeFeedback.DoesNotExist:
            return Response({'error': 'Feedback not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_message(request):
    """Handle chat message and return AI response"""
    if not request.data.get('message'):
        return JsonResponse({'error': 'Message is required'}, status=400)
    
    try:
        # Validate and sanitize user message
        user_message = ContentFilter.filter_chat_message(request.data.get('message'))
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    
    chat_service = ChatService()
    
    try:
        # Get or create conversation
        conversation = chat_service.get_or_create_conversation(request.user)
        
        # Save user message
        chat_service.save_message(conversation, 'user', user_message)
        
        # Generate AI response
        ai_response = chat_service.generate_response(user_message, conversation)
        
        # Save AI response
        chat_service.save_message(conversation, 'assistant', ai_response)
        
        # Only extract recommendations if the response doesn't contain error messages
        movie_recommendations = []
        tv_show_recommendations = []
        
        if not any(phrase in ai_response.lower() for phrase in [
            'temporarily unavailable', 'service is experiencing', 'having trouble',
            'try again', 'technical difficulties', 'not available right now'
        ]):
            movie_recommendations = chat_service.extract_movie_recommendations(ai_response)
            tv_show_recommendations = chat_service.extract_tv_show_recommendations(ai_response)
        
        return JsonResponse({
            'response': ai_response,
            'conversation_id': conversation.id,
            'movie_recommendations': movie_recommendations,
            'tv_show_recommendations': tv_show_recommendations
        })
    
    except Exception as e:
        return SecureErrorHandler.json_error_response(e, "Chat Service", 500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_history(request):
    """Get chat conversation history"""
    try:
        conversation = ChatConversation.objects.filter(user=request.user).first()
        
        if not conversation:
            return JsonResponse({'messages': []})
        
        serializer = ChatConversationSerializer(conversation)
        return JsonResponse(serializer.data)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_chat(request):
    """Clear chat conversation history"""
    try:
        chat_service = ChatService()
        chat_service.clear_conversation(request.user)
        
        return JsonResponse({'message': 'Chat history cleared'})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_movie_details(request):
    """Get movie details by title or TMDB ID"""
    title = request.GET.get('title')
    tmdb_id = request.GET.get('tmdb_id')
    
    if not title and not tmdb_id:
        return JsonResponse({'error': 'Either title or tmdb_id is required'}, status=400)
    
    try:
        chat_service = ChatService()
        
        if tmdb_id:
            movie = chat_service.tmdb_service.get_movie_details(int(tmdb_id))
        else:
            movie = chat_service.get_movie_by_title(title)
        
        if movie:
            return JsonResponse({'movie': movie})
        else:
            return JsonResponse({'error': 'Movie not found'}, status=404)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_tv_show_details(request):
    """Get TV show details by title or TMDB ID"""
    title = request.GET.get('title')
    tmdb_id = request.GET.get('tmdb_id')
    
    if not title and not tmdb_id:
        return JsonResponse({'error': 'Either title or tmdb_id is required'}, status=400)
    
    try:
        chat_service = ChatService()
        
        if tmdb_id:
            tv_show = chat_service.tmdb_tv_service.get_tv_show_details(int(tmdb_id))
        else:
            tv_show = chat_service.get_tv_show_by_title(title)
        
        if tv_show:
            return JsonResponse({'tv_show': tv_show})
        else:
            return JsonResponse({'error': 'TV show not found'}, status=404)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_quiz_questions(request):
    """Get all active quiz questions"""
    try:
        questions = PersonalityQuiz.objects.filter(is_active=True)
        serializer = PersonalityQuizSerializer(questions, many=True)
        return JsonResponse({'questions': serializer.data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_quiz(request):
    """Submit quiz answers and update user profile"""
    try:
        serializer = QuizSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return JsonResponse({'errors': serializer.errors}, status=400)
        
        answers = serializer.validated_data['answers']
        
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'personality_traits': {},
                'preferred_genres': [],
                'preferred_decades': [],
                'content_preferences': {}
            }
        )
        
        # Process answers and update personality traits
        personality_traits = {}
        preferred_genres = []
        preferred_decades = []
        content_preferences = {}
        
        for question_id, answer in answers.items():
            try:
                question = PersonalityQuiz.objects.get(id=int(question_id), is_active=True)
                
                # Map answers to personality traits based on question's trait_mapping
                if question.trait_mapping:
                    for trait, mapping in question.trait_mapping.items():
                        if isinstance(answer, list):
                            # Multiple choice - combine values
                            for ans in answer:
                                if ans in mapping:
                                    personality_traits[trait] = personality_traits.get(trait, 0) + mapping[ans]
                        else:
                            # Single choice or scale
                            if str(answer) in mapping:
                                personality_traits[trait] = personality_traits.get(trait, 0) + mapping[str(answer)]
                
                # Extract genre preferences
                if question.category == 'genres' and isinstance(answer, list):
                    preferred_genres.extend(answer)
                elif question.category == 'decades' and isinstance(answer, list):
                    preferred_decades.extend(answer)
                elif question.category == 'content_preferences':
                    content_preferences[question_id] = answer
                    
            except PersonalityQuiz.DoesNotExist:
                continue
        
        # Update user profile
        profile.personality_traits = personality_traits
        profile.preferred_genres = list(set(preferred_genres))  # Remove duplicates
        profile.preferred_decades = list(set(preferred_decades))
        profile.content_preferences = content_preferences
        profile.quiz_completed = True
        profile.quiz_completed_at = timezone.now()
        profile.save()
        
        # Return updated profile
        profile_serializer = UserProfileSerializer(profile)
        return JsonResponse({
            'message': 'Quiz submitted successfully',
            'profile': profile_serializer.data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """Get user's personality profile"""
    try:
        profile = UserProfile.objects.filter(user=request.user).first()
        
        if not profile:
            return JsonResponse({
                'profile': None,
                'quiz_completed': False
            })
        
        serializer = UserProfileSerializer(profile)
        return JsonResponse({
            'profile': serializer.data,
            'quiz_completed': profile.quiz_completed
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def retake_quiz(request):
    """Allow user to retake the quiz"""
    try:
        profile = UserProfile.objects.filter(user=request.user).first()
        
        if profile:
            # Reset quiz data
            profile.quiz_completed = False
            profile.quiz_completed_at = None
            profile.personality_traits = {}
            profile.preferred_genres = []
            profile.preferred_decades = []
            profile.content_preferences = {}
            profile.save()
        
        return JsonResponse({'message': 'Quiz reset successfully. You can now retake the quiz.'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
