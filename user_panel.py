"""
User panel for Medical Image Analysis System
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import numpy as np

class UserPanel:
    """User panel functionality"""
    
    def __init__(self, auth_manager, db_manager, log_manager):
        self.auth = auth_manager
        self.db = db_manager
        self.logger = log_manager
    
    def medical_analysis(self):
        """Medical image analysis interface"""
        from pages import analysis
        analysis.show(self.db, st.session_state.user_id, st.session_state.username)
    
    def my_studies(self):
        """Display user's studies and analyses"""
        st.header("📁 My Studies")
        
        # Get user's analyses
        analyses = self.db.execute_query('''
            SELECT * FROM medical_analyses
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (st.session_state.user_id,))
        
        if analyses:
            df = pd.DataFrame([dict(a) for a in analyses])
            
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                type_filter = st.multiselect("Filter by Type", df['analysis_type'].unique())
            with col2:
                status_filter = st.multiselect("Filter by Status", df['status'].unique())
            
            # Apply filters
            filtered_df = df.copy()
            if type_filter:
                filtered_df = filtered_df[filtered_df['analysis_type'].isin(type_filter)]
            if status_filter:
                filtered_df = filtered_df[filtered_df['status'].isin(status_filter)]
            
            # Display studies
            for _, study in filtered_df.iterrows():
                with st.expander(f"{study['analysis_type']} - {study['created_at']}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Status:** {study['status']}")
                    with col2:
                        st.write(f"**Confidence:** {study['confidence_score'] or 'N/A'}")
                    with col3:
                        if study['status'] == 'completed':
                            if st.button(f"View Results", key=f"view_{study['id']}"):
                                st.session_state['viewing_study'] = study['id']
                                st.rerun()
                    
                    if study['status'] == 'completed' and st.session_state.get('viewing_study') == study['id']:
                        # Parse and display results
                        import ast
                        try:
                            results = ast.literal_eval(study['results'])
                            self.display_analysis_results(results, True)
                        except:
                            st.write(study['results'])
        else:
            st.info("No studies found. Start by creating a new analysis.")
    
    def profile(self):
        """User profile management"""
        st.header("👤 My Profile")
        
        # Get user data
        user = self.db.execute_query('''
            SELECT * FROM users WHERE id = ?
        ''', (st.session_state.user_id,))[0]
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image("assets/images/profile_placeholder.png", use_column_width=True)
            st.write(f"**Member since:** {user['created_at']}")
            st.write(f"**Last login:** {user['last_login'] or 'N/A'}")
        
        with col2:
            with st.form("profile_form"):
                st.subheader("Personal Information")
                
                first_name = st.text_input("First Name", value=user['first_name'] or '')
                last_name = st.text_input("Last Name", value=user['last_name'] or '')
                email = st.text_input("Email", value=user['email'])
                
                st.subheader("Change Password")
                current_password = st.text_input("Current Password", type="password")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")
                
                submitted = st.form_submit_button("Update Profile")
                
                if submitted:
                    updates = []
                    params = []
                    
                    if first_name != user['first_name']:
                        updates.append("first_name = ?")
                        params.append(first_name)
                    
                    if last_name != user['last_name']:
                        updates.append("last_name = ?")
                        params.append(last_name)
                    
                    if email != user['email']:
                        if self.auth.security.validate_email(email):
                            updates.append("email = ?")
                            params.append(email)
                        else:
                            st.error("Invalid email format")
                    
                    if new_password:
                        if not current_password:
                            st.error("Please enter current password")
                        elif new_password != confirm_password:
                            st.error("New passwords do not match")
                        else:
                            # Verify current password
                            if self.auth.security.verify_password(current_password, user['password_hash']):
                                is_strong, errors = self.auth.security.validate_password_strength(new_password)
                                if is_strong:
                                    password_hash = self.auth.security.hash_password(new_password)
                                    updates.append("password_hash = ?")
                                    params.append(password_hash)
                                else:
                                    st.error(errors[0])
                            else:
                                st.error("Current password is incorrect")
                    
                    if updates:
                        params.append(st.session_state.user_id)
                        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
                        self.db.execute_query(query, params)
                        
                        self.logger.log_action(
                            st.session_state.user_id,
                            "PROFILE_UPDATED",
                            "Updated profile information"
                        )
                        
                        st.success("Profile updated successfully")