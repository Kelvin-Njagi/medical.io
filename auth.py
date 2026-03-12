"""
Authentication module for the Medical Image Analysis System
"""
import streamlit as st
from datetime import datetime, timedelta
import logging
from database import DatabaseManager
from security import SecurityManager
from logging_system import LogManager

logger = logging.getLogger(__name__)

class AuthenticationManager:
    """Manages user authentication and session handling"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.security = SecurityManager()
        self.logger = LogManager()
    
    def login_user(self, username, password):
        """Authenticate a user"""
        try:
            # Get user from database
            users = self.db.execute_query(
                "SELECT * FROM users WHERE username = ? OR email = ?",
                (username, username)
            )
            
            if not users:
                self.logger.log_action(
                    None, "LOGIN_FAILED", 
                    f"Failed login attempt for username: {username}",
                    status="FAILED - User not found"
                )
                return False, "Invalid username or password"
            
            user = dict(users[0])
            
            # Check if account is locked
            if user.get('locked_until'):
                lockout_time = datetime.strptime(user['locked_until'], '%Y-%m-%d %H:%M:%S')
                if datetime.now() < lockout_time:
                    return False, f"Account locked until {lockout_time}"
            
            # Verify password
            if not self.security.verify_password(password, user['password_hash']):
                # Increment login attempts
                attempts = user['login_attempts'] + 1
                
                if attempts >= 5:
                    lockout_until = datetime.now() + timedelta(minutes=15)
                    self.db.execute_query(
                        "UPDATE users SET login_attempts = ?, locked_until = ? WHERE id = ?",
                        (attempts, lockout_until, user['id'])
                    )
                else:
                    self.db.execute_query(
                        "UPDATE users SET login_attempts = ? WHERE id = ?",
                        (attempts, user['id'])
                    )
                
                self.logger.log_action(
                    user['id'], "LOGIN_FAILED", 
                    f"Failed login attempt - Invalid password",
                    status="FAILED"
                )
                return False, "Invalid username or password"
            
            # Check if account is approved
            if user['status'] != 'active':
                self.logger.log_action(
                    user['id'], "LOGIN_FAILED",
                    f"Login attempt on {user['status']} account",
                    status=f"FAILED - Account {user['status']}"
                )
                return False, f"Your account is {user['status']}. Please contact administrator."
            
            # Successful login
            self.db.execute_query(
                "UPDATE users SET login_attempts = 0, last_login = ? WHERE id = ?",
                (datetime.now(), user['id'])
            )
            
            # Create session
            session_token = self.security.generate_session_token()
            expires_at = datetime.now() + timedelta(hours=8)
            
            self.db.execute_insert(
                "INSERT INTO sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)",
                (user['id'], session_token, expires_at)
            )
            
            # Set session in Streamlit
            st.session_state['authenticated'] = True
            st.session_state['user_id'] = user['id']
            st.session_state['username'] = user['username']
            st.session_state['role'] = user['role']
            st.session_state['session_token'] = session_token
            st.session_state['login_time'] = datetime.now()
            
            self.logger.log_action(
                user['id'], "LOGIN_SUCCESS",
                f"User logged in successfully",
                status="SUCCESS"
            )
            
            return True, "Login successful"
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False, "An error occurred during login"
    
    def register_user(self, user_data):
        """Register a new user"""
        try:
            # Validate required fields
            required_fields = ['username', 'email', 'password', 'first_name', 
                             'last_name', 'security_question', 'security_answer']
            
            for field in required_fields:
                if field not in user_data or not user_data[field]:
                    return False, f"{field} is required"
            
            # Validate email
            if not self.security.validate_email(user_data['email']):
                return False, "Invalid email format"
            
            # Validate password strength
            is_strong, errors = self.security.validate_password_strength(user_data['password'])
            if not is_strong:
                return False, errors[0]
            
            # Check if username exists
            existing = self.db.execute_query(
                "SELECT id FROM users WHERE username = ?",
                (user_data['username'],)
            )
            if existing:
                return False, "Username already exists"
            
            # Check if email exists
            existing = self.db.execute_query(
                "SELECT id FROM users WHERE email = ?",
                (user_data['email'],)
            )
            if existing:
                return False, "Email already registered"
            
            # Hash password and security answer
            password_hash = self.security.hash_password(user_data['password'])
            security_answer_hash = self.security.hash_password(user_data['security_answer'])
            
            # Insert user
            user_id = self.db.execute_insert('''
                INSERT INTO users (
                    username, email, password_hash, first_name, last_name,
                    security_question, security_answer, role, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_data['username'], user_data['email'], password_hash,
                user_data['first_name'], user_data['last_name'],
                user_data['security_question'], security_answer_hash,
                'user', 'pending'
            ))
            
            self.logger.log_action(
                user_id, "USER_REGISTERED",
                f"New user registered: {user_data['username']}",
                status="PENDING_APPROVAL"
            )
            
            return True, "Registration successful. Please wait for admin approval."
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False, "An error occurred during registration"
    
    def logout_user(self):
        """Log out the current user"""
        if 'user_id' in st.session_state and 'session_token' in st.session_state:
            self.logger.log_action(
                st.session_state['user_id'],
                "LOGOUT",
                "User logged out",
                status="SUCCESS"
            )
            
            # Invalidate session
            self.db.execute_query(
                "UPDATE sessions SET is_active = 0 WHERE session_token = ?",
                (st.session_state['session_token'],)
            )
        
        # Clear session state
        for key in ['authenticated', 'user_id', 'username', 'role', 
                   'session_token', 'login_time']:
            if key in st.session_state:
                del st.session_state[key]
        
        return True
    
    def check_session(self):
        """Check if current session is valid"""
        if 'authenticated' not in st.session_state:
            return False
        
        if not st.session_state['authenticated']:
            return False
        
        # Check session expiry
        if 'session_token' in st.session_state:
            sessions = self.db.execute_query(
                "SELECT * FROM sessions WHERE session_token = ? AND is_active = 1",
                (st.session_state['session_token'],)
            )
            
            if not sessions:
                return False
            
            session = dict(sessions[0])
            # Handle microseconds in expires_at by splitting on '.'
            expires_at_str = session['expires_at'].split('.')[0]
            expires_at = datetime.strptime(expires_at_str, '%Y-%m-%d %H:%M:%S')
            
            if datetime.now() > expires_at:
                return False
        
        return True
    
    def reset_password(self, username, security_answer, new_password):
        """Reset user password"""
        try:
            # Get user
            users = self.db.execute_query(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )
            
            if not users:
                return False, "User not found"
            
            user = dict(users[0])
            
            # Verify security answer
            if not self.security.verify_password(security_answer, user['security_answer']):
                self.logger.log_action(
                    user['id'], "PASSWORD_RESET_FAILED",
                    "Failed security answer verification",
                    status="FAILED"
                )
                return False, "Incorrect security answer"
            
            # Validate new password
            is_strong, errors = self.security.validate_password_strength(new_password)
            if not is_strong:
                return False, errors[0]
            
            # Update password
            new_password_hash = self.security.hash_password(new_password)
            self.db.execute_query(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (new_password_hash, user['id'])
            )
            
            self.logger.log_action(
                user['id'], "PASSWORD_RESET",
                "Password reset successful",
                status="SUCCESS"
            )
            
            return True, "Password reset successful"
            
        except Exception as e:
            logger.error(f"Password reset error: {e}")
            return False, "An error occurred during password reset"