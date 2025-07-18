"""
Encryption utilities for sensitive data storage
"""
import base64
import os
from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models


class FieldEncryption:
    """Handle field-level encryption for sensitive data"""
    
    @staticmethod
    def get_key():
        """Get or generate encryption key"""
        key = getattr(settings, 'ENCRYPTION_KEY', None)
        if not key:
            # Generate a key if not provided
            key = Fernet.generate_key().decode()
            
        # Ensure key is bytes
        if isinstance(key, str):
            # If it's a placeholder, generate a real key
            if key == 'your-encryption-key-for-api-keys':
                key = Fernet.generate_key().decode()
            key = key.encode()
        
        return key
    
    @staticmethod
    def encrypt(value):
        """Encrypt a string value"""
        if not value:
            return value
            
        key = FieldEncryption.get_key()
        fernet = Fernet(key)
        encrypted_value = fernet.encrypt(value.encode())
        return base64.b64encode(encrypted_value).decode()
    
    @staticmethod
    def decrypt(encrypted_value):
        """Decrypt a string value"""
        if not encrypted_value:
            return encrypted_value
            
        try:
            key = FieldEncryption.get_key()
            fernet = Fernet(key)
            decoded_value = base64.b64decode(encrypted_value.encode())
            decrypted_value = fernet.decrypt(decoded_value)
            return decrypted_value.decode()
        except Exception:
            # If decryption fails, return original value (for migration compatibility)
            return encrypted_value


class EncryptedCharField(models.CharField):
    """CharField that automatically encrypts/decrypts data"""
    
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return FieldEncryption.decrypt(value)
    
    def to_python(self, value):
        if value is None:
            return value
        return FieldEncryption.decrypt(value)
    
    def get_prep_value(self, value):
        if value is None:
            return value
        return FieldEncryption.encrypt(value)