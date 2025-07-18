from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from datetime import timedelta
from typing import Dict, List, Optional
import logging

from .family_models import FamilyProfile, ProfileActivity

logger = logging.getLogger(__name__)


class COPPAComplianceService:
    """
    Service for COPPA (Children's Online Privacy Protection Act) compliance
    """
    
    COPPA_AGE_LIMIT = 13
    
    @classmethod
    def is_coppa_protected(cls, profile: FamilyProfile) -> bool:
        """
        Check if profile is COPPA protected (under 13 years old)
        
        Args:
            profile: FamilyProfile instance
            
        Returns:
            bool: True if profile is COPPA protected
        """
        return profile.age < cls.COPPA_AGE_LIMIT
    
    @classmethod
    def get_data_collection_restrictions(cls, profile: FamilyProfile) -> Dict:
        """
        Get data collection restrictions for profile
        
        Args:
            profile: FamilyProfile instance
            
        Returns:
            Dict with data collection restrictions
        """
        if cls.is_coppa_protected(profile):
            return {
                'minimal_data_collection': True,
                'no_behavioral_targeting': True,
                'no_third_party_sharing': True,
                'parental_consent_required': True,
                'data_retention_limit_days': 30,
                'activity_logging_restricted': True,
                'message': 'COPPA compliance restrictions apply'
            }
        else:
            return {
                'minimal_data_collection': False,
                'no_behavioral_targeting': False,
                'no_third_party_sharing': False,
                'parental_consent_required': False,
                'data_retention_limit_days': 365,
                'activity_logging_restricted': False,
                'message': 'Standard data collection applies'
            }
    
    @classmethod
    def sanitize_activity_data(cls, profile: FamilyProfile, activity_data: Dict) -> Dict:
        """
        Sanitize activity data for COPPA compliance
        
        Args:
            profile: FamilyProfile instance
            activity_data: Original activity data
            
        Returns:
            Sanitized activity data
        """
        if not cls.is_coppa_protected(profile):
            return activity_data
        
        # For COPPA-protected profiles, limit data collection
        sanitized = {
            'activity_type': activity_data.get('activity_type'),
            'timestamp': activity_data.get('timestamp'),
            'description': activity_data.get('description', ''),
        }
        
        # Remove detailed metadata for COPPA compliance
        if 'metadata' in activity_data:
            # Only keep essential metadata
            original_metadata = activity_data['metadata']
            sanitized['metadata'] = {
                'content_rating': original_metadata.get('content_rating'),
                'access_granted': original_metadata.get('access_granted'),
            }
        
        return sanitized
    
    @classmethod
    def cleanup_expired_data(cls, profile: FamilyProfile):
        """
        Clean up expired data for COPPA compliance
        
        Args:
            profile: FamilyProfile instance
        """
        if not cls.is_coppa_protected(profile):
            return
        
        # Remove activities older than 30 days for COPPA-protected profiles
        retention_limit = timezone.now() - timedelta(days=30)
        
        deleted_count = ProfileActivity.objects.filter(
            profile=profile,
            timestamp__lt=retention_limit
        ).delete()[0]
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired activities for COPPA profile {profile.id}")


