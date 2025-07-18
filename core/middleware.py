from django.http import HttpResponsePermanentRedirect
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers and handle HTTPS redirects properly
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add HSTS header only if using HTTPS
        if request.is_secure() and not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response


class HTTPSRedirectMiddleware:
    """
    Custom HTTPS redirect middleware that handles development server properly
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip HTTPS redirect for health checks and development
        if (settings.DEBUG or 
            request.path.startswith('/health/') or 
            request.path.startswith('/ready/') or 
            request.path.startswith('/live/')):
            return self.get_response(request)
        
        # Only redirect if SSL is forced and not already secure
        if (not request.is_secure() and 
            getattr(settings, 'FORCE_SSL', False) and 
            not settings.DEBUG):
            return HttpResponsePermanentRedirect(
                'https://' + request.get_host() + request.get_full_path()
            )
        
        return self.get_response(request)


class ErrorLoggingMiddleware:
    """
    Middleware to log HTTPS/HTTP errors for debugging
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            # Log the error with request details
            logger.error(f"Request error: {e}", extra={
                'request_method': request.method,
                'request_path': request.path,
                'request_secure': request.is_secure(),
                'request_host': request.get_host(),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            })
            raise

    def process_exception(self, request, exception):
        """Log exceptions with request context"""
        logger.error(f"Unhandled exception: {exception}", extra={
            'request_method': request.method,
            'request_path': request.path,
            'request_secure': request.is_secure(),
            'request_host': request.get_host(),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        })
        return None