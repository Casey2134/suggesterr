from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json

from .recommendation_engine import SmartRecommendationEngine
from .models import UserRecommendationSettings, RecommendationFeedback
from recommendations.models import UserNegativeFeedback


@login_required
def smart_discover_page(request):
    """Main smart discover page"""
    return render(request, 'smart_recommendations/discover.html', {
        'page_title': 'Smart Discover',
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_smart_recommendations(request):
    """Get smart recommendations for the authenticated user"""
    try:
        # Get query parameters
        limit = int(request.GET.get('limit', 20))
        refresh = request.GET.get('refresh', 'false').lower() == 'true'
        
        # Validate limit
        if limit < 1 or limit > 100:
            limit = 20
        
        # Get recommendations using the engine
        engine = SmartRecommendationEngine(request.user)
        recommendations = engine.get_smart_recommendations(limit=limit, refresh=refresh)
        
        return Response({
            'status': 'success',
            'recommendations': recommendations,
            'count': len(recommendations),
            'refresh_requested': refresh,
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Failed to get recommendations: {str(e)}',
            'recommendations': [],
            'count': 0,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_recommendation_settings(request):
    """Get or update user recommendation settings"""
    try:
        settings, created = UserRecommendationSettings.objects.get_or_create(
            user=request.user,
            defaults={
                'popular_vs_niche_balance': 0.5,
                'genre_diversity': 0.7,
                'release_year_preference': 0.5,
                'runtime_flexibility': 0.6,
                'movie_weight': 0.5,
                'include_rewatches': False,
                'minimum_rating': 6.0,
                'prefer_recent_releases': True,
                'prefer_highly_rated': True,
            }
        )
        
        if request.method == 'GET':
            return Response({
                'status': 'success',
                'settings': {
                    'popular_vs_niche_balance': settings.popular_vs_niche_balance,
                    'genre_diversity': settings.genre_diversity,
                    'release_year_preference': settings.release_year_preference,
                    'runtime_flexibility': settings.runtime_flexibility,
                    'movie_weight': settings.movie_weight,
                    'include_rewatches': settings.include_rewatches,
                    'auto_refresh_days': settings.auto_refresh_days,
                    'minimum_rating': settings.minimum_rating,
                    'prefer_recent_releases': settings.prefer_recent_releases,
                    'prefer_highly_rated': settings.prefer_highly_rated,
                    'last_refreshed': settings.last_refreshed,
                }
            })
        
        elif request.method == 'PUT':
            # Update settings
            data = request.data
            
            # Validate and update settings
            if 'popular_vs_niche_balance' in data:
                value = float(data['popular_vs_niche_balance'])
                settings.popular_vs_niche_balance = max(0.0, min(1.0, value))
            
            if 'genre_diversity' in data:
                value = float(data['genre_diversity'])
                settings.genre_diversity = max(0.0, min(1.0, value))
            
            if 'release_year_preference' in data:
                value = float(data['release_year_preference'])
                settings.release_year_preference = max(0.0, min(1.0, value))
            
            if 'runtime_flexibility' in data:
                value = float(data['runtime_flexibility'])
                settings.runtime_flexibility = max(0.0, min(1.0, value))
            
            if 'movie_weight' in data:
                value = float(data['movie_weight'])
                settings.movie_weight = max(0.0, min(1.0, value))
            
            if 'include_rewatches' in data:
                settings.include_rewatches = bool(data['include_rewatches'])
            
            if 'auto_refresh_days' in data:
                value = int(data['auto_refresh_days'])
                settings.auto_refresh_days = max(1, min(30, value))
            
            if 'minimum_rating' in data:
                value = float(data['minimum_rating'])
                settings.minimum_rating = max(0.0, min(10.0, value))
            
            if 'prefer_recent_releases' in data:
                settings.prefer_recent_releases = bool(data['prefer_recent_releases'])
            
            if 'prefer_highly_rated' in data:
                settings.prefer_highly_rated = bool(data['prefer_highly_rated'])
            
            settings.save()
            
            # Update engine settings and clear cache
            engine = SmartRecommendationEngine(request.user)
            engine.update_settings(**{
                'popular_vs_niche_balance': settings.popular_vs_niche_balance,
                'genre_diversity': settings.genre_diversity,
                'release_year_preference': settings.release_year_preference,
                'runtime_flexibility': settings.runtime_flexibility,
                'movie_weight': settings.movie_weight,
                'include_rewatches': settings.include_rewatches,
                'minimum_rating': settings.minimum_rating,
                'prefer_recent_releases': settings.prefer_recent_releases,
                'prefer_highly_rated': settings.prefer_highly_rated,
            })
            
            return Response({
                'status': 'success',
                'message': 'Settings updated successfully',
                'settings': {
                    'popular_vs_niche_balance': settings.popular_vs_niche_balance,
                    'genre_diversity': settings.genre_diversity,
                    'release_year_preference': settings.release_year_preference,
                    'runtime_flexibility': settings.runtime_flexibility,
                    'movie_weight': settings.movie_weight,
                    'include_rewatches': settings.include_rewatches,
                    'auto_refresh_days': settings.auto_refresh_days,
                    'minimum_rating': settings.minimum_rating,
                    'prefer_recent_releases': settings.prefer_recent_releases,
                    'prefer_highly_rated': settings.prefer_highly_rated,
                    'last_refreshed': settings.last_refreshed,
                }
            })
            
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Failed to handle settings: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_recommendation_feedback(request):
    """Submit feedback on a recommendation"""
    try:
        data = request.data
        
        # Validate required fields
        required_fields = ['tmdb_id', 'content_type', 'feedback_type']
        for field in required_fields:
            if field not in data:
                return Response({
                    'status': 'error',
                    'message': f'Missing required field: {field}',
                }, status=status.HTTP_400_BAD_REQUEST)
        
        tmdb_id = int(data['tmdb_id'])
        content_type = data['content_type']
        feedback_type = data['feedback_type']
        detailed_reason = data.get('detailed_reason', None)
        additional_feedback = data.get('additional_feedback', '')
        
        # Validate content type
        if content_type not in ['movie', 'tv']:
            return Response({
                'status': 'error',
                'message': 'Invalid content_type. Must be "movie" or "tv".',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate feedback type
        valid_feedback_types = ['positive', 'negative', 'not_interested', 'added_to_watchlist', 'requested', 'watched']
        if feedback_type not in valid_feedback_types:
            return Response({
                'status': 'error',
                'message': f'Invalid feedback_type. Must be one of: {", ".join(valid_feedback_types)}',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Record feedback using the engine
        engine = SmartRecommendationEngine(request.user)
        engine.record_feedback(
            tmdb_id=tmdb_id,
            content_type=content_type,
            feedback_type=feedback_type,
            detailed_reason=detailed_reason,
            additional_feedback=additional_feedback
        )
        
        # If user marked as "not interested" or gave negative feedback, 
        # also add to the existing negative feedback system
        if feedback_type in ['negative', 'not_interested']:
            reason = 'not_interested'
            if detailed_reason:
                reason = detailed_reason
            
            UserNegativeFeedback.objects.update_or_create(
                user=request.user,
                tmdb_id=tmdb_id,
                content_type=content_type,
                defaults={'reason': reason}
            )
        
        return Response({
            'status': 'success',
            'message': 'Feedback recorded successfully',
        })
        
    except ValueError as e:
        return Response({
            'status': 'error',
            'message': 'Invalid tmdb_id. Must be a number.',
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Failed to record feedback: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_recommendations(request):
    """Force refresh recommendations for the user"""
    try:
        limit = int(request.data.get('limit', 20))
        
        # Validate limit
        if limit < 1 or limit > 100:
            limit = 20
        
        # Force refresh recommendations
        engine = SmartRecommendationEngine(request.user)
        recommendations = engine.get_smart_recommendations(limit=limit, refresh=True)
        
        return Response({
            'status': 'success',
            'message': 'Recommendations refreshed successfully',
            'recommendations': recommendations,
            'count': len(recommendations),
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Failed to refresh recommendations: {str(e)}',
            'recommendations': [],
            'count': 0,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recommendation_stats(request):
    """Get recommendation statistics for the user"""
    try:
        # Get feedback statistics
        total_feedback = RecommendationFeedback.objects.filter(user=request.user).count()
        positive_feedback = RecommendationFeedback.objects.filter(
            user=request.user, 
            feedback_type__in=['positive', 'added_to_watchlist', 'requested']
        ).count()
        negative_feedback = RecommendationFeedback.objects.filter(
            user=request.user, 
            feedback_type__in=['negative', 'not_interested']
        ).count()
        
        # Calculate success rate
        success_rate = 0.0
        if total_feedback > 0:
            success_rate = positive_feedback / total_feedback
        
        # Get user settings
        try:
            settings = UserRecommendationSettings.objects.get(user=request.user)
            last_refreshed = settings.last_refreshed
            auto_refresh_days = settings.auto_refresh_days
        except UserRecommendationSettings.DoesNotExist:
            last_refreshed = None
            auto_refresh_days = 7
        
        return Response({
            'status': 'success',
            'stats': {
                'total_feedback': total_feedback,
                'positive_feedback': positive_feedback,
                'negative_feedback': negative_feedback,
                'success_rate': success_rate,
                'last_refreshed': last_refreshed,
                'auto_refresh_days': auto_refresh_days,
            }
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Failed to get statistics: {str(e)}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Traditional Django views for page rendering
@login_required
def settings_page(request):
    """Render the settings page for smart recommendations"""
    return render(request, 'smart_recommendations/settings.html', {
        'page_title': 'Smart Recommendation Settings',
    })


@login_required  
def feedback_page(request):
    """Render the feedback history page"""
    return render(request, 'smart_recommendations/feedback.html', {
        'page_title': 'Recommendation Feedback',
    })
