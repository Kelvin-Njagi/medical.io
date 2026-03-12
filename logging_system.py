"""
Logging system for the Medical Image Analysis System
"""
import logging
from datetime import datetime, timedelta
import streamlit as st
from database import DatabaseManager
import pandas as pd

class LogManager:
    """Manages system logging"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.setup_file_logging()
    
    def setup_file_logging(self):
        """Setup file-based logging"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            filename='logs/system.log',
            level=logging.INFO,
            format=log_format
        )
    
    def log_action(self, user_id, action, details, status="SUCCESS", ip_address=None, user_agent=None):
        """Log a user action to database"""
        try:
            self.db.execute_insert('''
                INSERT INTO system_logs (user_id, action, details, ip_address, user_agent, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, action, details, ip_address, user_agent, status))
            
            # Also log to file
            logger = logging.getLogger(__name__)
            log_message = f"User {user_id}: {action} - {details} [{status}]"
            
            if status == "SUCCESS":
                logger.info(log_message)
            elif status.startswith("FAILED"):
                logger.warning(log_message)
            else:
                logger.error(log_message)
                
        except Exception as e:
            print(f"Error logging action: {e}")
    
    def get_logs(self, days=7, user_id=None, action=None, status=None, limit=None):
        """Retrieve logs with filters"""
        query = "SELECT * FROM system_logs WHERE 1=1"
        params = []
        
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            query += " AND timestamp >= ?"
            params.append(cutoff_date)
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if action:
            query += " AND action = ?"
            params.append(action)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY timestamp DESC"
        
        logs = self.db.execute_query(query, params)
        return [dict(log) for log in logs]
    
    def get_logs_dataframe(self, **kwargs):
        """Get logs as pandas DataFrame"""
        logs = self.get_logs(**kwargs)
        if logs:
            return pd.DataFrame(logs)
        return pd.DataFrame()
    
    def get_user_activity_summary(self, user_id=None, days=30):
        """Get summary of user activity"""
        query = '''
            SELECT 
                user_id,
                u.username,
                COUNT(*) as total_actions,
                SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful_actions,
                SUM(CASE WHEN status LIKE 'FAILED%' THEN 1 ELSE 0 END) as failed_actions,
                MAX(timestamp) as last_action
            FROM system_logs l
            JOIN users u ON l.user_id = u.id
            WHERE timestamp >= datetime('now', ?)
        '''
        params = [f'-{days} days']
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        query += " GROUP BY user_id"
        
        results = self.db.execute_query(query, params)
        return [dict(r) for r in results]
    
    def get_system_stats(self):
        """Get system statistics"""
        stats = {}
        
        # Total users
        result = self.db.execute_query("SELECT COUNT(*) as count FROM users")
        stats['total_users'] = result[0]['count'] if result else 0
        
        # Active users today
        today = datetime.now().date()
        result = self.db.execute_query(
            "SELECT COUNT(DISTINCT user_id) as count FROM system_logs WHERE date(timestamp) = ?",
            (today,)
        )
        stats['active_today'] = result[0]['count'] if result else 0
        
        # Pending approvals
        result = self.db.execute_query(
            "SELECT COUNT(*) as count FROM users WHERE status = 'pending'"
        )
        stats['pending_approvals'] = result[0]['count'] if result else 0
        
        # Total analyses
        result = self.db.execute_query(
            "SELECT COUNT(*) as count FROM medical_analyses"
        )
        stats['total_analyses'] = result[0]['count'] if result else 0
        
        # Failed logins today
        result = self.db.execute_query(
            "SELECT COUNT(*) as count FROM system_logs WHERE action = 'LOGIN_FAILED' AND date(timestamp) = ?",
            (today,)
        )
        stats['failed_logins_today'] = result[0]['count'] if result else 0
        
        return stats