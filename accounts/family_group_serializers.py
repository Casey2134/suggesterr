from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError

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


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model with family context
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    is_family_admin = serializers.SerializerMethodField()
    family_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'full_name', 'is_family_admin', 'family_name', 'last_login'
        ]
        read_only_fields = ['id', 'username', 'last_login']
    
    def get_is_family_admin(self, obj):
        """Check if user is family admin"""
        try:
            return obj.family_membership.is_admin
        except:
            return False
    
    def get_family_name(self, obj):
        """Get family name"""
        try:
            return obj.family_membership.family.name
        except:
            return None


class FamilyGroupSerializer(serializers.ModelSerializer):
    """
    Serializer for family groups
    """
    admin_username = serializers.CharField(source='admin_user.username', read_only=True)
    admin_full_name = serializers.CharField(source='admin_user.get_full_name', read_only=True)
    member_count = serializers.SerializerMethodField()
    pending_requests_count = serializers.SerializerMethodField()
    
    class Meta:
        model = FamilyGroup
        fields = [
            'id', 'name', 'admin_user', 'admin_username', 'admin_full_name',
            'member_count', 'pending_requests_count', 'allow_requests', 
            'auto_approve_admin', 'created_at', 'updated_at'
        ]
        read_only_fields = ['admin_user', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        """Get number of family members"""
        return obj.members.count()
    
    def get_pending_requests_count(self, obj):
        """Get number of pending requests"""
        return obj.get_pending_requests().count()
    
    def create(self, validated_data):
        """Create family group with current user as admin"""
        request = self.context.get('request')
        validated_data['admin_user'] = request.user
        return super().create(validated_data)


class FamilyMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer for family memberships
    """
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    family_name = serializers.CharField(source='family.name', read_only=True)
    is_coppa_protected = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = FamilyMembership
        fields = [
            'id', 'user', 'family', 'username', 'full_name', 'email', 
            'family_name', 'is_admin', 'age', 'max_movie_rating', 
            'max_tv_rating', 'is_active', 'is_coppa_protected', 'joined_at'
        ]
        read_only_fields = ['user', 'family', 'joined_at']
    
    def validate(self, data):
        """Validate membership data"""
        request = self.context.get('request')
        if request and request.user:
            # Only family admin can update memberships
            if self.instance and self.instance.family.admin_user != request.user:
                raise serializers.ValidationError(
                    "Only family admin can update memberships."
                )
        return data


class UserContentFilterSerializer(serializers.ModelSerializer):
    """
    Serializer for user content filters
    """
    movie_title = serializers.CharField(source='movie.title', read_only=True)
    tv_show_title = serializers.CharField(source='tv_show.title', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    blocked_by_username = serializers.CharField(source='blocked_by.username', read_only=True)
    
    class Meta:
        model = UserContentFilter
        fields = [
            'id', 'user', 'content_type', 'movie', 'tv_show',
            'movie_title', 'tv_show_title', 'username', 'blocked_by',
            'blocked_by_username', 'reason', 'is_blocked', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate(self, data):
        """Validate content filter data"""
        content_type = data.get('content_type')
        movie = data.get('movie')
        tv_show = data.get('tv_show')
        
        if content_type == 'movie':
            if not movie:
                raise serializers.ValidationError(
                    "Movie must be specified for movie content type."
                )
            if tv_show:
                raise serializers.ValidationError(
                    "Cannot specify TV show for movie content type."
                )
        
        elif content_type == 'tv_show':
            if not tv_show:
                raise serializers.ValidationError(
                    "TV show must be specified for tv_show content type."
                )
            if movie:
                raise serializers.ValidationError(
                    "Cannot specify movie for tv_show content type."
                )
        
        return data
    
    def create(self, validated_data):
        """Create content filter with current user as blocker"""
        request = self.context.get('request')
        validated_data['blocked_by'] = request.user
        return super().create(validated_data)


class UserContentRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for content requests
    """
    movie_title = serializers.CharField(source='movie.title', read_only=True)
    tv_show_title = serializers.CharField(source='tv_show.title', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    reviewer_username = serializers.CharField(source='reviewed_by.username', read_only=True)
    content_title = serializers.CharField(read_only=True)
    content_type_display = serializers.CharField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = UserContentRequest
        fields = [
            'id', 'user', 'movie', 'tv_show', 'movie_title', 'tv_show_title',
            'username', 'user_full_name', 'request_message', 'status', 
            'response_message', 'reviewed_by', 'reviewer_username', 'reviewed_at',
            'temporary_access', 'access_expires_at', 'content_title', 
            'content_type_display', 'is_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user', 'reviewed_by', 'reviewed_at', 'content_title', 
            'content_type_display', 'is_expired', 'created_at', 'updated_at'
        ]
    
    def validate(self, data):
        """Validate content request"""
        movie = data.get('movie')
        tv_show = data.get('tv_show')
        
        if not movie and not tv_show:
            raise serializers.ValidationError(
                "Either movie or TV show must be specified."
            )
        
        if movie and tv_show:
            raise serializers.ValidationError(
                "Cannot request both movie and TV show in single request."
            )
        
        return data
    
    def create(self, validated_data):
        """Create content request with current user"""
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)


class UserContentRequestApprovalSerializer(serializers.ModelSerializer):
    """
    Serializer for approving/denying content requests
    """
    class Meta:
        model = UserContentRequest
        fields = [
            'id', 'status', 'response_message', 'temporary_access', 'access_expires_at'
        ]
    
    def validate_status(self, value):
        """Validate status change"""
        if value not in ['approved', 'denied']:
            raise serializers.ValidationError(
                "Status must be 'approved' or 'denied'."
            )
        return value
    
    def validate(self, data):
        """Validate approval data"""
        status = data.get('status')
        temporary_access = data.get('temporary_access')
        access_expires_at = data.get('access_expires_at')
        
        if status == 'approved' and temporary_access and not access_expires_at:
            raise serializers.ValidationError(
                "Access expiration date required for temporary access."
            )
        
        if access_expires_at and access_expires_at <= timezone.now():
            raise serializers.ValidationError(
                "Access expiration date must be in the future."
            )
        
        return data
    
    def update(self, instance, validated_data):
        """Update request with approval details"""
        request = self.context.get('request')
        if request and request.user:
            instance.reviewed_by = request.user
            instance.reviewed_at = timezone.now()
        
        return super().update(instance, validated_data)


class UserLimitsSerializer(serializers.ModelSerializer):
    """
    Serializer for user limits
    """
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserLimits
        fields = [
            'id', 'user', 'username', 'daily_request_limit',
            'weekly_request_limit', 'monthly_request_limit',
            'daily_viewing_limit', 'weekly_viewing_limit',
            'bedtime_hour', 'wakeup_hour', 'weekend_extended_hours',
            'weekend_bedtime_hour', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']


class UserActivitySerializer(serializers.ModelSerializer):
    """
    Serializer for user activity
    """
    username = serializers.CharField(source='user.username', read_only=True)
    movie_title = serializers.CharField(source='movie.title', read_only=True)
    tv_show_title = serializers.CharField(source='tv_show.title', read_only=True)
    content_title = serializers.CharField(read_only=True)
    
    class Meta:
        model = UserActivity
        fields = [
            'id', 'user', 'username', 'activity_type',
            'movie', 'tv_show', 'movie_title', 'tv_show_title',
            'content_title', 'description', 'metadata', 'timestamp'
        ]
        read_only_fields = ['user', 'timestamp']


class ApprovedContentSerializer(serializers.ModelSerializer):
    """
    Serializer for approved content
    """
    username = serializers.CharField(source='user.username', read_only=True)
    movie_title = serializers.CharField(source='movie.title', read_only=True)
    tv_show_title = serializers.CharField(source='tv_show.title', read_only=True)
    approver_username = serializers.CharField(source='approved_by.username', read_only=True)
    content_title = serializers.CharField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ApprovedContent
        fields = [
            'id', 'user', 'username', 'movie', 'tv_show',
            'movie_title', 'tv_show_title', 'approved_by', 'approver_username',
            'approval_reason', 'permanent_access', 'expires_at',
            'content_title', 'is_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = ['approved_by', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create approved content with current user as approver"""
        request = self.context.get('request')
        validated_data['approved_by'] = request.user
        return super().create(validated_data)


class FamilyInvitationSerializer(serializers.ModelSerializer):
    """
    Serializer for family invitations
    """
    family_name = serializers.CharField(source='family.name', read_only=True)
    invited_by_username = serializers.CharField(source='invited_by.username', read_only=True)
    invited_by_full_name = serializers.CharField(source='invited_by.get_full_name', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = FamilyInvitation
        fields = [
            'id', 'family', 'family_name', 'email', 'invited_by', 
            'invited_by_username', 'invited_by_full_name', 'message', 
            'status', 'proposed_age', 'proposed_max_movie_rating', 
            'proposed_max_tv_rating', 'token', 'expires_at', 'is_expired',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'invited_by', 'token', 'expires_at', 'is_expired',
            'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        """Create invitation with current user as inviter"""
        request = self.context.get('request')
        validated_data['invited_by'] = request.user
        
        # Generate token and expiration
        import secrets
        from datetime import timedelta
        
        validated_data['token'] = secrets.token_urlsafe(32)
        validated_data['expires_at'] = timezone.now() + timedelta(days=7)
        
        return super().create(validated_data)


class FamilyDashboardSerializer(serializers.Serializer):
    """
    Serializer for family dashboard data
    """
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    full_name = serializers.CharField()
    age = serializers.IntegerField()
    is_admin = serializers.BooleanField()
    is_active = serializers.BooleanField()
    
    # Request statistics
    total_requests = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    approved_requests = serializers.IntegerField()
    denied_requests = serializers.IntegerField()
    
    # Usage statistics
    daily_request_count = serializers.IntegerField()
    weekly_request_count = serializers.IntegerField()
    monthly_request_count = serializers.IntegerField()
    
    # Content statistics
    blocked_content_count = serializers.IntegerField()
    approved_content_count = serializers.IntegerField()
    
    # Recent activity
    recent_activities = UserActivitySerializer(many=True, read_only=True)
    
    # Limits
    limits = UserLimitsSerializer(read_only=True)


class CreateFamilySerializer(serializers.Serializer):
    """
    Serializer for creating a new family group
    """
    family_name = serializers.CharField(max_length=100)
    
    def create(self, validated_data):
        """Create family group with current user as admin"""
        from .family_group_services import FamilyGroupService
        
        request = self.context.get('request')
        return FamilyGroupService.create_family_group(
            admin_user=request.user,
            family_name=validated_data['family_name']
        )


class JoinFamilySerializer(serializers.Serializer):
    """
    Serializer for joining a family via invitation
    """
    token = serializers.CharField(max_length=64)
    
    def validate_token(self, value):
        """Validate invitation token"""
        try:
            invitation = FamilyInvitation.objects.get(token=value, status='pending')
            if invitation.is_expired():
                raise serializers.ValidationError("Invitation has expired.")
            return value
        except FamilyInvitation.DoesNotExist:
            raise serializers.ValidationError("Invalid invitation token.")
    
    def create(self, validated_data):
        """Accept invitation and join family"""
        request = self.context.get('request')
        invitation = FamilyInvitation.objects.get(token=validated_data['token'])
        
        try:
            return invitation.accept(request.user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))