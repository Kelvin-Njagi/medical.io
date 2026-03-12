"""
Database management module for the Medical Image Analysis System
"""
import sqlite3
import hashlib
import datetime
import os
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages all database operations"""
    
    def __init__(self, db_path="database/medical_system.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    role TEXT DEFAULT 'user',
                    status TEXT DEFAULT 'pending',
                    security_question TEXT,
                    security_answer TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP,
                    approved_by INTEGER,
                    approved_at TIMESTAMP,
                    FOREIGN KEY (approved_by) REFERENCES users(id)
                )
            ''')
            
            # Roles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role_name TEXT UNIQUE NOT NULL,
                    permissions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Permissions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    permission_name TEXT UNIQUE NOT NULL,
                    description TEXT
                )
            ''')
            
            # User permissions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_permissions (
                    user_id INTEGER,
                    permission_id INTEGER,
                    granted_by INTEGER,
                    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (permission_id) REFERENCES permissions(id),
                    FOREIGN KEY (granted_by) REFERENCES users(id),
                    PRIMARY KEY (user_id, permission_id)
                )
            ''')
            
            # Logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    status TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # Sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # Password reset table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS password_resets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    reset_token TEXT UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            # Medical analysis records table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS medical_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    filename TEXT,
                    filepath TEXT,
                    analysis_type TEXT,
                    scan_type TEXT,
                    body_part TEXT,
                    scan_date TEXT,
                    patient_age INTEGER,
                    notes TEXT,
                    findings TEXT,
                    severity TEXT,
                    quality_score INTEGER,
                    confidence INTEGER,
                    recommendations TEXT,
                    summary TEXT,
                    results TEXT,
                    confidence_score REAL,
                    prediction TEXT,
                    prediction_confidence REAL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            # ensure older databases gain the new columns if missing
            try:
                cursor.execute("ALTER TABLE medical_analyses ADD COLUMN prediction TEXT")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE medical_analyses ADD COLUMN prediction_confidence REAL")
            except Exception:
                pass
            
            # Insert default roles if they don't exist
            roles = [
                ('admin', 'full_control'),
                ('researcher', 'research_analysis'),
                ('clinician', 'clinical_analysis'),
                ('user', 'basic_access')
            ]
            
            for role_name, permissions in roles:
                cursor.execute('''
                    INSERT OR IGNORE INTO roles (role_name, permissions)
                    VALUES (?, ?)
                ''', (role_name, permissions))
            
            # Create default admin if no users exist
            cursor.execute('SELECT COUNT(*) as count FROM users')
            if cursor.fetchone()['count'] == 0:
                from security import SecurityManager
                security = SecurityManager()
                
                # Default admin credentials (should be changed on first login)
                admin_password = security.hash_password("Admin@123")
                security_answer = security.hash_password("blue")
                
                cursor.execute('''
                    INSERT INTO users (
                        username, email, password_hash, first_name, last_name,
                        role, status, security_question, security_answer
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    'admin', 'admin@medical.edu', admin_password,
                    'System', 'Administrator', 'admin', 'active',
                    'What is your favorite color?', security_answer
                ))
                
                logger.info("Default admin user created")

    def execute_query(self, query, params=()):
        """Execute a query and return results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_insert(self, query, params=()):
        """Execute an insert query and return last row id"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid