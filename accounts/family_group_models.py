from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from movies.models import Movie
from tv_shows.models import TVShow


class FamilyGroup(models.Model):
    """
    A family group that contains multiple user accounts
    """
    name = models.CharField(max_length=100)
    admin_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='administered_families'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Family settings
    allow_requests = models.BooleanField(default=True)
    auto_approve_admin = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} (Admin: {self.admin_user.username})"
    
    def get_members(self):
        """Get all family members"""
        return User.objects.filter(family_membership__family=self)
    
    def get_children(self):
        """Get all child members (non-admin)"""
        return User.objects.filter(
            family_membership__family=self,
            family_membership__is_admin=False
        )
    
    def get_pending_requests(self):
        """Get all pending content requests for this family"""
        return UserContentRequest.objects.filter(
            user__family_membership__family=self,
            status='pending'
        )


class FamilyMembership(models.Model):
    """
    Links a User to a FamilyGroup with specific settings
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='family_membership')
    family = models.ForeignKey(FamilyGroup, on_delete=models.CASCADE, related_name='members')
    
    # Member settings
    is_admin = models.BooleanField(default=False)
    age = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(99)]
    )
    
    # Content rating limits
    max_movie_rating = models.CharField(
        max_length=10, 
        choices=[
            ('G', 'General Audiences'),
            ('PG', 'Parental Guidance Suggested'),
            ('PG-13', 'Parents Strongly Cautioned'),
            ('R', 'Restricted'),
            ('NC-17', 'Adults Only'),
        ],
        default='G'
    )
    max_tv_rating = models.CharField(
        max_length=10, 
        choices=[
            ('TV-Y', 'All Children'),
            ('TV-Y7', 'Children 7+'),
            ('TV-G', 'General Audience'),
            ('TV-PG', 'Parental Guidance'),
            ('TV-14', 'Parents Strongly Cautioned'),
            ('TV-MA', 'Mature Audiences'),
        ],
        default='TV-Y'
    )
    
    # Account settings
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'family']
        ordering = ['user__first_name', 'user__username']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} in {self.family.name}"
    
    def clean(self):
        # Ensure admin user is the same as the family admin
        if self.is_admin and self.user != self.family.admin_user:
            raise ValidationError("Only the family admin can be marked as admin.")
        
        # Ensure family admin is always admin
        if self.user == self.family.admin_user and not self.is_admin:
            raise ValidationError("Family admin must be marked as admin.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def can_auto_approve(self):
        """Check if this member can auto-approve requests"""
        return self.is_admin and self.family.auto_approve_admin
    
    def is_coppa_protected(self):
        """Check if this member is COPPA protected"""
        return self.age < 13


class UserContentFilter(models.Model):
    """
    Custom content blocks for specific users
    """
    CONTENT_TYPES = [
        ('movie', 'Movie'),
        ('tv_show', 'TV Show'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='content_filters')
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    
    # Content references
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, blank=True)
    tv_show = models.ForeignKey(TVShow, on_delete=models.CASCADE, null=True, blank=True)
    
    # Block details
    reason = models.CharField(max_length=200, blank=True)
    is_blocked = models.BooleanField(default=True)
    blocked_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='blocked_content',
        help_text="User who blocked this content"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [
            ['user', 'movie'],
            ['user', 'tv_show'],
        ]
    
    def __str__(self):
        content_name = self.movie.title if self.movie else self.tv_show.title
        status = "Blocked" if self.is_blocked else "Allowed"
        return f"{self.user.username} - {content_name} ({status})"
    
    def clean(self):
        # Ensure only one content type is set
        if self.content_type == 'movie' and not self.movie:
            raise ValidationError("Movie must be specified for movie content type.")
        if self.content_type == 'tv_show' and not self.tv_show:
            raise ValidationError("TV Show must be specified for tv_show content type.")
        if self.movie and self.tv_show:
            raise ValidationError("Only one content type can be specified.")


class UserContentRequest(models.Model):
    """
    Requests from family members to access blocked content
    """
    REQUEST_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
        ('auto_approved', 'Auto-Approved'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_content_requests')
    
    # Content references
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, blank=True)
    tv_show = models.ForeignKey(TVShow, on_delete=models.CASCADE, null=True, blank=True)
    
    # Request details
    request_message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='pending')
    
    # Response details
    response_message = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='user_reviewed_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Access settings
    temporary_access = models.BooleanField(default=False)
    access_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        content_name = self.movie.title if self.movie else self.tv_show.title
        return f"{self.user.username} - {content_name} ({self.status})"
    
    @property
    def content_title(self):
        """Helper property to get content title"""
        return self.movie.title if self.movie else self.tv_show.title
    
    @property
    def content_type_display(self):
        """Helper property to get content type"""
        return "Movie" if self.movie else "TV Show"
    
    @property
    def is_expired(self):
        """Check if temporary access has expired"""
        if not self.temporary_access:
            return False
        return self.access_expires_at and timezone.now() > self.access_expires_at
    
    def auto_approve_if_admin(self):
        """Auto-approve request if user is admin with auto-approval enabled"""
        try:
            membership = self.user.family_membership
            if membership.can_auto_approve():
                self.status = 'auto_approved'
                self.reviewed_by = self.user
                self.reviewed_at = timezone.now()
                self.response_message = "Auto-approved (Admin account)"
                self.save()
                return True
        except:
            pass
        return False


class UserLimits(models.Model):
    """
    Usage limits for users
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='usage_limits')
    
    # Request limits
    daily_request_limit = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    weekly_request_limit = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(500)]
    )
    monthly_request_limit = models.PositiveIntegerField(
        default=200,
        validators=[MinValueValidator(1), MaxValueValidator(1000)]
    )
    
    # Viewing time limits (in minutes)
    daily_viewing_limit = models.PositiveIntegerField(
        default=120,  # 2 hours
        help_text="Daily viewing limit in minutes"
    )
    weekly_viewing_limit = models.PositiveIntegerField(
        default=840,  # 14 hours
        help_text="Weekly viewing limit in minutes"
    )
    
    # Time restrictions
    bedtime_hour = models.PositiveIntegerField(
        default=21,  # 9 PM
        validators=[MinValueValidator(0), MaxValueValidator(23)],
        help_text="Hour when content access is restricted (24-hour format)"
    )
    wakeup_hour = models.PositiveIntegerField(
        default=7,  # 7 AM
        validators=[MinValueValidator(0), MaxValueValidator(23)],
        help_text="Hour when content access is allowed (24-hour format)"
    )
    
    # Weekend settings
    weekend_extended_hours = models.BooleanField(
        default=True,
        help_text="Allow extended hours on weekends"
    )
    weekend_bedtime_hour = models.PositiveIntegerField(
        default=23,  # 11 PM
        validators=[MinValueValidator(0), MaxValueValidator(23)]
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - Usage Limits"


class UserActivity(models.Model):
    """
    Track user activity for family monitoring
    """
    ACTIVITY_TYPES = [
        ('content_view', 'Content Viewed'),
        ('content_request', 'Content Requested'),
        ('request_approved', 'Request Approved'),
        ('request_denied', 'Request Denied'),
        ('content_blocked', 'Content Blocked'),
        ('limit_exceeded', 'Limit Exceeded'),
        ('login', 'User Login'),
        ('logout', 'User Logout'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    
    # Content references
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, blank=True)
    tv_show = models.ForeignKey(TVShow, on_delete=models.CASCADE, null=True, blank=True)
    
    # Activity details
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['user', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_type} at {self.timestamp}"
    
    @property
    def content_title(self):
        """Helper property to get content title"""
        return self.movie.title if self.movie else (self.tv_show.title if self.tv_show else "")


class ApprovedContent(models.Model):
    """
    Content that has been specifically approved for users
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_approved_content')
    
    # Content references
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, blank=True)
    tv_show = models.ForeignKey(TVShow, on_delete=models.CASCADE, null=True, blank=True)
    
    # Approval details
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='user_content_approvals'
    )
    approval_reason = models.TextField(blank=True)
    
    # Access settings
    permanent_access = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [
            ['user', 'movie'],
            ['user', 'tv_show'],
        ]
    
    def __str__(self):
        content_name = self.movie.title if self.movie else self.tv_show.title
        return f"{self.user.username} - {content_name} (Approved)"
    
    @property
    def content_title(self):
        """Helper property to get content title"""
        return self.movie.title if self.movie else self.tv_show.title
    
    @property
    def is_expired(self):
        """Check if temporary access has expired"""
        if self.permanent_access:
            return False
        return self.expires_at and timezone.now() > self.expires_at


class FamilyInvitation(models.Model):
    """
    Invitations to join a family group
    """
    INVITATION_STATUS = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    
    family = models.ForeignKey(FamilyGroup, on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    invited_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_invitations'
    )
    
    # Invitation details
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=INVITATION_STATUS, default='pending')
    
    # Pre-set member settings
    proposed_age = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(99)]
    )
    proposed_max_movie_rating = models.CharField(max_length=10, default='G')
    proposed_max_tv_rating = models.CharField(max_length=10, default='TV-Y')
    
    # Token for secure invitation
    token = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Invitation to {self.email} for {self.family.name}"
    
    def is_expired(self):
        """Check if invitation has expired"""
        return timezone.now() > self.expires_at
    
    def accept(self, user):
        """Accept the invitation and create family membership"""
        if self.is_expired():
            raise ValidationError("Invitation has expired.")
        
        if self.status != 'pending':
            raise ValidationError("Invitation is not pending.")
        
        # Create family membership
        membership = FamilyMembership.objects.create(
            user=user,
            family=self.family,
            age=self.proposed_age,
            max_movie_rating=self.proposed_max_movie_rating,
            max_tv_rating=self.proposed_max_tv_rating
        )
        
        # Update invitation status
        self.status = 'accepted'
        self.save()
        
        return membership