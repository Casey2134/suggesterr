from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from datetime import timedelta

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
from .family_group_serializers import (
    FamilyGroupSerializer,
    FamilyMembershipSerializer,
    UserContentFilterSerializer,
    UserContentRequestSerializer,
    UserContentRequestApprovalSerializer,
    UserLimitsSerializer,
    UserActivitySerializer,
    ApprovedContentSerializer,
    FamilyInvitationSerializer,
    FamilyDashboardSerializer,
    CreateFamilySerializer,
    JoinFamilySerializer,
    UserSerializer,
)
from .family_group_services import (
    FamilyGroupService,
    UserContentFilterService,
    UserContentRequestService,
    UsageLimitService,
)


class FamilyGroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing family groups
    """
    serializer_class = FamilyGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Only return family groups where user is admin"""
        return FamilyGroup.objects.filter(admin_user=self.request.user)
    
    def perform_create(self, serializer):
        """Create family group with current user as admin"""
        family = serializer.save(admin_user=self.request.user)
        
        # Create admin membership
        FamilyMembership.objects.create(
            user=self.request.user,
            family=family,
            is_admin=True,
            age=18,  # Default adult age
            max_movie_rating='NC-17',
            max_tv_rating='TV-MA'
        )
        
        # Create default limits for admin
        UserLimits.objects.create(
            user=self.request.user,
            daily_request_limit=999,
            weekly_request_limit=999,
            monthly_request_limit=999
        )
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get all family members"""
        family = self.get_object()
        memberships = FamilyMembership.objects.filter(family=family)
        serializer = FamilyMembershipSerializer(memberships, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def invite_member(self, request, pk=None):
        """Invite a new member to the family"""
        family = self.get_object()
        
        serializer = FamilyInvitationSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            invitation = serializer.save(family=family)
            
            # TODO: Send invitation email
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """Remove a member from the family"""
        family = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user_to_remove = User.objects.get(id=user_id)
            success = FamilyGroupService.remove_member(family, user_to_remove, request.user)
            
            if success:
                return Response({'message': 'Member removed successfully'})
            else:
                return Response(
                    {'error': 'Failed to remove member'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        """Get family dashboard data"""
        family = self.get_object()
        members = family.get_members()
        
        dashboard_data = []
        for member in members:
            member_data = self._get_member_dashboard_data(member)
            dashboard_data.append(member_data)
        
        return Response(dashboard_data)
    
    def _get_member_dashboard_data(self, user):
        """Generate dashboard data for a family member"""
        now = timezone.now()
        
        # Get membership info
        try:
            membership = user.family_membership
        except:
            membership = None
        
        # Calculate date ranges
        daily_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        weekly_start = now - timedelta(days=7)
        monthly_start = now - timedelta(days=30)
        
        # Request statistics
        total_requests = UserContentRequest.objects.filter(user=user).count()
        pending_requests = UserContentRequest.objects.filter(
            user=user, status='pending'
        ).count()
        approved_requests = UserContentRequest.objects.filter(
            user=user, status__in=['approved', 'auto_approved']
        ).count()
        denied_requests = UserContentRequest.objects.filter(
            user=user, status='denied'
        ).count()
        
        # Usage statistics
        daily_request_count = UserContentRequest.objects.filter(
            user=user, created_at__gte=daily_start
        ).count()
        weekly_request_count = UserContentRequest.objects.filter(
            user=user, created_at__gte=weekly_start
        ).count()
        monthly_request_count = UserContentRequest.objects.filter(
            user=user, created_at__gte=monthly_start
        ).count()
        
        # Content statistics
        blocked_content_count = UserContentFilter.objects.filter(
            user=user, is_blocked=True
        ).count()
        approved_content_count = ApprovedContent.objects.filter(
            user=user
        ).count()
        
        # Recent activities
        recent_activities = UserActivity.objects.filter(
            user=user
        ).order_by('-timestamp')[:10]
        
        # User limits
        try:
            limits = user.usage_limits
        except:
            limits = None
        
        return {
            'user_id': user.id,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'age': membership.age if membership else None,
            'is_admin': membership.is_admin if membership else False,
            'is_active': membership.is_active if membership else True,
            'total_requests': total_requests,
            'pending_requests': pending_requests,
            'approved_requests': approved_requests,
            'denied_requests': denied_requests,
            'daily_request_count': daily_request_count,
            'weekly_request_count': weekly_request_count,
            'monthly_request_count': monthly_request_count,
            'blocked_content_count': blocked_content_count,
            'approved_content_count': approved_content_count,
            'recent_activities': UserActivitySerializer(recent_activities, many=True).data,
            'limits': UserLimitsSerializer(limits).data if limits else None,
        }


class FamilyMembershipViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing family memberships
    """
    serializer_class = FamilyMembershipSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Only return memberships for families where user is admin"""
        return FamilyMembership.objects.filter(family__admin_user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle membership active status"""
        membership = self.get_object()
        
        # Only family admin can toggle
        if membership.family.admin_user != request.user:
            return Response(
                {'error': 'Only family admin can toggle membership status'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        membership.is_active = not membership.is_active
        membership.save()
        
        # Log activity
        filter_service = UserContentFilterService(membership.user)
        filter_service.log_activity(
            activity_type='account_toggled',
            description=f"Account {'activated' if membership.is_active else 'deactivated'}"
        )
        
        return Response({
            'user_id': membership.user.id,
            'is_active': membership.is_active,
            'message': f"Account {'activated' if membership.is_active else 'deactivated'}"
        })


class UserContentFilterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user content filters
    """
    serializer_class = UserContentFilterSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return filters for family members or own filters"""
        user = self.request.user
        
        # If user is family admin, show all family member filters
        try:
            if user.family_membership.is_admin:
                family_users = user.family_membership.family.get_members()
                return UserContentFilter.objects.filter(user__in=family_users)
        except:
            pass
        
        # Otherwise, show only own filters
        return UserContentFilter.objects.filter(user=user)
    
    def perform_create(self, serializer):
        """Create content filter with current user as blocker"""
        serializer.save(blocked_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_user(self, request):
        """Get filters for specific user"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            target_user = User.objects.get(id=user_id)
            
            # Check if current user can view this user's filters
            if not self._can_view_user_filters(target_user):
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            filters = UserContentFilter.objects.filter(user=target_user)
            serializer = self.get_serializer(filters, many=True)
            return Response(serializer.data)
            
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def _can_view_user_filters(self, target_user):
        """Check if current user can view target user's filters"""
        current_user = self.request.user
        
        # Can always view own filters
        if current_user == target_user:
            return True
        
        # Family admin can view family member filters
        try:
            if current_user.family_membership.is_admin:
                family = current_user.family_membership.family
                return target_user in family.get_members()
        except:
            pass
        
        return False


class UserContentRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing content requests
    """
    serializer_class = UserContentRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return requests for family members or own requests"""
        user = self.request.user
        
        # If user is family admin, show all family member requests
        try:
            if user.family_membership.is_admin:
                family_users = user.family_membership.family.get_members()
                return UserContentRequest.objects.filter(user__in=family_users)
        except:
            pass
        
        # Otherwise, show only own requests
        return UserContentRequest.objects.filter(user=user)
    
    def perform_create(self, serializer):
        """Create content request with current user"""
        request = serializer.save(user=self.request.user)
        
        # Try auto-approval if user is admin
        request.auto_approve_if_admin()
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve content request"""
        content_request = self.get_object()
        
        # Check if user can approve this request
        if not self._can_approve_request(content_request):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserContentRequestApprovalSerializer(
            content_request,
            data={
                'status': 'approved',
                'response_message': request.data.get('response_message', ''),
                'temporary_access': request.data.get('temporary_access', False),
                'access_expires_at': request.data.get('access_expires_at')
            },
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            
            # Create approved content entry
            ApprovedContent.objects.create(
                user=content_request.user,
                movie=content_request.movie,
                tv_show=content_request.tv_show,
                approved_by=request.user,
                approval_reason=serializer.validated_data.get('response_message', ''),
                permanent_access=not serializer.validated_data.get('temporary_access', False),
                expires_at=serializer.validated_data.get('access_expires_at')
            )
            
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def deny(self, request, pk=None):
        """Deny content request"""
        content_request = self.get_object()
        
        # Check if user can deny this request
        if not self._can_approve_request(content_request):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserContentRequestApprovalSerializer(
            content_request,
            data={
                'status': 'denied',
                'response_message': request.data.get('response_message', '')
            },
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending requests for family"""
        user = request.user
        
        # Only family admin can view pending requests
        try:
            if user.family_membership.is_admin:
                family_users = user.family_membership.family.get_members()
                pending_requests = UserContentRequest.objects.filter(
                    user__in=family_users,
                    status='pending'
                )
                serializer = self.get_serializer(pending_requests, many=True)
                return Response(serializer.data)
        except:
            pass
        
        return Response(
            {'error': 'Only family admin can view pending requests'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    def _can_approve_request(self, content_request):
        """Check if current user can approve/deny this request"""
        current_user = self.request.user
        
        # Family admin can approve family member requests
        try:
            if current_user.family_membership.is_admin:
                family = current_user.family_membership.family
                return content_request.user in family.get_members()
        except:
            pass
        
        return False


class UserLimitsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user limits
    """
    serializer_class = UserLimitsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return limits for family members or own limits"""
        user = self.request.user
        
        # If user is family admin, show all family member limits
        try:
            if user.family_membership.is_admin:
                family_users = user.family_membership.family.get_members()
                return UserLimits.objects.filter(user__in=family_users)
        except:
            pass
        
        # Otherwise, show only own limits
        return UserLimits.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def by_user(self, request):
        """Get limits for specific user"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            target_user = User.objects.get(id=user_id)
            
            # Check if current user can view this user's limits
            if not self._can_view_user_limits(target_user):
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            try:
                limits = target_user.usage_limits
                serializer = self.get_serializer(limits)
                return Response(serializer.data)
            except UserLimits.DoesNotExist:
                # Create default limits
                limits = UserLimits.objects.create(user=target_user)
                serializer = self.get_serializer(limits)
                return Response(serializer.data)
                
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def _can_view_user_limits(self, target_user):
        """Check if current user can view target user's limits"""
        current_user = self.request.user
        
        # Can always view own limits
        if current_user == target_user:
            return True
        
        # Family admin can view family member limits
        try:
            if current_user.family_membership.is_admin:
                family = current_user.family_membership.family
                return target_user in family.get_members()
        except:
            pass
        
        return False


class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing user activity
    """
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return activities for family members or own activities"""
        user = self.request.user
        
        # If user is family admin, show all family member activities
        try:
            if user.family_membership.is_admin:
                family_users = user.family_membership.family.get_members()
                return UserActivity.objects.filter(user__in=family_users)
        except:
            pass
        
        # Otherwise, show only own activities
        return UserActivity.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def by_user(self, request):
        """Get activities for specific user"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            target_user = User.objects.get(id=user_id)
            
            # Check if current user can view this user's activities
            if not self._can_view_user_activities(target_user):
                return Response(
                    {'error': 'Permission denied'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            activities = UserActivity.objects.filter(user=target_user)
            
            # Optional date filtering
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            if start_date:
                activities = activities.filter(timestamp__gte=start_date)
            if end_date:
                activities = activities.filter(timestamp__lte=end_date)
            
            serializer = self.get_serializer(activities, many=True)
            return Response(serializer.data)
            
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def _can_view_user_activities(self, target_user):
        """Check if current user can view target user's activities"""
        current_user = self.request.user
        
        # Can always view own activities
        if current_user == target_user:
            return True
        
        # Family admin can view family member activities
        try:
            if current_user.family_membership.is_admin:
                family = current_user.family_membership.family
                return target_user in family.get_members()
        except:
            pass
        
        return False


class FamilyInvitationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing family invitations
    """
    serializer_class = FamilyInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Only return invitations for families where user is admin"""
        return FamilyInvitation.objects.filter(family__admin_user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def accept(self, request):
        """Accept a family invitation"""
        serializer = JoinFamilySerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            membership = serializer.save()
            
            # Create default limits for new member
            UserLimits.objects.create(user=request.user)
            
            return Response({
                'message': 'Successfully joined family',
                'family_name': membership.family.name,
                'membership_id': membership.id
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def resend(self, request, pk=None):
        """Resend invitation email"""
        invitation = self.get_object()
        
        if invitation.status != 'pending':
            return Response(
                {'error': 'Only pending invitations can be resent'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Resend invitation email
        
        return Response({'message': 'Invitation resent successfully'})


class FamilyManagementViewSet(viewsets.ViewSet):
    """
    ViewSet for family management operations
    """
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def create_family(self, request):
        """Create a new family group"""
        serializer = CreateFamilySerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            family = serializer.save()
            
            return Response({
                'family_id': family.id,
                'family_name': family.name,
                'message': 'Family created successfully'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_family(self, request):
        """Get current user's family information"""
        try:
            membership = request.user.family_membership
            family = membership.family
            
            return Response({
                'family_id': family.id,
                'family_name': family.name,
                'is_admin': membership.is_admin,
                'member_count': family.members.count(),
                'joined_at': membership.joined_at
            })
        except:
            return Response(
                {'error': 'User is not a member of any family'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get family dashboard for current user"""
        try:
            membership = request.user.family_membership
            family = membership.family
            
            # Only admin can view family dashboard
            if not membership.is_admin:
                return Response(
                    {'error': 'Only family admin can view dashboard'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get dashboard data for all family members
            members = family.get_members()
            dashboard_data = []
            
            for member in members:
                member_data = self._get_member_dashboard_data(member)
                dashboard_data.append(member_data)
            
            return Response(dashboard_data)
            
        except:
            return Response(
                {'error': 'User is not a member of any family'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def _get_member_dashboard_data(self, user):
        """Generate dashboard data for a family member"""
        # This is the same method as in FamilyGroupViewSet
        now = timezone.now()
        
        # Get membership info
        try:
            membership = user.family_membership
        except:
            membership = None
        
        # Calculate date ranges
        daily_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        weekly_start = now - timedelta(days=7)
        monthly_start = now - timedelta(days=30)
        
        # Request statistics
        total_requests = UserContentRequest.objects.filter(user=user).count()
        pending_requests = UserContentRequest.objects.filter(
            user=user, status='pending'
        ).count()
        approved_requests = UserContentRequest.objects.filter(
            user=user, status__in=['approved', 'auto_approved']
        ).count()
        denied_requests = UserContentRequest.objects.filter(
            user=user, status='denied'
        ).count()
        
        # Usage statistics
        daily_request_count = UserContentRequest.objects.filter(
            user=user, created_at__gte=daily_start
        ).count()
        weekly_request_count = UserContentRequest.objects.filter(
            user=user, created_at__gte=weekly_start
        ).count()
        monthly_request_count = UserContentRequest.objects.filter(
            user=user, created_at__gte=monthly_start
        ).count()
        
        # Content statistics
        blocked_content_count = UserContentFilter.objects.filter(
            user=user, is_blocked=True
        ).count()
        approved_content_count = ApprovedContent.objects.filter(
            user=user
        ).count()
        
        # Recent activities
        recent_activities = UserActivity.objects.filter(
            user=user
        ).order_by('-timestamp')[:10]
        
        # User limits
        try:
            limits = user.usage_limits
        except:
            limits = None
        
        return {
            'user_id': user.id,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'age': membership.age if membership else None,
            'is_admin': membership.is_admin if membership else False,
            'is_active': membership.is_active if membership else True,
            'total_requests': total_requests,
            'pending_requests': pending_requests,
            'approved_requests': approved_requests,
            'denied_requests': denied_requests,
            'daily_request_count': daily_request_count,
            'weekly_request_count': weekly_request_count,
            'monthly_request_count': monthly_request_count,
            'blocked_content_count': blocked_content_count,
            'approved_content_count': approved_content_count,
            'recent_activities': UserActivitySerializer(recent_activities, many=True).data,
            'limits': UserLimitsSerializer(limits).data if limits else None,
        }