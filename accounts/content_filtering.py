from django.utils import timezone
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from .family_models import (
    FamilyProfile,
    ContentFilter,
    ContentRequest,
    ProfileActivity,
    ParentApprovedContent,
    ProfileLimits,
)
from movies.models import Movie
from tv_shows.models import TVShow


class ContentFilterService:
    """
    Service class for content filtering logic
    """
    
    # Rating hierarchies for filtering
    MOVIE_RATING_HIERARCHY = ['G', 'PG', 'PG-13', 'R', 'NC-17']
    TV_RATING_HIERARCHY = ['TV-Y', 'TV-Y7', 'TV-G', 'TV-PG', 'TV-14', 'TV-MA']
    
    def __init__(self, profile: FamilyProfile):
        self.profile = profile
        self.now = timezone.now()
    
    def check_content_access(self, content_type: str, content_id: int) -> Dict:
        """
        Check if profile can access specific content
        
        Args:
            content_type: 'movie' or 'tv_show'
            content_id: ID of the content
            
        Returns:
            Dict with access status and reasons
        """
        # Get content object
        content = self._get_content_object(content_type, content_id)
        if not content:
            return {
                'access_granted': False,
                'reason': 'content_not_found',
                'message': f'{content_type.title()} not found'
            }
        
        # Check if profile is active
        if not self.profile.is_active:
            return {
                'access_granted': False,
                'reason': 'profile_inactive',
                'message': 'Profile is currently inactive'
            }
        
        # Check time restrictions
        time_check = self._check_time_restrictions()
        if not time_check['allowed']:
            return {
                'access_granted': False,
                'reason': 'time_restriction',
                'message': time_check['message']
            }
        
        # Check if content is explicitly blocked
        if self._is_content_blocked(content_type, content):
            return {
                'access_granted': False,
                'reason': 'content_blocked',
                'message': f'This {content_type} has been blocked for this profile'
            }
        
        # Check if content is parent-approved
        if self._is_content_approved(content_type, content):
            return {
                'access_granted': True,
                'reason': 'parent_approved',
                'message': f'This {content_type} has been approved by parent'
            }
        
        # Check age-based rating restrictions
        rating_check = self._check_age_rating(content_type, content)
        if not rating_check['allowed']:
            return {
                'access_granted': False,
                'reason': 'age_restriction',
                'message': rating_check['message'],
                'can_request': True
            }
        
        # All checks passed
        return {
            'access_granted': True,
            'reason': 'age_appropriate',
            'message': f'This {content_type} is appropriate for this profile'
        }
    
    def filter_content_queryset(self, queryset, content_type: str):
        """
        Filter a queryset based on profile restrictions
        
        Args:
            queryset: Django queryset to filter
            content_type: 'movie' or 'tv_show'
            
        Returns:
            Filtered queryset
        """
        if content_type == 'movie':
            return self._filter_movie_queryset(queryset)
        elif content_type == 'tv_show':
            return self._filter_tv_show_queryset(queryset)
        else:
            return queryset.none()
    
    def _filter_movie_queryset(self, queryset):
        """Filter movie queryset based on profile restrictions"""
        # Get allowed ratings based on profile's max rating
        allowed_ratings = self._get_allowed_movie_ratings()
        
        # Filter by rating
        filtered_queryset = queryset.filter(
            mpaa_rating__in=allowed_ratings
        )
        
        # Exclude blocked content
        blocked_movies = ContentFilter.objects.filter(
            profile=self.profile,
            content_type='movie',
            is_blocked=True
        ).values_list('movie_id', flat=True)
        
        filtered_queryset = filtered_queryset.exclude(id__in=blocked_movies)
        
        # Include parent-approved content regardless of rating
        approved_movies = ParentApprovedContent.objects.filter(
            profile=self.profile,
            movie__isnull=False
        ).values_list('movie_id', flat=True)
        
        # Union of age-appropriate and parent-approved content
        final_queryset = filtered_queryset.union(
            queryset.filter(id__in=approved_movies)
        )
        
        return final_queryset
    
    def _filter_tv_show_queryset(self, queryset):
        """Filter TV show queryset based on profile restrictions"""
        # Get allowed ratings based on profile's max rating
        allowed_ratings = self._get_allowed_tv_ratings()
        
        # Filter by rating
        filtered_queryset = queryset.filter(
            tv_rating__in=allowed_ratings
        )
        
        # Exclude blocked content
        blocked_shows = ContentFilter.objects.filter(
            profile=self.profile,
            content_type='tv_show',
            is_blocked=True
        ).values_list('tv_show_id', flat=True)
        
        filtered_queryset = filtered_queryset.exclude(id__in=blocked_shows)
        
        # Include parent-approved content regardless of rating
        approved_shows = ParentApprovedContent.objects.filter(
            profile=self.profile,
            tv_show__isnull=False
        ).values_list('tv_show_id', flat=True)
        
        # Union of age-appropriate and parent-approved content
        final_queryset = filtered_queryset.union(
            queryset.filter(id__in=approved_shows)
        )
        
        return final_queryset
    
    def _get_content_object(self, content_type: str, content_id: int):
        """Get content object by type and ID"""
        try:
            if content_type == 'movie':
                return Movie.objects.get(id=content_id)
            elif content_type == 'tv_show':
                return TVShow.objects.get(id=content_id)
        except (Movie.DoesNotExist, TVShow.DoesNotExist):
            return None
    
    def _check_time_restrictions(self) -> Dict:
        """Check if current time is within allowed hours"""
        try:
            limits = self.profile.limits
        except ProfileLimits.DoesNotExist:
            # No limits set, allow access
            return {'allowed': True, 'message': 'No time restrictions'}
        
        current_hour = self.now.hour
        is_weekend = self.now.weekday() >= 5  # Saturday = 5, Sunday = 6
        
        # Determine bedtime and wakeup hours
        if is_weekend and limits.weekend_extended_hours:
            bedtime = limits.weekend_bedtime_hour
        else:
            bedtime = limits.bedtime_hour
        
        wakeup = limits.wakeup_hour
        
        # Check if current time is within allowed hours
        if wakeup <= bedtime:
            # Normal case: wakeup at 7, bedtime at 21
            allowed = wakeup <= current_hour < bedtime
        else:
            # Edge case: wakeup at 6, bedtime at 1 (next day)
            allowed = current_hour >= wakeup or current_hour < bedtime
        
        if not allowed:
            return {
                'allowed': False,
                'message': f'Access restricted between {bedtime}:00 and {wakeup}:00'
            }
        
        return {'allowed': True, 'message': 'Within allowed hours'}
    
    def _is_content_blocked(self, content_type: str, content) -> bool:
        """Check if content is explicitly blocked"""
        filter_kwargs = {
            'profile': self.profile,
            'content_type': content_type,
            'is_blocked': True
        }
        
        if content_type == 'movie':
            filter_kwargs['movie'] = content
        else:
            filter_kwargs['tv_show'] = content
        
        return ContentFilter.objects.filter(**filter_kwargs).exists()
    
    def _is_content_approved(self, content_type: str, content) -> bool:
        """Check if content is parent-approved"""
        filter_kwargs = {'profile': self.profile}
        
        if content_type == 'movie':
            filter_kwargs['movie'] = content
        else:
            filter_kwargs['tv_show'] = content
        
        approved_content = ParentApprovedContent.objects.filter(**filter_kwargs).first()
        
        if not approved_content:
            return False
        
        # Check if approval has expired
        if approved_content.is_expired:
            return False
        
        return True
    
    def _check_age_rating(self, content_type: str, content) -> Dict:
        """Check if content rating is appropriate for profile age"""
        if content_type == 'movie':
            return self._check_movie_rating(content)
        else:
            return self._check_tv_rating(content)
    
    def _check_movie_rating(self, movie: Movie) -> Dict:
        """Check if movie rating is appropriate"""
        if not movie.mpaa_rating:
            # No rating assigned, assume safest option
            return {
                'allowed': True,
                'message': 'No rating assigned, access granted'
            }
        
        allowed_ratings = self._get_allowed_movie_ratings()
        
        if movie.mpaa_rating in allowed_ratings:
            return {
                'allowed': True,
                'message': f'Rating {movie.mpaa_rating} is appropriate'
            }
        else:
            return {
                'allowed': False,
                'message': f'Rating {movie.mpaa_rating} exceeds profile limit of {self.profile.max_movie_rating}'
            }
    
    def _check_tv_rating(self, tv_show: TVShow) -> Dict:
        """Check if TV show rating is appropriate"""
        if not tv_show.tv_rating:
            # No rating assigned, assume safest option
            return {
                'allowed': True,
                'message': 'No rating assigned, access granted'
            }
        
        allowed_ratings = self._get_allowed_tv_ratings()
        
        if tv_show.tv_rating in allowed_ratings:
            return {
                'allowed': True,
                'message': f'Rating {tv_show.tv_rating} is appropriate'
            }
        else:
            return {
                'allowed': False,
                'message': f'Rating {tv_show.tv_rating} exceeds profile limit of {self.profile.max_tv_rating}'
            }
    
    def _get_allowed_movie_ratings(self) -> List[str]:
        """Get list of allowed movie ratings for profile"""
        try:
            max_rating_index = self.MOVIE_RATING_HIERARCHY.index(self.profile.max_movie_rating)
            return self.MOVIE_RATING_HIERARCHY[:max_rating_index + 1]
        except ValueError:
            # Default to G if rating not found
            return ['G']
    
    def _get_allowed_tv_ratings(self) -> List[str]:
        """Get list of allowed TV ratings for profile"""
        try:
            max_rating_index = self.TV_RATING_HIERARCHY.index(self.profile.max_tv_rating)
            return self.TV_RATING_HIERARCHY[:max_rating_index + 1]
        except ValueError:
            # Default to TV-Y if rating not found
            return ['TV-Y']
    
    def log_activity(self, activity_type: str, content_type: str = None, 
                    content_id: int = None, description: str = '', 
                    metadata: Dict = None):
        """Log activity for the profile"""
        activity_data = {
            'profile': self.profile,
            'activity_type': activity_type,
            'description': description,
            'metadata': metadata or {}
        }
        
        # Add content references if provided
        if content_type and content_id:
            content = self._get_content_object(content_type, content_id)
            if content:
                if content_type == 'movie':
                    activity_data['movie'] = content
                else:
                    activity_data['tv_show'] = content
        
        ProfileActivity.objects.create(**activity_data)


