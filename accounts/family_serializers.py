from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from .family_models import (
    FamilyProfile,
    ContentFilter,
    ContentRequest,
    ProfileLimits,
    ProfileActivity,
    ParentApprovedContent,
)
from movies.models import Movie
from tv_shows.models import TVShow


class FamilyProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for family profiles with user ownership validation
    """
    parent_username = serializers.CharField(source='parent_user.username', read_only=True)
    profile_count = serializers.SerializerMethodField()
    
    class Meta:
        model = FamilyProfile
        fields = [
            'id', 'profile_name', 'age', 'max_movie_rating', 'max_tv_rating',
            'is_active', 'avatar_url', 'parent_user', 'parent_username',
            'profile_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['parent_user', 'created_at', 'updated_at']
    
    def get_profile_count(self, obj):
        """Get total number of profiles for this parent"""
        return FamilyProfile.objects.filter(parent_user=obj.parent_user).count()
    
    def validate(self, data):
        """Validate profile creation limits"""
        request = self.context.get('request')
        if request and request.user:
            # Check if creating new profile (no instance) or updating existing
            if not self.instance:
                existing_count = FamilyProfile.objects.filter(
                    parent_user=request.user
                ).count()
                if existing_count >= 6:
                    raise serializers.ValidationError(
                        "Maximum 6 family profiles allowed per parent."
                    )
        return data
    
    def create(self, validated_data):
        """Create profile with parent_user set to current user"""
        request = self.context.get('request')
        validated_data['parent_user'] = request.user
        return super().create(validated_data)


class ContentFilterSerializer(serializers.ModelSerializer):
    """
    Serializer for content filtering with content validation
    """
    movie_title = serializers.CharField(source='movie.title', read_only=True)
    tv_show_title = serializers.CharField(source='tv_show.title', read_only=True)
    profile_name = serializers.CharField(source='profile.profile_name', read_only=True)
    
    class Meta:
        model = ContentFilter
        fields = [
            'id', 'profile', 'content_type', 'movie', 'tv_show',
            'movie_title', 'tv_show_title', 'profile_name',
            'reason', 'is_blocked', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate(self, data):
        """Validate content type and references"""
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
        
        # Validate profile ownership
        request = self.context.get('request')
        if request and request.user:
            profile = data.get('profile')
            if profile and profile.parent_user != request.user:
                raise serializers.ValidationError(
                    "You can only create filters for your own profiles."
                )
        
        return data


class ContentRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for content requests with approval workflow
    """
    movie_title = serializers.CharField(source='movie.title', read_only=True)
    tv_show_title = serializers.CharField(source='tv_show.title', read_only=True)
    profile_name = serializers.CharField(source='profile.profile_name', read_only=True)
    reviewer_username = serializers.CharField(source='reviewed_by.username', read_only=True)
    content_title = serializers.CharField(read_only=True)
    content_type_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = ContentRequest
        fields = [
            'id', 'profile', 'movie', 'tv_show', 'movie_title', 'tv_show_title',
            'profile_name', 'request_message', 'status', 'parent_response',
            'reviewed_by', 'reviewer_username', 'reviewed_at', 'temporary_access',
            'access_expires_at', 'content_title', 'content_type_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'reviewed_by', 'reviewed_at', 'content_title', 'content_type_display',
            'created_at', 'updated_at'
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
        
        # Validate profile ownership for creation
        request = self.context.get('request')
        if request and request.user:
            profile = data.get('profile')
            if profile and profile.parent_user != request.user:
                raise serializers.ValidationError(
                    "You can only create requests for your own profiles."
                )
        
        return data


class ContentRequestApprovalSerializer(serializers.ModelSerializer):
    """
    Serializer for parent approval of content requests
    """
    class Meta:
        model = ContentRequest
        fields = [
            'id', 'status', 'parent_response', 'temporary_access', 'access_expires_at'
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


class ProfileLimitsSerializer(serializers.ModelSerializer):
    """
    Serializer for profile usage limits
    """
    profile_name = serializers.CharField(source='profile.profile_name', read_only=True)
    
    class Meta:
        model = ProfileLimits
        fields = [
            'id', 'profile', 'profile_name', 'daily_request_limit',
            'weekly_request_limit', 'monthly_request_limit',
            'daily_viewing_limit', 'weekly_viewing_limit',
            'bedtime_hour', 'wakeup_hour', 'weekend_extended_hours',
            'weekend_bedtime_hour', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def validate(self, data):
        """Validate time restrictions"""
        bedtime_hour = data.get('bedtime_hour')
        wakeup_hour = data.get('wakeup_hour')
        weekend_bedtime_hour = data.get('weekend_bedtime_hour')
        
        if bedtime_hour is not None and wakeup_hour is not None:
            if bedtime_hour == wakeup_hour:
                raise serializers.ValidationError(
                    "Bedtime and wakeup hours cannot be the same."
                )
        
        if weekend_bedtime_hour is not None and wakeup_hour is not None:
            if weekend_bedtime_hour == wakeup_hour:
                raise serializers.ValidationError(
                    "Weekend bedtime and wakeup hours cannot be the same."
                )
        
        # Validate profile ownership
        request = self.context.get('request')
        if request and request.user:
            profile = data.get('profile')
            if profile and profile.parent_user != request.user:
                raise serializers.ValidationError(
                    "You can only set limits for your own profiles."
                )
        
        return data


class ProfileActivitySerializer(serializers.ModelSerializer):
    """
    Serializer for profile activity tracking
    """
    profile_name = serializers.CharField(source='profile.profile_name', read_only=True)
    movie_title = serializers.CharField(source='movie.title', read_only=True)
    tv_show_title = serializers.CharField(source='tv_show.title', read_only=True)
    content_title = serializers.CharField(read_only=True)
    
    class Meta:
        model = ProfileActivity
        fields = [
            'id', 'profile', 'profile_name', 'activity_type',
            'movie', 'tv_show', 'movie_title', 'tv_show_title',
            'content_title', 'description', 'metadata', 'timestamp'
        ]
        read_only_fields = ['timestamp']


class ParentApprovedContentSerializer(serializers.ModelSerializer):
    """
    Serializer for parent-approved content
    """
    profile_name = serializers.CharField(source='profile.profile_name', read_only=True)
    movie_title = serializers.CharField(source='movie.title', read_only=True)
    tv_show_title = serializers.CharField(source='tv_show.title', read_only=True)
    approver_username = serializers.CharField(source='approved_by.username', read_only=True)
    content_title = serializers.CharField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ParentApprovedContent
        fields = [
            'id', 'profile', 'profile_name', 'movie', 'tv_show',
            'movie_title', 'tv_show_title', 'approved_by', 'approver_username',
            'approval_reason', 'permanent_access', 'expires_at',
            'content_title', 'is_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = ['approved_by', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate approved content"""
        movie = data.get('movie')
        tv_show = data.get('tv_show')
        
        if not movie and not tv_show:
            raise serializers.ValidationError(
                "Either movie or TV show must be specified."
            )
        
        if movie and tv_show:
            raise serializers.ValidationError(
                "Cannot approve both movie and TV show in single entry."
            )
        
        permanent_access = data.get('permanent_access')
        expires_at = data.get('expires_at')
        
        if not permanent_access and not expires_at:
            raise serializers.ValidationError(
                "Expiration date required for temporary access."
            )
        
        if expires_at and expires_at <= timezone.now():
            raise serializers.ValidationError(
                "Expiration date must be in the future."
            )
        
        # Validate profile ownership
        request = self.context.get('request')
        if request and request.user:
            profile = data.get('profile')
            if profile and profile.parent_user != request.user:
                raise serializers.ValidationError(
                    "You can only approve content for your own profiles."
                )
        
        return data
    
    def create(self, validated_data):
        """Create approved content with current user as approver"""
        request = self.context.get('request')
        validated_data['approved_by'] = request.user
        return super().create(validated_data)


class ParentalDashboardSerializer(serializers.Serializer):
    """
    Serializer for parental dashboard overview data
    """
    profile_id = serializers.IntegerField()
    profile_name = serializers.CharField()
    age = serializers.IntegerField()
    is_active = serializers.BooleanField()
    
    # Activity statistics
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
    recent_activities = ProfileActivitySerializer(many=True, read_only=True)
    
    # Limits status
    limits = ProfileLimitsSerializer(read_only=True)
    
    class Meta:
        fields = [
            'profile_id', 'profile_name', 'age', 'is_active',
            'total_requests', 'pending_requests', 'approved_requests', 'denied_requests',
            'daily_request_count', 'weekly_request_count', 'monthly_request_count',
            'blocked_content_count', 'approved_content_count',
            'recent_activities', 'limits'
        ]