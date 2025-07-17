"""
Example usage of the Family Profile Management & Parental Controls system

This file demonstrates how to use the various components of the system.
"""

from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from .family_models import (
    FamilyProfile,
    ContentFilter,
    ContentRequest,
    ProfileLimits,
    ProfileActivity,
    ParentApprovedContent,
)
from .content_filtering import ContentFilterService, UsageLimitService
from .security_utils import COPPAComplianceService, SecurityService
from movies.models import Movie
from tv_shows.models import TVShow


def create_family_profile_example():
    """
    Example: Creating a family profile for a child
    """
    # Get parent user
    parent = User.objects.get(username='parent_user')
    
    # Create child profile
    child_profile = FamilyProfile.objects.create(
        parent_user=parent,
        profile_name="Emma",
        age=10,
        max_movie_rating='PG',
        max_tv_rating='TV-G',
        is_active=True
    )
    
    # Create default limits
    ProfileLimits.objects.create(
        profile=child_profile,
        daily_request_limit=5,
        weekly_request_limit=20,
        monthly_request_limit=50,
        daily_viewing_limit=120,  # 2 hours
        bedtime_hour=20,  # 8 PM
        wakeup_hour=7,   # 7 AM
        weekend_extended_hours=True,
        weekend_bedtime_hour=21  # 9 PM on weekends
    )
    
    print(f"Created profile: {child_profile}")
    return child_profile


def content_filtering_example():
    """
    Example: Using content filtering service
    """
    # Get profile
    profile = FamilyProfile.objects.get(profile_name="Emma")
    
    # Create content filter service
    filter_service = ContentFilterService(profile)
    
    # Check if profile can access a specific movie
    movie = Movie.objects.first()
    if movie:
        access_result = filter_service.check_content_access('movie', movie.id)
        print(f"Access check for {movie.title}: {access_result}")
    
    # Filter movie queryset
    all_movies = Movie.objects.all()
    filtered_movies = filter_service.filter_content_queryset(all_movies, 'movie')
    print(f"Filtered movies: {filtered_movies.count()} out of {all_movies.count()}")
    
    # Filter TV show queryset
    all_tv_shows = TVShow.objects.all()
    filtered_tv_shows = filter_service.filter_content_queryset(all_tv_shows, 'tv_show')
    print(f"Filtered TV shows: {filtered_tv_shows.count()} out of {all_tv_shows.count()}")


def block_content_example():
    """
    Example: Blocking specific content for a profile
    """
    # Get profile and content
    profile = FamilyProfile.objects.get(profile_name="Emma")
    movie = Movie.objects.first()
    
    if movie:
        # Block the movie
        content_filter = ContentFilter.objects.create(
            profile=profile,
            content_type='movie',
            movie=movie,
            reason="Too scary for child",
            is_blocked=True
        )
        
        print(f"Blocked {movie.title} for {profile.profile_name}")
        
        # Log the activity
        ProfileActivity.objects.create(
            profile=profile,
            activity_type='content_blocked',
            movie=movie,
            description=f"Parent blocked {movie.title}"
        )


def content_request_example():
    """
    Example: Child requesting access to blocked content
    """
    # Get profile and blocked content
    profile = FamilyProfile.objects.get(profile_name="Emma")
    movie = Movie.objects.first()
    
    if movie:
        # Create content request
        content_request = ContentRequest.objects.create(
            profile=profile,
            movie=movie,
            request_message="Please can I watch this movie? My friend said it's good.",
            status='pending'
        )
        
        print(f"Created request: {content_request}")
        
        # Log the activity
        ProfileActivity.objects.create(
            profile=profile,
            activity_type='content_request',
            movie=movie,
            description=f"Child requested access to {movie.title}"
        )
        
        return content_request


def approve_content_request_example():
    """
    Example: Parent approving a content request
    """
    # Get pending request
    request = ContentRequest.objects.filter(status='pending').first()
    
    if request:
        # Approve the request
        request.status = 'approved'
        request.parent_response = "You can watch this, but only on weekends."
        request.reviewed_by = request.profile.parent_user
        request.reviewed_at = timezone.now()
        request.temporary_access = True
        request.access_expires_at = timezone.now() + timedelta(days=7)
        request.save()
        
        # Create approved content entry
        ParentApprovedContent.objects.create(
            profile=request.profile,
            movie=request.movie,
            approved_by=request.profile.parent_user,
            approval_reason="Weekend viewing approved",
            permanent_access=False,
            expires_at=request.access_expires_at
        )
        
        # Log the activity
        ProfileActivity.objects.create(
            profile=request.profile,
            activity_type='request_approved',
            movie=request.movie,
            description=f"Parent approved access to {request.movie.title}"
        )
        
        print(f"Approved request: {request}")


def usage_limits_example():
    """
    Example: Checking usage limits
    """
    # Get profile
    profile = FamilyProfile.objects.get(profile_name="Emma")
    
    # Create usage limit service
    limit_service = UsageLimitService(profile)
    
    # Check request limits
    limit_check = limit_service.check_request_limits()
    print(f"Request limits check: {limit_check}")
    
    # Get usage statistics
    usage_stats = limit_service.get_usage_stats()
    print(f"Usage statistics: {usage_stats}")