class UsageLimitService:
    """
    Service class for usage limit checking and enforcement
    """
    
    def __init__(self, profile: FamilyProfile):
        self.profile = profile
        self.now = timezone.now()
    
    def check_request_limits(self) -> Dict:
        """
        Check if profile has exceeded request limits
        
        Returns:
            Dict with limit status and details
        """
        try:
            limits = self.profile.limits
        except ProfileLimits.DoesNotExist:
            # No limits set, allow requests
            return {
                'allowed': True,
                'message': 'No request limits set'
            }
        
        # Check daily limit
        daily_check = self._check_daily_requests(limits)
        if not daily_check['allowed']:
            return daily_check
        
        # Check weekly limit
        weekly_check = self._check_weekly_requests(limits)
        if not weekly_check['allowed']:
            return weekly_check
        
        # Check monthly limit
        monthly_check = self._check_monthly_requests(limits)
        if not monthly_check['allowed']:
            return monthly_check
        
        return {
            'allowed': True,
            'message': 'Within all request limits',
            'daily_remaining': daily_check['remaining'],
            'weekly_remaining': weekly_check['remaining'],
            'monthly_remaining': monthly_check['remaining']
        }
    
    def _check_daily_requests(self, limits: ProfileLimits) -> Dict:
        """Check daily request limit"""
        daily_start = self.now.replace(hour=0, minute=0, second=0, microsecond=0)
        daily_count = ContentRequest.objects.filter(
            profile=self.profile,
            created_at__gte=daily_start
        ).count()
        
        remaining = limits.daily_request_limit - daily_count
        
        if daily_count >= limits.daily_request_limit:
            return {
                'allowed': False,
                'message': f'Daily request limit ({limits.daily_request_limit}) exceeded',
                'remaining': 0
            }
        
        return {
            'allowed': True,
            'message': f'{remaining} daily requests remaining',
            'remaining': remaining
        }
    
    def _check_weekly_requests(self, limits: ProfileLimits) -> Dict:
        """Check weekly request limit"""
        weekly_start = self.now - timedelta(days=7)
        weekly_count = ContentRequest.objects.filter(
            profile=self.profile,
            created_at__gte=weekly_start
        ).count()
        
        remaining = limits.weekly_request_limit - weekly_count
        
        if weekly_count >= limits.weekly_request_limit:
            return {
                'allowed': False,
                'message': f'Weekly request limit ({limits.weekly_request_limit}) exceeded',
                'remaining': 0
            }
        
        return {
            'allowed': True,
            'message': f'{remaining} weekly requests remaining',
            'remaining': remaining
        }
    
    def _check_monthly_requests(self, limits: ProfileLimits) -> Dict:
        """Check monthly request limit"""
        monthly_start = self.now - timedelta(days=30)
        monthly_count = ContentRequest.objects.filter(
            profile=self.profile,
            created_at__gte=monthly_start
        ).count()
        
        remaining = limits.monthly_request_limit - monthly_count
        
        if monthly_count >= limits.monthly_request_limit:
            return {
                'allowed': False,
                'message': f'Monthly request limit ({limits.monthly_request_limit}) exceeded',
                'remaining': 0
            }
        
        return {
            'allowed': True,
            'message': f'{remaining} monthly requests remaining',
            'remaining': remaining
        }
    
    def get_usage_stats(self) -> Dict:
        """Get current usage statistics"""
        try:
            limits = self.profile.limits
        except ProfileLimits.DoesNotExist:
            return {'error': 'No limits configured'}
        
        # Calculate date ranges
        daily_start = self.now.replace(hour=0, minute=0, second=0, microsecond=0)
        weekly_start = self.now - timedelta(days=7)
        monthly_start = self.now - timedelta(days=30)
        
        # Get request counts
        daily_count = ContentRequest.objects.filter(
            profile=self.profile,
            created_at__gte=daily_start
        ).count()
        
        weekly_count = ContentRequest.objects.filter(
            profile=self.profile,
            created_at__gte=weekly_start
        ).count()
        
        monthly_count = ContentRequest.objects.filter(
            profile=self.profile,
            created_at__gte=monthly_start
        ).count()
        
        return {
            'daily': {
                'used': daily_count,
                'limit': limits.daily_request_limit,
                'remaining': limits.daily_request_limit - daily_count,
                'percentage': (daily_count / limits.daily_request_limit) * 100
            },
            'weekly': {
                'used': weekly_count,
                'limit': limits.weekly_request_limit,
                'remaining': limits.weekly_request_limit - weekly_count,
                'percentage': (weekly_count / limits.weekly_request_limit) * 100
            },
            'monthly': {
                'used': monthly_count,
                'limit': limits.monthly_request_limit,
                'remaining': limits.monthly_request_limit - monthly_count,
                'percentage': (monthly_count / limits.monthly_request_limit) * 100
            }
        }