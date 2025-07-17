from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from .family_group_models import (
    FamilyGroup,
    FamilyMembership,
    UserContentFilter,
    UserContentRequest,
    UserLimits,
    UserActivity,
    ApprovedContent,
    FamilyInvitation,
)
from movies.models import Movie
from tv_shows.models import TVShow


class FamilyGroupService:
    """
    Service for managing family groups and memberships
    """
    
    @staticmethod
    def create_family_group(admin_user: User, family_name: str) -> FamilyGroup:
        """
        Create a new family group with the given user as admin
        
        Args:
            admin_user: User who will be the family admin
            family_name: Name for the family group
            
        Returns:
            FamilyGroup: The created family group
        """
        # Create family group
        family = FamilyGroup.objects.create(
            name=family_name,
            admin_user=admin_user
        )
        
        # Create admin membership
        FamilyMembership.objects.create(
            user=admin_user,
            family=family,
            is_admin=True,
            age=18,  # Default adult age
            max_movie_rating='NC-17',
            max_tv_rating='TV-MA'
        )
        
        # Create default limits for admin
        UserLimits.objects.create(
            user=admin_user,
            daily_request_limit=999,
            weekly_request_limit=999,
            monthly_request_limit=999
        )
        
        return family
    
    @staticmethod
    def invite_member(family: FamilyGroup, email: str, invited_by: User, 
                     age: int, max_movie_rating: str = 'G', 
                     max_tv_rating: str = 'TV-Y', message: str = '') -> FamilyInvitation:
        """
        Create an invitation for someone to join a family
        
        Args:
            family: Family group to invite to
            email: Email address to invite
            invited_by: User sending the invitation
            age: Proposed age for the new member
            max_movie_rating: Proposed movie rating limit
            max_tv_rating: Proposed TV rating limit
            message: Optional message for the invitation
            
        Returns:
            FamilyInvitation: The created invitation
        """
        import secrets
        
        # Generate secure token
        token = secrets.token_urlsafe(32)
        
        # Set expiration to 7 days from now
        expires_at = timezone.now() + timedelta(days=7)
        
        invitation = FamilyInvitation.objects.create(
            family=family,
            email=email,
            invited_by=invited_by,
            message=message,
            proposed_age=age,
            proposed_max_movie_rating=max_movie_rating,
            proposed_max_tv_rating=max_tv_rating,
            token=token,
            expires_at=expires_at
        )
        
        return invitation
    
    @staticmethod
    def get_user_family(user: User) -> Optional[FamilyGroup]:
        """
        Get the family group for a user
        
        Args:
            user: User to get family for
            
        Returns:
            FamilyGroup or None: The user's family group
        """
        try:
            return user.family_membership.family
        except:
            return None
    
    @staticmethod
    def is_family_admin(user: User) -> bool:
        """
        Check if user is a family admin
        
        Args:
            user: User to check
            
        Returns:
            bool: True if user is family admin
        """
        try:
            return user.family_membership.is_admin
        except:
            return False
    
    @staticmethod
    def get_family_members(family: FamilyGroup) -> List[User]:
        """
        Get all members of a family
        
        Args:
            family: Family group
            
        Returns:
            List[User]: List of family members
        """
        return list(family.get_members())
    
    @staticmethod
    def remove_member(family: FamilyGroup, user: User, removed_by: User) -> bool:
        """
        Remove a member from a family
        
        Args:
            family: Family group
            user: User to remove
            removed_by: User performing the removal
            
        Returns:
            bool: True if removal was successful
        """
        # Only admin can remove members
        if not FamilyGroupService.is_family_admin(removed_by):
            raise ValidationError("Only family admin can remove members.")
        
        # Can't remove the admin
        if user == family.admin_user:
            raise ValidationError("Cannot remove the family admin.")
        
        try:
            membership = user.family_membership
            if membership.family != family:
                raise ValidationError("User is not a member of this family.")
            
            membership.delete()
            return True
        except:
            return False


