from typing import List, Dict, Optional
import re
from movies.gemini_service import GeminiService
from movies.tmdb_service import TMDBService
from movies.tmdb_tv_service import TMDBTVService
from .models import ChatConversation, ChatMessage, UserProfile


class ChatService:
    """Service for handling conversational movie recommendations"""
    
    def __init__(self):
        self.gemini_service = GeminiService()
        self.tmdb_service = TMDBService()
        self.tmdb_tv_service = TMDBTVService()
    
    def generate_response(self, user_message: str, conversation: ChatConversation) -> str:
        """Generate AI response for user message using conversation context"""
        
        # Get conversation history
        messages = conversation.messages.order_by('timestamp')
        
        # Build context from conversation history
        context = self._build_conversation_context(messages)
        
        # Get user's library context if available
        library_context = self._get_user_library_context(conversation.user)
        
        # Get user's negative feedback context
        negative_feedback = self._get_user_negative_feedback(conversation.user)
        
        # Get user's personality profile
        personality_profile = self._get_user_personality_profile(conversation.user)
        
        # Create comprehensive prompt for conversational recommendations
        prompt = self._create_conversational_prompt(
            user_message, 
            context, 
            library_context, 
            negative_feedback,
            personality_profile
        )
        
        # Get AI response
        response = self.gemini_service._make_request(prompt)
        
        if not response:
            return "I'm sorry, I'm having trouble generating a response right now. Please try again."
        
        return response
    
    def _build_conversation_context(self, messages) -> str:
        """Build conversation context from message history"""
        context = ""
        # Get last 10 messages for context
        recent_messages = list(messages)[-10:]
        for message in recent_messages:
            role = "Human" if message.role == "user" else "Assistant"
            context += f"{role}: {message.content}\n"
        return context
    
    def _get_user_library_context(self, user) -> Optional[List[Dict]]:
        """Get user's library context - simplified for now"""
        # For now, return None - can be enhanced later with Jellyfin integration
        return None
    
    def _get_user_negative_feedback(self, user) -> List[int]:
        """Get user's negative feedback TMDb IDs"""
        from .models import UserNegativeFeedback
        return list(
            UserNegativeFeedback.objects.filter(user=user, content_type='movie')
            .values_list('tmdb_id', flat=True)[:50]
        )
    
    def _get_user_personality_profile(self, user) -> Optional[Dict]:
        """Get user's personality profile data"""
        try:
            profile = UserProfile.objects.get(user=user)
            if profile.quiz_completed:
                return {
                    'personality_summary': profile.get_personality_summary(),
                    'genre_preferences': profile.get_genre_preferences(),
                    'preferred_decades': profile.preferred_decades,
                    'content_preferences': profile.content_preferences,
                    'personality_traits': profile.personality_traits
                }
        except UserProfile.DoesNotExist:
            pass
        return None
    
    def _create_conversational_prompt(
        self, 
        user_message: str, 
        context: str, 
        library_context: Optional[List[Dict]], 
        negative_feedback: List[int],
        personality_profile: Optional[Dict]
    ) -> str:
        """Create conversational prompt for Gemini API"""
        
        # Build library context string
        library_context_str = ""
        if library_context:
            library_titles = [f"'{movie.get('title', 'Unknown')} ({movie.get('year', 'N/A')})'" 
                            for movie in library_context]
            library_context_str = f"\n\nUSER'S LIBRARY: The user has access to these movies: {', '.join(library_titles[:30])}. Consider this when making recommendations - you can mention movies they already have or suggest complementary titles."
        
        # Build negative feedback context
        negative_feedback_str = ""
        if negative_feedback:
            negative_feedback_str = f"\n\nUSER DISLIKES: The user has marked these TMDB movie IDs as 'Not Interested': {', '.join(map(str, negative_feedback))}. Avoid recommending these movies."
        
        # Build personality profile context
        personality_context_str = ""
        if personality_profile:
            personality_summary = personality_profile.get('personality_summary', '')
            genre_preferences = personality_profile.get('genre_preferences', '')
            preferred_decades = personality_profile.get('preferred_decades', [])
            content_preferences = personality_profile.get('content_preferences', {})
            
            if personality_summary:
                personality_context_str += f"\n\nUSER'S PERSONALITY PROFILE: {personality_summary}"
            
            if genre_preferences:
                personality_context_str += f"\n\nUSER'S PREFERRED GENRES: {genre_preferences}"
            
            if preferred_decades:
                decades_str = ", ".join(preferred_decades)
                personality_context_str += f"\n\nUSER'S PREFERRED TIME PERIODS: {decades_str}"
            
            if content_preferences:
                prefs_list = []
                for key, value in content_preferences.items():
                    if value:
                        prefs_list.append(f"{key}: {value}")
                if prefs_list:
                    personality_context_str += f"\n\nUSER'S CONTENT PREFERENCES: {'; '.join(prefs_list)}"
        
        # Conversation context
        context_str = f"\n\nCONVERSATION HISTORY:\n{context}" if context else ""
        
        prompt = f"""You are an AI movie and TV show recommendation assistant. You help users discover great movies and TV shows based on their preferences, mood, and interests. Be conversational, helpful, and enthusiastic about movies and TV shows.

USER'S CURRENT MESSAGE: {user_message}
{context_str}
{library_context_str}
{negative_feedback_str}
{personality_context_str}

INSTRUCTIONS:
1. Respond in a conversational, friendly tone
2. If the user asks for recommendations, provide 3-5 specific movie or TV show titles with brief explanations
3. When recommending movies or TV shows, format titles clearly with quotes like "The Matrix" or "Breaking Bad"
4. Consider their conversation history and preferences
5. If they have a library, mention relevant movies or TV shows they already own when appropriate
6. Use their personality profile to tailor recommendations - consider their preferred genres, decades, and personality traits
7. Ask follow-up questions to better understand their preferences
8. If they ask about a specific movie or TV show, provide helpful information
9. Keep responses concise but engaging (2-3 paragraphs max)
10. You can recommend both movies and TV shows based on user preferences
11. Always put movie and TV show titles in quotes to make them easy to identify
12. If the user has completed a personality quiz, use that information to provide more personalized recommendations

Respond naturally as if you're having a conversation with a movie-loving friend."""
        
        return prompt
    
    def get_or_create_conversation(self, user) -> ChatConversation:
        """Get the user's current conversation or create a new one"""
        conversation = ChatConversation.objects.filter(user=user).first()
        
        if not conversation:
            conversation = ChatConversation.objects.create(
                user=user,
                title="Movie Chat"
            )
        
        return conversation
    
    def save_message(self, conversation: ChatConversation, role: str, content: str) -> ChatMessage:
        """Save a message to the conversation"""
        return ChatMessage.objects.create(
            conversation=conversation,
            role=role,
            content=content
        )
    
    def clear_conversation(self, user):
        """Clear user's conversation history"""
        ChatConversation.objects.filter(user=user).delete()
    
    def extract_movie_recommendations(self, ai_response: str) -> List[Dict]:
        """Extract movie titles from AI response and fetch their details"""
        movies = []
        
        # Pattern to match movie titles (looking for quoted titles or common patterns)
        patterns = [
            r'"([^"]+)"',  # Quoted titles
            r'\*([^*]+)\*',  # Titles in asterisks
            r'(?:^|\n)(?:\d+\.?\s*)?([A-Z][^.!?]*(?:\([0-9]{4}\))?)',  # Numbered lists or capitalized titles
        ]
        
        potential_titles = set()
        
        for pattern in patterns:
            matches = re.finditer(pattern, ai_response, re.MULTILINE)
            for match in matches:
                title = match.group(1).strip()
                # Filter out common non-movie phrases
                if (len(title) > 3 and 
                    not title.lower().startswith(('here', 'what', 'if you', 'some', 'these', 'great', 'perfect', 'based on')) and
                    not title.endswith('?') and
                    title not in potential_titles):
                    potential_titles.add(title)
        
        # Search for each potential title
        for title in list(potential_titles)[:5]:  # Limit to 5 searches
            movie_results = self.tmdb_service.search_movies(title)
            if movie_results['results']:
                # Get the first result (most relevant)
                movie = movie_results['results'][0]
                movies.append({
                    'title': movie['title'],
                    'tmdb_id': movie['tmdb_id'],
                    'poster_path': movie['poster_path'],
                    'overview': movie['overview'],
                    'release_date': movie['release_date'],
                    'vote_average': movie['vote_average'],
                    'original_query': title
                })
        
        return movies
    
    def get_movie_by_title(self, title: str) -> Optional[Dict]:
        """Get movie details by title"""
        results = self.tmdb_service.search_movies(title)
        if results['results']:
            return results['results'][0]
        return None
    
    def extract_tv_show_recommendations(self, ai_response: str) -> List[Dict]:
        """Extract TV show titles from AI response and fetch their details"""
        tv_shows = []
        
        # Pattern to match TV show titles (similar to movies but also looking for TV-specific terms)
        patterns = [
            r'"([^"]+)"',  # Quoted titles
            r'\*([^*]+)\*',  # Titles in asterisks
            r'(?:^|\n)(?:\d+\.?\s*)?([A-Z][^.!?]*(?:\([0-9]{4}\))?)',  # Numbered lists or capitalized titles
        ]
        
        potential_titles = set()
        
        for pattern in patterns:
            matches = re.finditer(pattern, ai_response, re.MULTILINE)
            for match in matches:
                title = match.group(1).strip()
                # Filter out common non-TV show phrases
                if (len(title) > 3 and 
                    not title.lower().startswith(('here', 'what', 'if you', 'some', 'these', 'great', 'perfect', 'based on')) and
                    not title.endswith('?') and
                    title not in potential_titles):
                    potential_titles.add(title)
        
        # Search for each potential title
        for title in list(potential_titles)[:5]:  # Limit to 5 searches
            tv_results = self.tmdb_tv_service.search_tv_shows(title)
            if tv_results:
                # Get the first result (most relevant)
                tv_show = tv_results[0]
                tv_shows.append({
                    'title': tv_show['title'],
                    'tmdb_id': tv_show['tmdb_id'],
                    'poster_path': tv_show['poster_path'],
                    'overview': tv_show['overview'],
                    'first_air_date': tv_show['first_air_date'],
                    'vote_average': tv_show['vote_average'],
                    'number_of_seasons': tv_show['number_of_seasons'],
                    'original_query': title
                })
        
        return tv_shows
    
    def get_tv_show_by_title(self, title: str) -> Optional[Dict]:
        """Get TV show details by title"""
        results = self.tmdb_tv_service.search_tv_shows(title)
        if results:
            return results[0]
        return None