def coppa_compliance_example():
    """
    Example: COPPA compliance checking
    """
    # Get profile
    profile = FamilyProfile.objects.get(profile_name="Emma")
    
    # Check if profile is COPPA protected
    is_coppa_protected = COPPAComplianceService.is_coppa_protected(profile)
    print(f"Is COPPA protected: {is_coppa_protected}")
    
    # Get data collection restrictions
    restrictions = COPPAComplianceService.get_data_collection_restrictions(profile)
    print(f"Data collection restrictions: {restrictions}")
    
    # Sanitize activity data
    activity_data = {
        'activity_type': 'content_view',
        'timestamp': timezone.now(),
        'description': 'Watched a movie',
        'metadata': {
            'movie_title': 'Example Movie',
            'watch_duration': 120,
            'user_agent': 'Mozilla/5.0...',
            'ip_address': '192.168.1.1'
        }
    }
    
    sanitized_data = COPPAComplianceService.sanitize_activity_data(profile, activity_data)
    print(f"Sanitized activity data: {sanitized_data}")


def security_example():
    """
    Example: Security features
    """
    # Get user and profile
    parent = User.objects.get(username='parent_user')
    profile = FamilyProfile.objects.get(profile_name="Emma")
    
    # Verify parent access
    has_access = SecurityService.verify_parent_access(parent, profile)
    print(f"Parent has access: {has_access}")
    
    # Check profile creation limits
    limits_check = SecurityService.validate_profile_limits(parent)
    print(f"Profile creation limits: {limits_check}")
    
    # Log security event
    SecurityService.log_security_event(
        user=parent,
        event_type='profile_access',
        description='Parent accessed child profile settings',
        profile=profile
    )


def parental_dashboard_example():
    """
    Example: Generating parental dashboard data
    """
    # Get all profiles for parent
    parent = User.objects.get(username='parent_user')
    profiles = FamilyProfile.objects.filter(parent_user=parent)
    
    dashboard_data = []
    
    for profile in profiles:
        # Calculate statistics
        now = timezone.now()
        daily_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        profile_stats = {
            'profile_id': profile.id,
            'profile_name': profile.profile_name,
            'age': profile.age,
            'is_active': profile.is_active,
            'total_requests': ContentRequest.objects.filter(profile=profile).count(),
            'pending_requests': ContentRequest.objects.filter(
                profile=profile, status='pending'
            ).count(),
            'daily_requests': ContentRequest.objects.filter(
                profile=profile, created_at__gte=daily_start
            ).count(),
            'blocked_content': ContentFilter.objects.filter(
                profile=profile, is_blocked=True
            ).count(),
            'approved_content': ParentApprovedContent.objects.filter(
                profile=profile
            ).count(),
            'recent_activities': ProfileActivity.objects.filter(
                profile=profile
            ).order_by('-timestamp')[:5]
        }
        
        dashboard_data.append(profile_stats)
    
    print(f"Dashboard data: {dashboard_data}")
    return dashboard_data


def api_usage_examples():
    """
    Example API endpoint usage (pseudo-code)
    """
    print("""
    API Usage Examples:
    
    1. Create Family Profile:
    POST /accounts/api/family/profiles/
    {
        "profile_name": "Emma",
        "age": 10,
        "max_movie_rating": "PG",
        "max_tv_rating": "TV-G"
    }
    
    2. Check Content Access:
    GET /accounts/api/family/profiles/1/content_access_check/?content_type=movie&content_id=123
    
    3. Block Content:
    POST /accounts/api/family/content-filters/
    {
        "profile": 1,
        "content_type": "movie",
        "movie": 123,
        "reason": "Too scary"
    }
    
    4. Request Content Access:
    POST /accounts/api/family/content-requests/
    {
        "profile": 1,
        "movie": 123,
        "request_message": "Please can I watch this?"
    }
    
    5. Approve Request:
    POST /accounts/api/family/content-requests/1/approve/
    {
        "parent_response": "You can watch this on weekends",
        "temporary_access": true,
        "access_expires_at": "2024-01-07T00:00:00Z"
    }
    
    6. Get Parental Dashboard:
    GET /accounts/api/family/dashboard/
    
    7. Get Profile Activities:
    GET /accounts/api/family/profile-activities/by_profile/?profile_id=1
    
    8. Set Usage Limits:
    POST /accounts/api/family/profile-limits/
    {
        "profile": 1,
        "daily_request_limit": 10,
        "bedtime_hour": 20,
        "wakeup_hour": 7
    }
    """)


if __name__ == "__main__":
    print("Family Profile Management & Parental Controls - Usage Examples")
    print("=" * 60)
    
    # Run examples (uncomment as needed)
    # create_family_profile_example()
    # content_filtering_example()
    # block_content_example()
    # content_request_example()
    # approve_content_request_example()
    # usage_limits_example()
    # coppa_compliance_example()
    # security_example()
    # parental_dashboard_example()
    api_usage_examples()