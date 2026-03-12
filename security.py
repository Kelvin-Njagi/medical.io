"""
Security utilities for the Medical Image Analysis System
"""
import bcrypt
import secrets
import string
import re
from datetime import datetime, timedelta
import hashlib
import logging

logger = logging.getLogger(__name__)

class SecurityManager:
    """Handles all security-related operations"""
    
    @staticmethod
    def hash_password(password):
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password, hashed):
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    @staticmethod
    def generate_session_token():
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_reset_token():
        """Generate a password reset token"""
        return secrets.token_urlsafe(48)
    
    @staticmethod
    def validate_password_strength(password):
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r"\d", password):
            errors.append("Password must contain at least one digit")
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def sanitize_input(text):
        """Sanitize user input"""
        if not text:
            return text
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", ';', '--', '/*', '*/']
        for char in dangerous_chars:
            text = text.replace(char, '')
        
        return text.strip()
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def check_rate_limit(login_attempts, last_attempt_time, max_attempts=5, lockout_minutes=15):
        """Check if user is rate limited"""
        if login_attempts >= max_attempts:
            if last_attempt_time:
                lockout_end = last_attempt_time + timedelta(minutes=lockout_minutes)
                if datetime.now() < lockout_end:
                    return False, lockout_end
        return True, None
    
    @staticmethod
    def generate_secure_filename(original_filename):
        """Generate a secure filename"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_string = secrets.token_hex(8)
        extension = original_filename.split('.')[-1] if '.' in original_filename else ''
        
        secure_name = f"{timestamp}_{random_string}"
        if extension:
            secure_name += f".{extension}"
        
        return secure_name
    
    @staticmethod
    def is_safe_file(filename, allowed_extensions):
        """Check if file is safe to upload"""
        extension = '.' + filename.split('.')[-1].lower()
        return extension in allowed_extensions