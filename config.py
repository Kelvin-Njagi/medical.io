"""
Configuration settings for the Medical Image Analysis System
"""
import os
from datetime import timedelta

class Config:
    """Main configuration class"""
    
    # Application settings
    APP_NAME = "Medical Image Analysis System"
    APP_VERSION = "1.0.0"
    APP_ICON = "🏥"
    
    # Database settings
    DATABASE_PATH = "database/medical_system.db"
    
    # Security settings
    SESSION_TIMEOUT = timedelta(minutes=30)
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_TIME = timedelta(minutes=15)
    
    # Password policy
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_SPECIAL_CHAR = True
    REQUIRE_DIGIT = True
    REQUIRE_UPPERCASE = True
    
    # Logging settings
    LOG_RETENTION_DAYS = 30
    LOG_LEVEL = "INFO"
    
    # File upload settings
    MAX_UPLOAD_SIZE_MB = 100
    ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.dcm', '.nii']
    
    # System paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ASSETS_DIR = os.path.join(BASE_DIR, "assets")
    DATABASE_DIR = os.path.join(BASE_DIR, "database")
    
    @classmethod
    def init_directories(cls):
        """Initialize required directories"""
        directories = [
            cls.DATABASE_DIR,
            cls.ASSETS_DIR,
            os.path.join(cls.ASSETS_DIR, "images"),
            os.path.join(cls.BASE_DIR, "logs")
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)