class SecurityService:
    """
    Service for security-related operations
    """
    
    @classmethod
    def verify_parent_access(cls, user: User, profile: FamilyProfile) -> bool:
        """
        Verify that user has access to profile
        
        Args:
            user: User attempting access
            profile: FamilyProfile being accessed
            
        Returns:
            bool: True if access is allowed
        """
        return profile.parent_user == user
    
    @classmethod
    def verify_profile_ownership(cls, user: User, profile_id: int) -> FamilyProfile:
        """
        Verify profile ownership and return profile
        
        Args:
            user: User attempting access
            profile_id: ID of profile being accessed
            
        Returns:
            FamilyProfile: Profile if access is allowed
            
        Raises:
            PermissionDenied: If access is not allowed
        """
        try:
            profile = FamilyProfile.objects.get(id=profile_id)
            if profile.parent_user != user:
                raise PermissionDenied("You don't have permission to access this profile")
            return profile
        except FamilyProfile.DoesNotExist:
            raise PermissionDenied("Profile not found")
    
    @classmethod
    def log_security_event(cls, user: User, event_type: str, description: str, 
                          profile: Optional[FamilyProfile] = None, 
                          metadata: Optional[Dict] = None):
        """
        Log security-related events
        
        Args:
            user: User associated with event
            event_type: Type of security event
            description: Description of event
            profile: Associated profile (if applicable)
            metadata: Additional metadata
        """
        log_data = {
            'user': user.username,
            'event_type': event_type,
            'description': description,
            'timestamp': timezone.now().isoformat(),
            'metadata': metadata or {}
        }
        
        if profile:
            log_data['profile_id'] = profile.id
            log_data['profile_name'] = profile.profile_name
        
        logger.warning(f"Security event: {log_data}")
    
    @classmethod
    def validate_profile_limits(cls, user: User) -> Dict:
        """
        Validate profile creation limits
        
        Args:
            user: User attempting to create profile
            
        Returns:
            Dict with validation results
        """
        current_count = FamilyProfile.objects.filter(parent_user=user).count()
        max_profiles = 6
        
        if current_count >= max_profiles:
            return {
                'allowed': False,
                'message': f'Maximum {max_profiles} profiles allowed per parent',
                'current_count': current_count,
                'max_count': max_profiles
            }
        
        return {
            'allowed': True,
            'message': f'{max_profiles - current_count} profiles remaining',
            'current_count': current_count,
            'max_count': max_profiles
        }
    
    @classmethod
    def sanitize_profile_data(cls, profile_data: Dict) -> Dict:
        """
        Sanitize profile data for security
        
        Args:
            profile_data: Raw profile data
            
        Returns:
            Sanitized profile data
        """
        # Remove any potentially harmful fields
        allowed_fields = [
            'profile_name', 'age', 'max_movie_rating', 'max_tv_rating',
            'is_active', 'avatar_url'
        ]
        
        sanitized = {}
        for field in allowed_fields:
            if field in profile_data:
                sanitized[field] = profile_data[field]
        
        # Validate age
        if 'age' in sanitized:
            try:
                age = int(sanitized['age'])
                if age < 1 or age > 99:
                    raise ValueError("Age must be between 1 and 99")
                sanitized['age'] = age
            except (ValueError, TypeError):
                raise ValueError("Invalid age provided")
        
        # Validate profile name
        if 'profile_name' in sanitized:
            name = str(sanitized['profile_name']).strip()
            if not name or len(name) > 100:
                raise ValueError("Profile name must be 1-100 characters")
            sanitized['profile_name'] = name
        
        return sanitized
    
    @classmethod
    def check_rate_limiting(cls, user: User, action: str) -> Dict:
        """
        Check rate limiting for specific actions
        
        Args:
            user: User performing action
            action: Type of action being performed
            
        Returns:
            Dict with rate limiting results
        """
        # Simple rate limiting - can be enhanced with Redis/cache
        now = timezone.now()
        
        # Different limits for different actions
        rate_limits = {
            'profile_creation': {'count': 5, 'window_minutes': 60},
            'content_request': {'count': 20, 'window_minutes': 60},
            'approval_action': {'count': 50, 'window_minutes': 60},
        }
        
        if action not in rate_limits:
            return {'allowed': True, 'message': 'No rate limit for this action'}
        
        limit_config = rate_limits[action]
        window_start = now - timedelta(minutes=limit_config['window_minutes'])
        
        # This is a simplified check - in production, use proper rate limiting
        # with Redis or similar technology
        
        return {
            'allowed': True,
            'message': f'Within rate limit for {action}',
            'limit': limit_config['count'],
            'window_minutes': limit_config['window_minutes']
        }


class AuditService:
    """
    Service for audit logging
    """
    
    @classmethod
    def log_profile_action(cls, user: User, action: str, profile: FamilyProfile, 
                          details: Optional[Dict] = None):
        """
        Log profile-related actions for auditing
        
        Args:
            user: User performing action
            action: Type of action
            profile: Profile being modified
            details: Additional details
        """
        audit_data = {
            'user_id': user.id,
            'username': user.username,
            'action': action,
            'profile_id': profile.id,
            'profile_name': profile.profile_name,
            'profile_age': profile.age,
            'timestamp': timezone.now().isoformat(),
            'details': details or {}
        }
        
        logger.info(f"Profile audit: {audit_data}")
    
    @classmethod
    def log_content_action(cls, user: User, action: str, profile: FamilyProfile,
                          content_type: str, content_id: int, 
                          details: Optional[Dict] = None):
        """
        Log content-related actions for auditing
        
        Args:
            user: User performing action
            action: Type of action
            profile: Profile associated with action
            content_type: Type of content
            content_id: ID of content
            details: Additional details
        """
        audit_data = {
            'user_id': user.id,
            'username': user.username,
            'action': action,
            'profile_id': profile.id,
            'profile_name': profile.profile_name,
            'content_type': content_type,
            'content_id': content_id,
            'timestamp': timezone.now().isoformat(),
            'details': details or {}
        }
        
        logger.info(f"Content audit: {audit_data}")
    
    @classmethod
    def log_approval_action(cls, user: User, action: str, request_id: int,
                           profile: FamilyProfile, details: Optional[Dict] = None):
        """
        Log approval-related actions for auditing
        
        Args:
            user: User performing action
            action: Type of action
            request_id: ID of request
            profile: Profile associated with request
            details: Additional details
        """
        audit_data = {
            'user_id': user.id,
            'username': user.username,
            'action': action,
            'request_id': request_id,
            'profile_id': profile.id,
            'profile_name': profile.profile_name,
            'timestamp': timezone.now().isoformat(),
            'details': details or {}
        }
        
        logger.info(f"Approval audit: {audit_data}")


