from typing import Union
from .gemini_service import GeminiService
from .openai_service import OpenAIService


class AIServiceFactory:
    """Factory for creating AI service instances based on user preferences"""
    
    @staticmethod
    def get_ai_service(user) -> Union[GeminiService, OpenAIService]:
        """
        Get the appropriate AI service based on user settings
        
        Args:
            user: Django user object
            
        Returns:
            Either GeminiService or OpenAIService instance
        """
        # Default to Gemini if user has no settings
        if not hasattr(user, 'settings'):
            return GeminiService()
        
        user_settings = user.settings
        
        # Check user's AI provider preference
        if user_settings.ai_provider == 'openai':
            # Create OpenAI service instance
            service = OpenAIService()
            
            # Set the API key from user settings if available
            if user_settings.openai_api_key:
                service.api_key = user_settings.openai_api_key
            
            return service
        else:
            # Default to Gemini
            service = GeminiService()
            
            # Set the API key from user settings if available, otherwise use global key
            if user_settings.gemini_api_key:
                service.api_key = user_settings.gemini_api_key
            
            return service
    
    @staticmethod
    def get_service_name(user) -> str:
        """Get the name of the AI service being used"""
        if hasattr(user, 'settings') and user.settings.ai_provider == 'openai':
            return 'OpenAI'
        return 'Google Gemini'