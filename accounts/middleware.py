from django.utils.deprecation import MiddlewareMixin
from .family_models import FamilyProfile
from .content_filtering import ContentFilterService


class FamilyProfileMiddleware(MiddlewareMixin):
    """
    Middleware to add family profile context to requests
    """
    
    def process_request(self, request):
        # Initialize profile-related attributes
        request.family_profile = None
        request.content_filter_service = None
        request.is_child_profile = False
        
        # Only process for authenticated users
        if not request.user.is_authenticated:
            return
        
        # Check if there's an active profile in session
        active_profile_id = request.session.get('active_profile_id')
        
        if active_profile_id:
            try:
                profile = FamilyProfile.objects.get(
                    id=active_profile_id,
                    parent_user=request.user,
                    is_active=True
                )
                request.family_profile = profile
                request.content_filter_service = ContentFilterService(profile)
                request.is_child_profile = True
                
                # Add profile info to context
                request.profile_context = {
                    'profile_id': profile.id,
                    'profile_name': profile.profile_name,
                    'profile_age': profile.age,
                    'max_movie_rating': profile.max_movie_rating,
                    'max_tv_rating': profile.max_tv_rating,
                }
                
            except FamilyProfile.DoesNotExist:
                # Profile doesn't exist or is inactive, clear session
                request.session.pop('active_profile_id', None)
                request.session.pop('active_profile_name', None)
                request.session.pop('active_profile_age', None)
        
        # If no active profile, user is browsing as parent
        if not request.family_profile:
            request.profile_context = {
                'profile_id': None,
                'profile_name': 'Parent Account',
                'profile_age': None,
                'max_movie_rating': None,
                'max_tv_rating': None,
            }
    
    def process_template_response(self, request, response):
        """Add profile context to template context"""
        if hasattr(response, 'context_data') and hasattr(request, 'profile_context'):
            if response.context_data is None:
                response.context_data = {}
            response.context_data['profile_context'] = request.profile_context
            response.context_data['is_child_profile'] = request.is_child_profile
        
        return response