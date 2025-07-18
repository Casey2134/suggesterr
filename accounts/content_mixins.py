from django.db.models import Q
from django.http import JsonResponse
from django.contrib import messages
from .family_models import FamilyProfile, ContentRequest, ProfileActivity
from .content_filtering import ContentFilterService, UsageLimitService
from .security_utils import COPPAComplianceService


class FamilyProfileMixin:
    """
    Mixin to add family profile functionality to views
    """
    
    def get_filtered_queryset(self, queryset, content_type):
        """
        Filter queryset based on active family profile
        
        Args:
            queryset: Base queryset to filter
            content_type: 'movie' or 'tv_show'
            
        Returns:
            Filtered queryset
        """
        # If no profile is active, return full queryset (parent view)
        if not hasattr(self.request, 'family_profile') or not self.request.family_profile:
            return queryset
        
        # Use content filter service to filter queryset
        filter_service = ContentFilterService(self.request.family_profile)
        return filter_service.filter_content_queryset(queryset, content_type)
    
    def check_content_access(self, content_type, content_id):
        """
        Check if current profile can access specific content
        
        Args:
            content_type: 'movie' or 'tv_show'
            content_id: ID of content to check
            
        Returns:
            Dict with access status
        """
        # If no profile is active, allow access (parent view)
        if not hasattr(self.request, 'family_profile') or not self.request.family_profile:
            return {
                'access_granted': True,
                'reason': 'parent_account',
                'message': 'Parent account has full access'
            }
        
        # Use content filter service to check access
        filter_service = ContentFilterService(self.request.family_profile)
        return filter_service.check_content_access(content_type, content_id)
    
    def request_content_access(self, content_type, content_id, message=''):
        """
        Create a content access request for blocked content
        
        Args:
            content_type: 'movie' or 'tv_show'
            content_id: ID of content to request
            message: Optional message from child
            
        Returns:
            Dict with request status
        """
        # Only allowed for child profiles
        if not hasattr(self.request, 'family_profile') or not self.request.family_profile:
            return {
                'success': False,
                'error': 'Content requests are only available for child profiles'
            }
        
        profile = self.request.family_profile
        
        # Check usage limits
        limit_service = UsageLimitService(profile)
        limit_check = limit_service.check_request_limits()
        
        if not limit_check['allowed']:
            return {
                'success': False,
                'error': limit_check['message']
            }
        
        # Create request
        try:
            request_data = {
                'profile': profile,
                'request_message': message,
                'status': 'pending'
            }
            
            if content_type == 'movie':
                from movies.models import Movie
                request_data['movie'] = Movie.objects.get(id=content_id)
            else:
                from tv_shows.models import TVShow
                request_data['tv_show'] = TVShow.objects.get(id=content_id)
            
            content_request = ContentRequest.objects.create(**request_data)
            
            # Log activity
            filter_service = ContentFilterService(profile)
            filter_service.log_activity(
                activity_type='content_request',
                content_type=content_type,
                content_id=content_id,
                description=f"Requested access to {content_request.content_title}"
            )
            
            return {
                'success': True,
                'request_id': content_request.id,
                'message': 'Request submitted successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to create request: {str(e)}'
            }
    
    def log_content_view(self, content_type, content_id):
        """
        Log content viewing activity
        
        Args:
            content_type: 'movie' or 'tv_show'
            content_id: ID of content viewed
        """
        # Only log for child profiles
        if not hasattr(self.request, 'family_profile') or not self.request.family_profile:
            return
        
        profile = self.request.family_profile
        
        # Check COPPA compliance
        if COPPAComplianceService.is_coppa_protected(profile):
            # Limited logging for COPPA compliance
            activity_data = {
                'activity_type': 'content_view',
                'description': f"Viewed {content_type}",
                'metadata': {
                    'content_type': content_type,
                    'coppa_protected': True
                }
            }
        else:
            # Full logging for non-COPPA profiles
            activity_data = {
                'activity_type': 'content_view',
                'content_type': content_type,
                'content_id': content_id,
                'description': f"Viewed {content_type} (ID: {content_id})"
            }
        
        filter_service = ContentFilterService(profile)
        filter_service.log_activity(**activity_data)
    
    def get_profile_context(self):
        """
        Get context data for templates
        
        Returns:
            Dict with profile context
        """
        if hasattr(self.request, 'profile_context'):
            return self.request.profile_context
        
        return {
            'profile_id': None,
            'profile_name': 'Parent Account',
            'profile_age': None,
            'max_movie_rating': None,
            'max_tv_rating': None,
        }


class ContentRequestMixin:
    """
    Mixin to handle content request actions
    """
    
    def handle_content_request(self, request):
        """
        Handle AJAX content request
        
        Args:
            request: Django request object
            
        Returns:
            JsonResponse
        """
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # Get request data
        content_type = request.POST.get('content_type')
        content_id = request.POST.get('content_id')
        message = request.POST.get('message', '')
        
        if not content_type or not content_id:
            return JsonResponse({'error': 'Content type and ID required'}, status=400)
        
        # Create mixin instance to use methods
        mixin = FamilyProfileMixin()
        mixin.request = request
        
        # Check access first
        access_check = mixin.check_content_access(content_type, content_id)
        
        if access_check['access_granted']:
            return JsonResponse({
                'success': True,
                'access_granted': True,
                'message': 'Content is already accessible'
            })
        
        # Create request
        request_result = mixin.request_content_access(content_type, content_id, message)
        
        if request_result['success']:
            return JsonResponse({
                'success': True,
                'request_id': request_result['request_id'],
                'message': request_result['message']
            })
        else:
            return JsonResponse({
                'success': False,
                'error': request_result['error']
            }, status=400)


class ContentAccessMixin:
    """
    Mixin to handle content access checks
    """
    
    def handle_content_access_check(self, request):
        """
        Handle AJAX content access check
        
        Args:
            request: Django request object
            
        Returns:
            JsonResponse
        """
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        # Get request data
        content_type = request.GET.get('content_type')
        content_id = request.GET.get('content_id')
        
        if not content_type or not content_id:
            return JsonResponse({'error': 'Content type and ID required'}, status=400)
        
        # Create mixin instance to use methods
        mixin = FamilyProfileMixin()
        mixin.request = request
        
        # Check access
        access_check = mixin.check_content_access(content_type, content_id)
        
        return JsonResponse({
            'access_granted': access_check['access_granted'],
            'reason': access_check['reason'],
            'message': access_check['message'],
            'can_request': access_check.get('can_request', False)
        })


class ContentViewMixin:
    """
    Mixin to handle content viewing logging
    """
    
    def log_content_view(self, content_type, content_id):
        """
        Log content view with proper profile context
        
        Args:
            content_type: 'movie' or 'tv_show'
            content_id: ID of content viewed
        """
        mixin = FamilyProfileMixin()
        mixin.request = self.request
        mixin.log_content_view(content_type, content_id)