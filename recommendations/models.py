from django.db import models
from django.contrib.auth.models import User
import json


class ChatConversation(models.Model):
    """Store chat conversations for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title or 'Conversation'}"


class ChatMessage(models.Model):
    """Store individual chat messages"""
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=[
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ])
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class UserNegativeFeedback(models.Model):
    """Track movies/shows that users marked as 'Not Interested'"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tmdb_id = models.IntegerField()
    content_type = models.CharField(max_length=10, choices=[
        ('movie', 'Movie'),
        ('tv', 'TV Show'),
    ])
    reason = models.CharField(max_length=50, choices=[
        ('not_interested', 'Not Interested'),
        ('already_seen', 'Already Seen'),
        ('not_my_genre', 'Not My Genre'),
        ('poor_rating', 'Poor Rating'),
    ], default='not_interested')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'tmdb_id', 'content_type']
        indexes = [
            models.Index(fields=['user', 'content_type']),
            models.Index(fields=['tmdb_id', 'content_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - Not Interested in {self.content_type} {self.tmdb_id}"


class UserProfile(models.Model):
    """Store user personality quiz results and preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='personality_profile')
    
    # Personality traits stored as JSON
    personality_traits = models.JSONField(default=dict, blank=True)
    
    # Quiz completion tracking
    quiz_completed = models.BooleanField(default=False)
    quiz_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Preference categories
    preferred_genres = models.JSONField(default=list, blank=True)
    preferred_decades = models.JSONField(default=list, blank=True)
    content_preferences = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - Profile"
    
    def get_personality_summary(self):
        """Get a text summary of personality traits for AI prompts"""
        if not self.personality_traits:
            return ""
        
        summary_parts = []
        for trait, value in self.personality_traits.items():
            if value:
                summary_parts.append(f"{trait}: {value}")
        
        return "; ".join(summary_parts)
    
    def get_genre_preferences(self):
        """Get formatted genre preferences for AI prompts"""
        if not self.preferred_genres:
            return ""
        return ", ".join(self.preferred_genres)


class PersonalityQuiz(models.Model):
    """Store quiz questions and answer options"""
    QUESTION_TYPES = [
        ('single_choice', 'Single Choice'),
        ('multiple_choice', 'Multiple Choice'),
        ('scale', 'Scale (1-5)'),
        ('text', 'Text Response'),
    ]
    
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    answer_options = models.JSONField(default=list, blank=True)
    
    # Categorization
    category = models.CharField(max_length=50, default='general')
    trait_mapping = models.JSONField(default=dict, blank=True)
    
    # Ordering and status
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}..."
