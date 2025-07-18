"""
Centralized error handling to prevent information disclosure
"""
import logging
from django.http import JsonResponse
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class SecureErrorHandler:
    """Handle errors securely without exposing system information"""
    
    @staticmethod
    def handle_exception(exception, context="Unknown"):
        """
        Log exception details but return generic error message
        """
        # Log the full exception for debugging
        logger.error(f"{context}: {str(exception)}", exc_info=True)
        
        # Return generic error message
        if settings.DEBUG:
            # In debug mode, show more detail for development
            return f"Error in {context}: {str(exception)}"
        else:
            # In production, return generic message
            return "An error occurred while processing your request"
    
    @staticmethod
    def api_error_response(exception, context="API", status_code=500):
        """
        Return secure API error response
        """
        error_message = SecureErrorHandler.handle_exception(exception, context)
        
        return Response({
            'error': error_message,
            'status': 'error'
        }, status=status_code)
    
    @staticmethod
    def json_error_response(exception, context="Request", status_code=500):
        """
        Return secure JSON error response
        """
        error_message = SecureErrorHandler.handle_exception(exception, context)
        
        return JsonResponse({
            'error': error_message,
            'status': 'error'
        }, status=status_code)


def secure_api_exception_handler(exc, context):
    """
    Custom exception handler for DRF that prevents information disclosure
    """
    logger.error(f"API Exception: {str(exc)}", exc_info=True)
    
    if settings.DEBUG:
        # In debug mode, show actual error
        error_message = str(exc)
    else:
        # In production, return generic message
        error_message = "An error occurred while processing your request"
    
    return Response({
        'error': error_message,
        'status': 'error'
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)