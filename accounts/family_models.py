from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from movies.models import Movie
from tv_shows.models import TVShow


class FamilyProfile(models.Model):
    """
    Sub-profile under a parent account for family members
    """
    AGE_RATINGS = [
        ('G', 'General Audiences'),
        ('PG', 'Parental Guidance Suggested'),
        ('PG-13', 'Parents Strongly Cautioned'),
        ('R', 'Restricted'),
        ('NC-17', 'Adults Only'),
    ]
    
    TV_RATINGS = [
        ('TV-Y', 'All Children'),
        ('TV-Y7', 'Children 7+'),
        ('TV-G', 'General Audience'),
        ('TV-PG', 'Parental Guidance'),
        ('TV-14', 'Parents Strongly Cautioned'),
        ('TV-MA', 'Mature Audiences'),
    ]
    
    parent_user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='family_profiles'
    )
    profile_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(99)]
    )
    
    # Content rating limits
    max_movie_rating = models.CharField(
        max_length=10, 
        choices=AGE_RATINGS, 
        default='G'
    )
    max_tv_rating = models.CharField(
        max_length=10, 
        choices=TV_RATINGS, 
        default='TV-Y'
    )
    
    # Profile settings
    is_active = models.BooleanField(default=True)
    avatar_url = models.URLField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['parent_user', 'profile_name']
        ordering = ['profile_name']
    
    def __str__(self):
        return f"{self.parent_user.username} - {self.profile_name} (Age: {self.age})"
    
    def clean(self):
        # Validate max 6 profiles per parent
        if self.pk is None:  # New profile
            existing_count = FamilyProfile.objects.filter(
                parent_user=self.parent_user
            ).count()
            if existing_count >= 6:
                raise ValidationError("Maximum 6 family profiles allowed per parent.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class ContentFilter(models.Model):
    """
    Custom content blocks for specific profiles
    """
    CONTENT_TYPES = [
        ('movie', 'Movie'),
        ('tv_show', 'TV Show'),
    ]
    
    profile = models.ForeignKey(
        FamilyProfile, 
        on_delete=models.CASCADE, 
        related_name='content_filters'
    )
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    
    # Content references
    movie = models.ForeignKey(
        Movie, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    tv_show = models.ForeignKey(
        TVShow, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    
    # Block reason
    reason = models.CharField(max_length=200, blank=True)
    is_blocked = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [
            ['profile', 'movie'],
            ['profile', 'tv_show'],
        ]
    
    def __str__(self):
        content_name = self.movie.title if self.movie else self.tv_show.title
        status = "Blocked" if self.is_blocked else "Allowed"
        return f"{self.profile.profile_name} - {content_name} ({status})"
    
    def clean(self):
        # Ensure only one content type is set
        if self.content_type == 'movie' and not self.movie:
            raise ValidationError("Movie must be specified for movie content type.")
        if self.content_type == 'tv_show' and not self.tv_show:
            raise ValidationError("TV Show must be specified for tv_show content type.")
        if self.movie and self.tv_show:
            raise ValidationError("Only one content type can be specified.")


class ContentRequest(models.Model):
    """
    Requests from child profiles to access blocked content
    """
    REQUEST_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
    ]
    
    profile = models.ForeignKey(
        FamilyProfile, 
        on_delete=models.CASCADE, 
        related_name='content_requests'
    )
    
    # Content references
    movie = models.ForeignKey(
        Movie, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    tv_show = models.ForeignKey(
        TVShow, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    
    # Request details
    request_message = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, 
        choices=REQUEST_STATUS, 
        default='pending'
    )
    
    # Parent response
    parent_response = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    # Approval settings
    temporary_access = models.BooleanField(default=False)
    access_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        content_name = self.movie.title if self.movie else self.tv_show.title
        return f"{self.profile.profile_name} - {content_name} ({self.status})"
    
    @property
    def content_title(self):
        """Helper property to get content title"""
        return self.movie.title if self.movie else self.tv_show.title
    
    @property
    def content_type_display(self):
        """Helper property to get content type"""
        return "Movie" if self.movie else "TV Show"


class ProfileLimits(models.Model):
    """
    Usage limits for child profiles
    """
    LIMIT_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    profile = models.OneToOneField(
        FamilyProfile, 
        on_delete=models.CASCADE, 
        related_name='limits'
    )
    
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
        return f"{self.profile.profile_name} - Limits"


class ProfileActivity(models.Model):
    """
    Track profile activity for parental dashboard
    """
    ACTIVITY_TYPES = [
        ('content_view', 'Content Viewed'),
        ('content_request', 'Content Requested'),
        ('request_denied', 'Request Denied'),
        ('content_blocked', 'Content Blocked'),
        ('limit_exceeded', 'Limit Exceeded'),
    ]
    
    profile = models.ForeignKey(
        FamilyProfile, 
        on_delete=models.CASCADE, 
        related_name='activities'
    )
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    
    # Content references
    movie = models.ForeignKey(
        Movie, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    tv_show = models.ForeignKey(
        TVShow, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    
    # Activity details
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['profile', 'activity_type']),
            models.Index(fields=['profile', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.profile.profile_name} - {self.activity_type} at {self.timestamp}"
    
    @property
    def content_title(self):
        """Helper property to get content title"""
        return self.movie.title if self.movie else (self.tv_show.title if self.tv_show else "")


class ParentApprovedContent(models.Model):
    """
    Content that has been specifically approved by parents for child profiles
    """
    profile = models.ForeignKey(
        FamilyProfile, 
        on_delete=models.CASCADE, 
        related_name='approved_content'
    )
    
    # Content references
    movie = models.ForeignKey(
        Movie, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    tv_show = models.ForeignKey(
        TVShow, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    
    # Approval details
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='approved_content'
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
            ['profile', 'movie'],
            ['profile', 'tv_show'],
        ]
    
    def __str__(self):
        content_name = self.movie.title if self.movie else self.tv_show.title
        return f"{self.profile.profile_name} - {content_name} (Approved)"
    
    @property
    def content_title(self):
        """Helper property to get content title"""
        return self.movie.title if self.movie else self.tv_show.title
    
    @property
    def is_expired(self):
        """Check if temporary access has expired"""
        if self.permanent_access:
            return False
        from django.utils import timezone
        return self.expires_at and timezone.now() > self.expires_at