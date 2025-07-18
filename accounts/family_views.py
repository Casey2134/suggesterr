from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta, datetime
from django.shortcuts import get_object_or_404

from .family_models import (
    FamilyProfile,
    ContentFilter,
    ContentRequest,
    ProfileLimits,
    ProfileActivity,
    ParentApprovedContent,
)
from .family_serializers import (
    FamilyProfileSerializer,
    ContentFilterSerializer,
    ContentRequestSerializer,
    ContentRequestApprovalSerializer,
    ProfileLimitsSerializer,
    ProfileActivitySerializer,
    ParentApprovedContentSerializer,
    ParentalDashboardSerializer,
)
from movies.models import Movie
from tv_shows.models import TVShow


class FamilyProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing family profiles
    """
    serializer_class = FamilyProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Only return profiles owned by the current user"""
        return FamilyProfile.objects.filter(parent_user=self.request.user)
    
    def perform_create(self, serializer):
        """Create profile with current user as parent"""
        serializer.save(parent_user=self.request.user)
        
        # Create default limits for the new profile
        profile = serializer.instance
        ProfileLimits.objects.create(profile=profile)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle profile active status"""
        profile = self.get_object()
        profile.is_active = not profile.is_active
        profile.save()
        
        # Log activity
        ProfileActivity.objects.create(
            profile=profile,
            activity_type='profile_toggled',
            description=f"Profile {'activated' if profile.is_active else 'deactivated'}"
        )
        
        return Response({
            'profile_id': profile.id,
            'is_active': profile.is_active,
            'message': f"Profile {'activated' if profile.is_active else 'deactivated'}"
        })
    
    @action(detail=True, methods=['get'])
    def content_access_check(self, request, pk=None):
        """Check if profile can access specific content"""
        profile = self.get_object()
        
        # Get content parameters
        content_type = request.query_params.get('content_type')
        content_id = request.query_params.get('content_id')
        
        if not content_type or not content_id:
            return Response(
                {'error': 'content_type and content_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check content access
        access_result = self._check_content_access(profile, content_type, content_id)
        
        return Response(access_result)
    
    def _check_content_access(self, profile, content_type, content_id):
        """Helper method to check content access"""
        from .content_filtering import ContentFilterService
        
        service = ContentFilterService(profile)
        return service.check_content_access(content_type, content_id)


class ContentFilterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing content filters
    """
    serializer_class = ContentFilterSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Only return filters for profiles owned by current user"""
        return ContentFilter.objects.filter(profile__parent_user=self.request.user)
    
    def perform_create(self, serializer):
        """Create filter with validation"""
        profile = serializer.validated_data['profile']
        
        # Verify profile ownership
        if profile.parent_user != self.request.user:
            raise permissions.PermissionDenied(
                "You can only create filters for your own profiles."
            )
        
        serializer.save()
        
        # Log activity
        content_name = (
            serializer.instance.movie.title if serializer.instance.movie
            else serializer.instance.tv_show.title
        )
        ProfileActivity.objects.create(
            profile=profile,
            activity_type='content_blocked',
            description=f"Content blocked: {content_name}",
            movie=serializer.instance.movie,
            tv_show=serializer.instance.tv_show
        )
    
    @action(detail=False, methods=['get'])
    def by_profile(self, request):
        """Get filters for specific profile"""
        profile_id = request.query_params.get('profile_id')
        if not profile_id:
            return Response(
                {'error': 'profile_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify profile ownership
        profile = get_object_or_404(
            FamilyProfile,
            id=profile_id,
            parent_user=request.user
        )
        
        filters = ContentFilter.objects.filter(profile=profile)
        serializer = self.get_serializer(filters, many=True)
        return Response(serializer.data)


class ContentRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing content requests
    """
    serializer_class = ContentRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Only return requests for profiles owned by current user"""
        return ContentRequest.objects.filter(profile__parent_user=self.request.user)
    
    def perform_create(self, serializer):
        """Create request with validation"""
        profile = serializer.validated_data['profile']
        
        # Verify profile ownership
        if profile.parent_user != self.request.user:
            raise permissions.PermissionDenied(
                "You can only create requests for your own profiles."
            )
        
        # Check usage limits
        self._check_usage_limits(profile)
        
        serializer.save()
        
        # Log activity
        content_name = (
            serializer.instance.movie.title if serializer.instance.movie
            else serializer.instance.tv_show.title
        )
        ProfileActivity.objects.create(
            profile=profile,
            activity_type='content_request',
            description=f"Content requested: {content_name}",
            movie=serializer.instance.movie,
            tv_show=serializer.instance.tv_show
        )
    
    def _check_usage_limits(self, profile):
        """Check if profile has exceeded usage limits"""
        try:
            limits = profile.limits
        except ProfileLimits.DoesNotExist:
            # Create default limits if they don't exist
            limits = ProfileLimits.objects.create(profile=profile)
        
        now = timezone.now()
        
        # Check daily limit
        daily_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        daily_requests = ContentRequest.objects.filter(
            profile=profile,
            created_at__gte=daily_start
        ).count()
        
        if daily_requests >= limits.daily_request_limit:
            raise permissions.PermissionDenied(
                f"Daily request limit ({limits.daily_request_limit}) exceeded."
            )
        
        # Check weekly limit
        weekly_start = now - timedelta(days=7)
        weekly_requests = ContentRequest.objects.filter(
            profile=profile,
            created_at__gte=weekly_start
        ).count()
        
        if weekly_requests >= limits.weekly_request_limit:
            raise permissions.PermissionDenied(
                f"Weekly request limit ({limits.weekly_request_limit}) exceeded."
            )
        
        # Check monthly limit
        monthly_start = now - timedelta(days=30)
        monthly_requests = ContentRequest.objects.filter(
            profile=profile,
            created_at__gte=monthly_start
        ).count()
        
        if monthly_requests >= limits.monthly_request_limit:
            raise permissions.PermissionDenied(
                f"Monthly request limit ({limits.monthly_request_limit}) exceeded."
            )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve content request"""
        content_request = self.get_object()
        
        # Verify request is for user's profile
        if content_request.profile.parent_user != request.user:
            raise permissions.PermissionDenied(
                "You can only approve requests for your own profiles."
            )
        
        if content_request.status != 'pending':
            return Response(
                {'error': 'Only pending requests can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use approval serializer
        serializer = ContentRequestApprovalSerializer(
            content_request,
            data={
                'status': 'approved',
                'parent_response': request.data.get('parent_response', ''),
                'temporary_access': request.data.get('temporary_access', False),
                'access_expires_at': request.data.get('access_expires_at')
            },
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            
            # Create approved content entry if approved
            if serializer.validated_data['status'] == 'approved':
                ParentApprovedContent.objects.create(
                    profile=content_request.profile,
                    movie=content_request.movie,
                    tv_show=content_request.tv_show,
                    approved_by=request.user,
                    approval_reason=serializer.validated_data.get('parent_response', ''),
                    permanent_access=not serializer.validated_data.get('temporary_access', False),
                    expires_at=serializer.validated_data.get('access_expires_at')
                )
            
            # Log activity
            content_name = content_request.content_title
            ProfileActivity.objects.create(
                profile=content_request.profile,
                activity_type='request_approved',
                description=f"Request approved: {content_name}",
                movie=content_request.movie,
                tv_show=content_request.tv_show
            )
            
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def deny(self, request, pk=None):
        """Deny content request"""
        content_request = self.get_object()
        
        # Verify request is for user's profile
        if content_request.profile.parent_user != request.user:
            raise permissions.PermissionDenied(
                "You can only deny requests for your own profiles."
            )
        
        if content_request.status != 'pending':
            return Response(
                {'error': 'Only pending requests can be denied'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use approval serializer
        serializer = ContentRequestApprovalSerializer(
            content_request,
            data={
                'status': 'denied',
                'parent_response': request.data.get('parent_response', '')
            },
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            
            # Log activity
            content_name = content_request.content_title
            ProfileActivity.objects.create(
                profile=content_request.profile,
                activity_type='request_denied',
                description=f"Request denied: {content_name}",
                movie=content_request.movie,
                tv_show=content_request.tv_show
            )
            
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending requests for all profiles"""
        pending_requests = self.get_queryset().filter(status='pending')
        serializer = self.get_serializer(pending_requests, many=True)
        return Response(serializer.data)


class ProfileLimitsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing profile limits
    """
    serializer_class = ProfileLimitsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Only return limits for profiles owned by current user"""
        return ProfileLimits.objects.filter(profile__parent_user=self.request.user)
    
    def perform_create(self, serializer):
        """Create limits with validation"""
        profile = serializer.validated_data['profile']
        
        # Verify profile ownership
        if profile.parent_user != self.request.user:
            raise permissions.PermissionDenied(
                "You can only set limits for your own profiles."
            )
        
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def by_profile(self, request):
        """Get limits for specific profile"""
        profile_id = request.query_params.get('profile_id')
        if not profile_id:
            return Response(
                {'error': 'profile_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify profile ownership
        profile = get_object_or_404(
            FamilyProfile,
            id=profile_id,
            parent_user=request.user
        )
        
        try:
            limits = profile.limits
            serializer = self.get_serializer(limits)
            return Response(serializer.data)
        except ProfileLimits.DoesNotExist:
            # Create default limits if they don't exist
            limits = ProfileLimits.objects.create(profile=profile)
            serializer = self.get_serializer(limits)
            return Response(serializer.data)


class ProfileActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing profile activity (read-only)
    """
    serializer_class = ProfileActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Only return activities for profiles owned by current user"""
        return ProfileActivity.objects.filter(profile__parent_user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_profile(self, request):
        """Get activities for specific profile"""
        profile_id = request.query_params.get('profile_id')
        if not profile_id:
            return Response(
                {'error': 'profile_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify profile ownership
        profile = get_object_or_404(
            FamilyProfile,
            id=profile_id,
            parent_user=request.user
        )
        
        activities = ProfileActivity.objects.filter(profile=profile)
        
        # Optional date filtering
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            activities = activities.filter(timestamp__gte=start_date)
        if end_date:
            activities = activities.filter(timestamp__lte=end_date)
        
        serializer = self.get_serializer(activities, many=True)
        return Response(serializer.data)


class ParentApprovedContentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing parent-approved content
    """
    serializer_class = ParentApprovedContentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Only return approved content for profiles owned by current user"""
        return ParentApprovedContent.objects.filter(profile__parent_user=self.request.user)
    
    def perform_create(self, serializer):
        """Create approved content with validation"""
        profile = serializer.validated_data['profile']
        
        # Verify profile ownership
        if profile.parent_user != self.request.user:
            raise permissions.PermissionDenied(
                "You can only approve content for your own profiles."
            )
        
        serializer.save(approved_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_profile(self, request):
        """Get approved content for specific profile"""
        profile_id = request.query_params.get('profile_id')
        if not profile_id:
            return Response(
                {'error': 'profile_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify profile ownership
        profile = get_object_or_404(
            FamilyProfile,
            id=profile_id,
            parent_user=request.user
        )
        
        approved_content = ParentApprovedContent.objects.filter(profile=profile)
        serializer = self.get_serializer(approved_content, many=True)
        return Response(serializer.data)


class ParentalDashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for parental dashboard overview
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Get dashboard overview for all profiles"""
        profiles = FamilyProfile.objects.filter(parent_user=request.user)
        dashboard_data = []
        
        for profile in profiles:
            profile_data = self._get_profile_dashboard_data(profile)
            dashboard_data.append(profile_data)
        
        return Response(dashboard_data)
    
    def retrieve(self, request, pk=None):
        """Get dashboard data for specific profile"""
        profile = get_object_or_404(
            FamilyProfile,
            id=pk,
            parent_user=request.user
        )
        
        profile_data = self._get_profile_dashboard_data(profile)
        return Response(profile_data)
    
    def _get_profile_dashboard_data(self, profile):
        """Generate dashboard data for a profile"""
        now = timezone.now()
        
        # Calculate date ranges
        daily_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        weekly_start = now - timedelta(days=7)
        monthly_start = now - timedelta(days=30)
        
        # Request statistics
        total_requests = ContentRequest.objects.filter(profile=profile).count()
        pending_requests = ContentRequest.objects.filter(
            profile=profile, status='pending'
        ).count()
        approved_requests = ContentRequest.objects.filter(
            profile=profile, status='approved'
        ).count()
        denied_requests = ContentRequest.objects.filter(
            profile=profile, status='denied'
        ).count()
        
        # Usage statistics
        daily_request_count = ContentRequest.objects.filter(
            profile=profile, created_at__gte=daily_start
        ).count()
        weekly_request_count = ContentRequest.objects.filter(
            profile=profile, created_at__gte=weekly_start
        ).count()
        monthly_request_count = ContentRequest.objects.filter(
            profile=profile, created_at__gte=monthly_start
        ).count()
        
        # Content statistics
        blocked_content_count = ContentFilter.objects.filter(
            profile=profile, is_blocked=True
        ).count()
        approved_content_count = ParentApprovedContent.objects.filter(
            profile=profile
        ).count()
        
        # Recent activities (last 10)
        recent_activities = ProfileActivity.objects.filter(
            profile=profile
        ).order_by('-timestamp')[:10]
        
        # Profile limits
        try:
            limits = profile.limits
        except ProfileLimits.DoesNotExist:
            limits = ProfileLimits.objects.create(profile=profile)
        
        # Serialize data
        return {
            'profile_id': profile.id,
            'profile_name': profile.profile_name,
            'age': profile.age,
            'is_active': profile.is_active,
            'total_requests': total_requests,
            'pending_requests': pending_requests,
            'approved_requests': approved_requests,
            'denied_requests': denied_requests,
            'daily_request_count': daily_request_count,
            'weekly_request_count': weekly_request_count,
            'monthly_request_count': monthly_request_count,
            'blocked_content_count': blocked_content_count,
            'approved_content_count': approved_content_count,
            'recent_activities': ProfileActivitySerializer(recent_activities, many=True).data,
            'limits': ProfileLimitsSerializer(limits).data,
        }