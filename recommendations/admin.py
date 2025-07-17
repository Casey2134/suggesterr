from django.contrib import admin
from .models import ChatConversation, ChatMessage, UserNegativeFeedback, UserProfile, PersonalityQuiz


@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'role', 'content_preview', 'timestamp']
    list_filter = ['role', 'timestamp']
    search_fields = ['conversation__user__username', 'content']
    readonly_fields = ['timestamp']
    
    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'


@admin.register(UserNegativeFeedback)
class UserNegativeFeedbackAdmin(admin.ModelAdmin):
    list_display = ['user', 'tmdb_id', 'content_type', 'reason', 'created_at']
    list_filter = ['content_type', 'reason', 'created_at']
    search_fields = ['user__username', 'tmdb_id']
    readonly_fields = ['created_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz_completed', 'quiz_completed_at', 'created_at']
    list_filter = ['quiz_completed', 'quiz_completed_at', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'quiz_completed', 'quiz_completed_at')
        }),
        ('Personality Data', {
            'fields': ('personality_traits', 'preferred_genres', 'preferred_decades', 'content_preferences'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PersonalityQuiz)
class PersonalityQuizAdmin(admin.ModelAdmin):
    list_display = ['question_text_preview', 'question_type', 'category', 'order', 'is_active']
    list_filter = ['question_type', 'category', 'is_active', 'created_at']
    search_fields = ['question_text', 'category']
    list_editable = ['order', 'is_active']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Question Details', {
            'fields': ('question_text', 'question_type', 'answer_options')
        }),
        ('Categorization', {
            'fields': ('category', 'trait_mapping')
        }),
        ('Settings', {
            'fields': ('order', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def question_text_preview(self, obj):
        return obj.question_text[:100] + "..." if len(obj.question_text) > 100 else obj.question_text
    question_text_preview.short_description = 'Question Text'