class UserContentFilterService:
    """
    Service for content filtering based on User accounts
    """
    
    # Rating hierarchies for filtering
    MOVIE_RATING_HIERARCHY = ['G', 'PG', 'PG-13', 'R', 'NC-17']
    TV_RATING_HIERARCHY = ['TV-Y', 'TV-Y7', 'TV-G', 'TV-PG', 'TV-14', 'TV-MA']
    
    def __init__(self, user: User):
        self.user = user
        self.membership = getattr(user, 'family_membership', None)
        self.now = timezone.now()
    
    def check_content_access(self, content_type: str, content_id: int) -> Dict:
        """
        Check if user can access specific content
        
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
        
        # If user is family admin, allow access
        if self.membership and self.membership.is_admin:
            return {
                'access_granted': True,
                'reason': 'admin_access',
                'message': 'Admin account has full access'
            }
        
        # Check if user has no family membership (standalone user)
        if not self.membership:
            return {
                'access_granted': True,
                'reason': 'standalone_user',
                'message': 'Standalone user has full access'
            }
        
        # Check if membership is active
        if not self.membership.is_active:
            return {
                'access_granted': False,
                'reason': 'account_inactive',
                'message': 'Account is currently inactive'
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
                'message': f'This {content_type} has been blocked for your account',
                'can_request': True
            }
        
        # Check if content is approved
        if self._is_content_approved(content_type, content):
            return {
                'access_granted': True,
                'reason': 'content_approved',
                'message': f'This {content_type} has been approved for your account'
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
            'message': f'This {content_type} is appropriate for your account'
        }
    
    def filter_content_queryset(self, queryset, content_type: str):
        """
        Filter a queryset based on user restrictions
        
        Args:
            queryset: Django queryset to filter
            content_type: 'movie' or 'tv_show'
            
        Returns:
            Filtered queryset
        """
        # Admin or standalone users get full access
        if not self.membership or self.membership.is_admin:
            return queryset
        
        if content_type == 'movie':
            return self._filter_movie_queryset(queryset)
        elif content_type == 'tv_show':
            return self._filter_tv_show_queryset(queryset)
        else:
            return queryset.none()
    
    def _filter_movie_queryset(self, queryset):
        """Filter movie queryset based on user restrictions"""
        # Get allowed ratings
        allowed_ratings = self._get_allowed_movie_ratings()
        
        # Filter by rating
        filtered_queryset = queryset.filter(mpaa_rating__in=allowed_ratings)
        
        # Exclude blocked content
        blocked_movies = UserContentFilter.objects.filter(
            user=self.user,
            content_type='movie',
            is_blocked=True
        ).values_list('movie_id', flat=True)
        
        filtered_queryset = filtered_queryset.exclude(id__in=blocked_movies)
        
        # Include approved content regardless of rating
        approved_movies = ApprovedContent.objects.filter(
            user=self.user,
            movie__isnull=False
        ).values_list('movie_id', flat=True)
        
        final_queryset = filtered_queryset.union(
            queryset.filter(id__in=approved_movies)
        )
        
        return final_queryset
    
    def _filter_tv_show_queryset(self, queryset):
        """Filter TV show queryset based on user restrictions"""
        # Get allowed ratings
        allowed_ratings = self._get_allowed_tv_ratings()
        
        # Filter by rating
        filtered_queryset = queryset.filter(tv_rating__in=allowed_ratings)
        
        # Exclude blocked content
        blocked_shows = UserContentFilter.objects.filter(
            user=self.user,
            content_type='tv_show',
            is_blocked=True
        ).values_list('tv_show_id', flat=True)
        
        filtered_queryset = filtered_queryset.exclude(id__in=blocked_shows)
        
        # Include approved content regardless of rating
        approved_shows = ApprovedContent.objects.filter(
            user=self.user,
            tv_show__isnull=False
        ).values_list('tv_show_id', flat=True)
        
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
            limits = self.user.usage_limits
        except:
            return {'allowed': True, 'message': 'No time restrictions'}
        
        current_hour = self.now.hour
        is_weekend = self.now.weekday() >= 5
        
        # Determine bedtime and wakeup hours
        if is_weekend and limits.weekend_extended_hours:
            bedtime = limits.weekend_bedtime_hour
        else:
            bedtime = limits.bedtime_hour
        
        wakeup = limits.wakeup_hour
        
        # Check if current time is within allowed hours
        if wakeup <= bedtime:
            allowed = wakeup <= current_hour < bedtime
        else:
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
            'user': self.user,
            'content_type': content_type,
            'is_blocked': True
        }
        
        if content_type == 'movie':
            filter_kwargs['movie'] = content
        else:
            filter_kwargs['tv_show'] = content
        
        return UserContentFilter.objects.filter(**filter_kwargs).exists()
    
    def _is_content_approved(self, content_type: str, content) -> bool:
        """Check if content is approved"""
        filter_kwargs = {'user': self.user}
        
        if content_type == 'movie':
            filter_kwargs['movie'] = content
        else:
            filter_kwargs['tv_show'] = content
        
        approved_content = ApprovedContent.objects.filter(**filter_kwargs).first()
        
        if not approved_content:
            return False
        
        # Check if approval has expired
        if approved_content.is_expired:
            return False
        
        return True
    
    def _check_age_rating(self, content_type: str, content) -> Dict:
        """Check if content rating is appropriate for user age"""
        if content_type == 'movie':
            return self._check_movie_rating(content)
        else:
            return self._check_tv_rating(content)
    
    def _check_movie_rating(self, movie: Movie) -> Dict:
        """Check if movie rating is appropriate"""
        if not movie.mpaa_rating:
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
                'message': f'Rating {movie.mpaa_rating} exceeds your limit of {self.membership.max_movie_rating}'
            }
    
    def _check_tv_rating(self, tv_show: TVShow) -> Dict:
        """Check if TV show rating is appropriate"""
        if not tv_show.tv_rating:
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
                'message': f'Rating {tv_show.tv_rating} exceeds your limit of {self.membership.max_tv_rating}'
            }
    
    def _get_allowed_movie_ratings(self) -> List[str]:
        """Get list of allowed movie ratings for user"""
        if not self.membership:
            return self.MOVIE_RATING_HIERARCHY
        
        try:
            max_rating_index = self.MOVIE_RATING_HIERARCHY.index(self.membership.max_movie_rating)
            return self.MOVIE_RATING_HIERARCHY[:max_rating_index + 1]
        except ValueError:
            return ['G']
    
    def _get_allowed_tv_ratings(self) -> List[str]:
        """Get list of allowed TV ratings for user"""
        if not self.membership:
            return self.TV_RATING_HIERARCHY
        
        try:
            max_rating_index = self.TV_RATING_HIERARCHY.index(self.membership.max_tv_rating)
            return self.TV_RATING_HIERARCHY[:max_rating_index + 1]
        except ValueError:
            return ['TV-Y']
    
    def log_activity(self, activity_type: str, content_type: str = None, 
                    content_id: int = None, description: str = '', 
                    metadata: Dict = None):
        """Log activity for the user"""
        activity_data = {
            'user': self.user,
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
        
        UserActivity.objects.create(**activity_data)


class UserContentRequestService:
    """
    Service for handling content requests
    """
    
    @staticmethod
    def create_request(user: User, content_type: str, content_id: int, 
                      message: str = '') -> UserContentRequest:
        """
        Create a content request
        
        Args:
            user: User making the request
            content_type: 'movie' or 'tv_show'
            content_id: ID of the content
            message: Optional message with the request
            
        Returns:
            UserContentRequest: The created request
        """
        # Get content object
        content = None
        if content_type == 'movie':
            content = Movie.objects.get(id=content_id)
        elif content_type == 'tv_show':
            content = TVShow.objects.get(id=content_id)
        
        if not content:
            raise ValidationError(f"Content not found: {content_type} {content_id}")
        
        # Create request
        request_data = {
            'user': user,
            'request_message': message,
            'status': 'pending'
        }
        
        if content_type == 'movie':
            request_data['movie'] = content
        else:
            request_data['tv_show'] = content
        
        request = UserContentRequest.objects.create(**request_data)
        
        # Try auto-approval if user is admin
        request.auto_approve_if_admin()
        
        # Log activity
        filter_service = UserContentFilterService(user)
        filter_service.log_activity(
            activity_type='content_request',
            content_type=content_type,
            content_id=content_id,
            description=f"Requested access to {content.title}"
        )
        
        return request
    
    @staticmethod
    def approve_request(request: UserContentRequest, approved_by: User, 
                       response_message: str = '', temporary_access: bool = False,
                       expires_at: datetime = None) -> bool:
        """
        Approve a content request
        
        Args:
            request: UserContentRequest to approve
            approved_by: User approving the request
            response_message: Response message
            temporary_access: Whether access is temporary
            expires_at: When temporary access expires
            
        Returns:
            bool: True if approval was successful
        """
        if request.status != 'pending':
            raise ValidationError("Only pending requests can be approved.")
        
        # Update request
        request.status = 'approved'
        request.response_message = response_message
        request.reviewed_by = approved_by
        request.reviewed_at = timezone.now()
        request.temporary_access = temporary_access
        request.access_expires_at = expires_at
        request.save()
        
        # Create approved content entry
        ApprovedContent.objects.create(
            user=request.user,
            movie=request.movie,
            tv_show=request.tv_show,
            approved_by=approved_by,
            approval_reason=response_message,
            permanent_access=not temporary_access,
            expires_at=expires_at
        )
        
        # Log activity
        filter_service = UserContentFilterService(request.user)
        filter_service.log_activity(
            activity_type='request_approved',
            description=f"Request approved: {request.content_title}"
        )
        
        return True
    
    @staticmethod
    def deny_request(request: UserContentRequest, denied_by: User, 
                    response_message: str = '') -> bool:
        """
        Deny a content request
        
        Args:
            request: UserContentRequest to deny
            denied_by: User denying the request
            response_message: Response message
            
        Returns:
            bool: True if denial was successful
        """
        if request.status != 'pending':
            raise ValidationError("Only pending requests can be denied.")
        
        # Update request
        request.status = 'denied'
        request.response_message = response_message
        request.reviewed_by = denied_by
        request.reviewed_at = timezone.now()
        request.save()
        
        # Log activity
        filter_service = UserContentFilterService(request.user)
        filter_service.log_activity(
            activity_type='request_denied',
            description=f"Request denied: {request.content_title}"
        )
        
        return True


class UsageLimitService:
    """
    Service for usage limit checking and enforcement
    """
    
    def __init__(self, user: User):
        self.user = user
        self.now = timezone.now()
    
    def check_request_limits(self) -> Dict:
        """
        Check if user has exceeded request limits
        
        Returns:
            Dict with limit status and details
        """
        try:
            limits = self.user.usage_limits
        except:
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
    
    def _check_daily_requests(self, limits: UserLimits) -> Dict:
        """Check daily request limit"""
        daily_start = self.now.replace(hour=0, minute=0, second=0, microsecond=0)
        daily_count = UserContentRequest.objects.filter(
            user=self.user,
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
    
    def _check_weekly_requests(self, limits: UserLimits) -> Dict:
        """Check weekly request limit"""
        weekly_start = self.now - timedelta(days=7)
        weekly_count = UserContentRequest.objects.filter(
            user=self.user,
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
    
    def _check_monthly_requests(self, limits: UserLimits) -> Dict:
        """Check monthly request limit"""
        monthly_start = self.now - timedelta(days=30)
        monthly_count = UserContentRequest.objects.filter(
            user=self.user,
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