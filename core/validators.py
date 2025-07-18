"""
Input validation and sanitization utilities
"""
import re
import html
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError


class InputSanitizer:
    """Sanitize user input to prevent security issues"""
    
    @staticmethod
    def sanitize_text(text, max_length=1000):
        """Sanitize text input"""
        if not text:
            return text
        
        # Strip whitespace
        text = text.strip()
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length]
        
        # HTML escape
        text = html.escape(text)
        
        return text
    
    @staticmethod
    def sanitize_search_query(query, max_length=100):
        """Sanitize search queries"""
        if not query:
            return query
        
        # Strip whitespace and limit length
        query = query.strip()[:max_length]
        
        # Remove potentially dangerous characters
        query = re.sub(r'[<>&"\']', '', query)
        
        # Remove excessive whitespace
        query = re.sub(r'\s+', ' ', query)
        
        return query
    
    @staticmethod
    def validate_url(url):
        """Validate URL input"""
        if not url:
            return True
        
        validator = URLValidator()
        try:
            validator(url)
            return True
        except ValidationError:
            return False
    
    @staticmethod
    def sanitize_api_key(api_key):
        """Sanitize API key input"""
        if not api_key:
            return api_key
        
        # Remove whitespace
        api_key = api_key.strip()
        
        # Remove non-alphanumeric characters (except common API key chars)
        api_key = re.sub(r'[^a-zA-Z0-9\-_]', '', api_key)
        
        # Limit length
        if len(api_key) > 255:
            api_key = api_key[:255]
        
        return api_key
    
    @staticmethod
    def validate_pagination(page, per_page=20, max_per_page=100):
        """Validate pagination parameters"""
        try:
            page = int(page) if page else 1
            per_page = int(per_page) if per_page else 20
        except (ValueError, TypeError):
            page = 1
            per_page = 20
        
        # Ensure positive values
        page = max(1, page)
        per_page = min(max(1, per_page), max_per_page)
        
        return page, per_page


class ContentFilter:
    """Filter content to prevent inappropriate or malicious content"""
    
    # Common XSS attack patterns
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'onmouseover\s*=',
    ]
    
    @staticmethod
    def contains_xss(text):
        """Check if text contains potential XSS patterns"""
        if not text:
            return False
        
        text_lower = text.lower()
        for pattern in ContentFilter.XSS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        
        return False
    
    @staticmethod
    def filter_chat_message(message, max_length=2000):
        """Filter and sanitize chat messages"""
        if not message:
            return message
        
        # Limit length
        message = message[:max_length]
        
        # Check for XSS
        if ContentFilter.contains_xss(message):
            raise ValidationError("Message contains potentially dangerous content")
        
        # Basic sanitization
        message = InputSanitizer.sanitize_text(message, max_length)
        
        return message