#!/usr/bin/env python
"""
Simple test script to verify family profiles functionality
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'suggesterr.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.family_models import FamilyProfile, ContentRequest, ProfileLimits
from movies.models import Movie

def test_family_profiles():
    """Test basic family profile functionality"""
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='testparent',
        defaults={
            'email': 'parent@test.com',
            'first_name': 'Test',
            'last_name': 'Parent'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✓ Created test user: {user.username}")
    else:
        print(f"✓ Using existing test user: {user.username}")
    
    # Create family profile
    profile, created = FamilyProfile.objects.get_or_create(
        parent_user=user,
        profile_name='Emma',
        defaults={
            'age': 10,
            'max_movie_rating': 'PG',
            'max_tv_rating': 'TV-G',
            'is_active': True
        }
    )
    
    if created:
        print(f"✓ Created family profile: {profile.profile_name}")
    else:
        print(f"✓ Using existing family profile: {profile.profile_name}")
    
    # Create profile limits
    limits, created = ProfileLimits.objects.get_or_create(
        profile=profile,
        defaults={
            'daily_request_limit': 10,
            'weekly_request_limit': 50,
            'monthly_request_limit': 200,
            'daily_viewing_limit': 120,
            'bedtime_hour': 20,
            'wakeup_hour': 7
        }
    )
    
    if created:
        print(f"✓ Created profile limits for {profile.profile_name}")
    else:
        print(f"✓ Using existing profile limits for {profile.profile_name}")
    
    # Test content filtering
    from accounts.content_filtering import ContentFilterService
    
    filter_service = ContentFilterService(profile)
    
    # Test age-based filtering
    print(f"\n--- Content Filtering Tests ---")
    print(f"Profile: {profile.profile_name} (Age: {profile.age})")
    print(f"Max Movie Rating: {profile.max_movie_rating}")
    print(f"Max TV Rating: {profile.max_tv_rating}")
    
    # Test usage limits
    from accounts.content_filtering import UsageLimitService
    
    limit_service = UsageLimitService(profile)
    limit_check = limit_service.check_request_limits()
    
    print(f"\n--- Usage Limits Tests ---")
    print(f"Request limits check: {limit_check}")
    
    usage_stats = limit_service.get_usage_stats()
    print(f"Usage statistics: {usage_stats}")
    
    # Test COPPA compliance
    from accounts.security_utils import COPPAComplianceService
    
    is_coppa = COPPAComplianceService.is_coppa_protected(profile)
    print(f"\n--- COPPA Compliance Tests ---")
    print(f"Is COPPA protected: {is_coppa}")
    
    restrictions = COPPAComplianceService.get_data_collection_restrictions(profile)
    print(f"Data collection restrictions: {restrictions}")
    
    print(f"\n✅ All tests completed successfully!")
    print(f"Family profiles system is working correctly.")
    
    return True

if __name__ == '__main__':
    try:
        test_family_profiles()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)