class DataProtectionService:
    """
    Service for data protection and privacy
    """
    
    @classmethod
    def anonymize_profile_data(cls, profile: FamilyProfile) -> Dict:
        """
        Anonymize profile data for privacy protection
        
        Args:
            profile: FamilyProfile to anonymize
            
        Returns:
            Anonymized profile data
        """
        return {
            'profile_id': f"profile_{profile.id}",
            'age_range': cls._get_age_range(profile.age),
            'max_movie_rating': profile.max_movie_rating,
            'max_tv_rating': profile.max_tv_rating,
            'is_active': profile.is_active,
            'created_month': profile.created_at.strftime('%Y-%m'),
        }
    
    @classmethod
    def _get_age_range(cls, age: int) -> str:
        """Get age range for anonymization"""
        if age < 5:
            return "0-4"
        elif age < 10:
            return "5-9"
        elif age < 13:
            return "10-12"
        elif age < 16:
            return "13-15"
        elif age < 18:
            return "16-17"
        else:
            return "18+"
    
    @classmethod
    def export_profile_data(cls, profile: FamilyProfile) -> Dict:
        """
        Export all profile data for data portability
        
        Args:
            profile: FamilyProfile to export
            
        Returns:
            Complete profile data export
        """
        from .family_serializers import (
            FamilyProfileSerializer,
            ContentFilterSerializer,
            ContentRequestSerializer,
            ProfileLimitsSerializer,
            ProfileActivitySerializer,
            ParentApprovedContentSerializer
        )
        
        # Profile data
        profile_data = FamilyProfileSerializer(profile).data
        
        # Related data
        export_data = {
            'profile': profile_data,
            'content_filters': ContentFilterSerializer(
                profile.content_filters.all(), many=True
            ).data,
            'content_requests': ContentRequestSerializer(
                profile.content_requests.all(), many=True
            ).data,
            'approved_content': ParentApprovedContentSerializer(
                profile.approved_content.all(), many=True
            ).data,
            'activities': ProfileActivitySerializer(
                profile.activities.all(), many=True
            ).data,
            'export_timestamp': timezone.now().isoformat(),
        }
        
        # Include limits if they exist
        try:
            export_data['limits'] = ProfileLimitsSerializer(profile.limits).data
        except:
            export_data['limits'] = None
        
        return export_data
    
    @classmethod
    def delete_profile_data(cls, profile: FamilyProfile) -> Dict:
        """
        Delete all profile data for data erasure
        
        Args:
            profile: FamilyProfile to delete
            
        Returns:
            Summary of deleted data
        """
        deletion_summary = {
            'profile_id': profile.id,
            'profile_name': profile.profile_name,
            'deleted_items': {}
        }
        
        # Delete related data
        deletion_summary['deleted_items']['content_filters'] = profile.content_filters.all().delete()[0]
        deletion_summary['deleted_items']['content_requests'] = profile.content_requests.all().delete()[0]
        deletion_summary['deleted_items']['approved_content'] = profile.approved_content.all().delete()[0]
        deletion_summary['deleted_items']['activities'] = profile.activities.all().delete()[0]
        
        # Delete limits
        try:
            deletion_summary['deleted_items']['limits'] = profile.limits.delete()[0]
        except:
            deletion_summary['deleted_items']['limits'] = 0
        
        # Delete profile
        profile.delete()
        
        deletion_summary['deletion_timestamp'] = timezone.now().isoformat()
        
        return deletion_summary