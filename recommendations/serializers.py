from rest_framework import serializers
from .models import UserNegativeFeedback, ChatConversation, ChatMessage, UserProfile, PersonalityQuiz


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'timestamp']
        read_only_fields = ['timestamp']


class ChatConversationSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatConversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'messages', 'message_count']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_message_count(self, obj):
        return obj.messages.count()


class UserNegativeFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNegativeFeedback
        fields = ['id', 'tmdb_id', 'content_type', 'reason', 'created_at']
        read_only_fields = ['created_at']


class PersonalityQuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalityQuiz
        fields = ['id', 'question_text', 'question_type', 'answer_options', 'category', 'order']


class UserProfileSerializer(serializers.ModelSerializer):
    personality_summary = serializers.CharField(source='get_personality_summary', read_only=True)
    genre_preferences = serializers.CharField(source='get_genre_preferences', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'personality_traits', 'quiz_completed', 'quiz_completed_at',
            'preferred_genres', 'preferred_decades', 'content_preferences',
            'personality_summary', 'genre_preferences', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class QuizSubmissionSerializer(serializers.Serializer):
    """Serializer for quiz submission data"""
    answers = serializers.JSONField()
    
    def validate_answers(self, value):
        """Validate that answers is a dict with question IDs as keys"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Answers must be a dictionary")
        
        for question_id, answer in value.items():
            if not str(question_id).isdigit():
                raise serializers.ValidationError("Question IDs must be numeric")
        
        return value