"""
Admin panel for Medical Image Analysis System
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

class AdminPanel:
    """Admin panel functionality"""
    
    def __init__(self, auth_manager, db_manager, log_manager):
        self.auth = auth_manager
        self.db = db_manager
        self.logger = log_manager
    
    def user_management(self):
        """User management interface"""
        st.header("👥 User Management")
        
        # Tabs for different user management functions
        tab1, tab2, tab3, tab4 = st.tabs([
            "All Users", "Pending Approvals", "Create User", "User Roles"
        ])
        
        with tab1:
            self.show_all_users()
        
        with tab2:
            self.show_pending_approvals()
        
        with tab3:
            self.create_user()
        
        with tab4:
            self.manage_roles()
    
    def show_all_users(self):
        """Display all users with management options"""
        users = self.db.execute_query('''
            SELECT id, username, email, first_name, last_name, role, status, 
                   created_at, last_login
            FROM users
            ORDER BY created_at DESC
        ''')
        
        if users:
            df = pd.DataFrame([dict(u) for u in users])
            
            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                role_filter = st.multiselect("Filter by Role", df['role'].unique())
            with col2:
                status_filter = st.multiselect("Filter by Status", df['status'].unique())
            with col3:
                search = st.text_input("Search", placeholder="Username or email")
            
            # Apply filters
            filtered_df = df.copy()
            if role_filter:
                filtered_df = filtered_df[filtered_df['role'].isin(role_filter)]
            if status_filter:
                filtered_df = filtered_df[filtered_df['status'].isin(status_filter)]
            if search:
                filtered_df = filtered_df[
                    filtered_df['username'].str.contains(search, case=False) |
                    filtered_df['email'].str.contains(search, case=False)
                ]
            
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": "ID",
                    "username": "Username",
                    "email": "Email",
                    "first_name": "First Name",
                    "last_name": "Last Name",
                    "role": "Role",
                    "status": "Status",
                    "created_at": "Registered",
                    "last_login": "Last Login"
                }
            )
            
            # User actions
            st.subheader("User Actions")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            selected_user = st.selectbox(
                "Select User",
                options=filtered_df['username'].tolist(),
                key="user_select"
            )
            
            if selected_user:
                user_data = filtered_df[filtered_df['username'] == selected_user].iloc[0]
                
                with col1:
                    if st.button("🔄 Enable/Disable"):
                        new_status = 'disabled' if user_data['status'] == 'active' else 'active'
                        self.db.execute_query(
                            "UPDATE users SET status = ? WHERE id = ?",
                            (new_status, user_data['id'])
                        )
                        self.logger.log_action(
                            st.session_state.user_id,
                            "USER_STATUS_CHANGED",
                            f"Changed user {selected_user} status to {new_status}"
                        )
                        st.success(f"User {selected_user} status updated")
                        st.rerun()
                
                with col2:
                    if st.button("🔑 Reset Password"):
                        # Generate temporary password
                        temp_password = "Temp@123"  # In production, generate securely
                        password_hash = self.auth.security.hash_password(temp_password)
                        self.db.execute_query(
                            "UPDATE users SET password_hash = ? WHERE id = ?",
                            (password_hash, user_data['id'])
                        )
                        self.logger.log_action(
                            st.session_state.user_id,
                            "PASSWORD_RESET_ADMIN",
                            f"Reset password for user {selected_user}"
                        )
                        st.info(f"Temporary password: {temp_password}")
                
                with col3:
                    if st.button("🗑️ Delete User"):
                        if st.checkbox("Confirm deletion"):
                            self.db.execute_query(
                                "DELETE FROM users WHERE id = ?",
                                (user_data['id'],)
                            )
                            self.logger.log_action(
                                st.session_state.user_id,
                                "USER_DELETED",
                                f"Deleted user {selected_user}"
                            )
                            st.success(f"User {selected_user} deleted")
                            st.rerun()
                
                with col4:
                    if st.button("📋 View Logs"):
                        logs = self.logger.get_logs(user_id=user_data['id'], days=30)
                        if logs:
                            log_df = pd.DataFrame(logs)
                            st.dataframe(log_df)
                
                with col5:
                    if st.button("✏️ Edit Role"):
                        new_role = st.selectbox(
                            "New Role",
                            ['user', 'researcher', 'clinician', 'admin'],
                            key="role_select"
                        )
                        if st.button("Update Role"):
                            self.db.execute_query(
                                "UPDATE users SET role = ? WHERE id = ?",
                                (new_role, user_data['id'])
                            )
                            self.logger.log_action(
                                st.session_state.user_id,
                                "ROLE_CHANGED",
                                f"Changed user {selected_user} role to {new_role}"
                            )
                            st.success(f"Role updated for {selected_user}")
                            st.rerun()
        else:
            st.info("No users found")
    
    def show_pending_approvals(self):
        """Show users pending approval"""
        pending = self.db.execute_query('''
            SELECT id, username, email, first_name, last_name, created_at
            FROM users
            WHERE status = 'pending'
            ORDER BY created_at
        ''')
        
        if pending:
            df = pd.DataFrame([dict(p) for p in pending])
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.subheader("Approve Users")
            selected = st.multiselect(
                "Select users to approve",
                options=df['username'].tolist()
            )
            
            if selected and st.button("✅ Approve Selected"):
                for username in selected:
                    user_id = df[df['username'] == username]['id'].iloc[0]
                    self.db.execute_query('''
                        UPDATE users 
                        SET status = 'active', approved_by = ?, approved_at = ?
                        WHERE id = ?
                    ''', (st.session_state.user_id, datetime.now(), user_id))
                    
                    self.logger.log_action(
                        st.session_state.user_id,
                        "USER_APPROVED",
                        f"Approved user {username}"
                    )
                
                st.success(f"Approved {len(selected)} users")
                st.rerun()
        else:
            st.info("No pending approvals")
    
    def create_user(self):
        """Create a new user"""
        with st.form("create_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                username = st.text_input("Username *")
                email = st.text_input("Email *")
                password = st.text_input("Password *", type="password")
                role = st.selectbox("Role", ['user', 'researcher', 'clinician', 'admin'])
            
            with col2:
                first_name = st.text_input("First Name *")
                last_name = st.text_input("Last Name *")
                status = st.selectbox("Status", ['active', 'pending', 'disabled'])
            
            submit = st.form_submit_button("Create User")
            
            if submit:
                if not all([username, email, password, first_name, last_name]):
                    st.error("Please fill in all required fields")
                else:
                    # Hash password
                    password_hash = self.auth.security.hash_password(password)
                    
                    # Insert user
                    user_id = self.db.execute_insert('''
                        INSERT INTO users (
                            username, email, password_hash, first_name, last_name,
                            role, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (username, email, password_hash, first_name, last_name,
                          role, status, datetime.now()))
                    
                    self.logger.log_action(
                        st.session_state.user_id,
                        "USER_CREATED",
                        f"Created user {username} with role {role}"
                    )
                    
                    st.success(f"User {username} created successfully")
    
    def manage_roles(self):
        """Manage user roles and permissions"""
        st.subheader("🔐 Role Management")
        
        # Available roles
        available_roles = ['user', 'researcher', 'clinician', 'admin']
        
        # Get all users
        users = self.db.execute_query('''
            SELECT id, username, email, role, status
            FROM users
            ORDER BY username
        ''')
        
        if not users:
            st.info("No users found")
            return
        
        # Tab 1: Bulk Role Assignment
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("#### 📋 User Roles Overview")
            
            # Display all users with their roles
            df = pd.DataFrame([dict(u) for u in users])
            
            # Create editable role selection
            st.write("Select users and assign roles:")
            
            selected_users = st.multiselect(
                "Select users to modify",
                options=df['username'].tolist(),
                help="Choose one or more users"
            )
            
            if selected_users:
                st.markdown("---")
                
                # Get the selected users data
                selected_df = df[df['username'].isin(selected_users)]
                
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.write("**Current Roles:**")
                    for idx, row in selected_df.iterrows():
                        st.write(f"• {row['username']}: **{row['role'].title()}**")
                
                with col_b:
                    new_role = st.selectbox(
                        "Assign new role to selected users",
                        available_roles,
                        key="bulk_role_select"
                    )
                    
                    if st.button("✅ Update Selected Users' Roles", use_container_width=True):
                        for username in selected_users:
                            user_id = df[df['username'] == username]['id'].iloc[0]
                            
                            # Update role
                            self.db.execute_query(
                                "UPDATE users SET role = ? WHERE id = ?",
                                (new_role, user_id)
                            )
                            
                            # Log the action
                            self.logger.log_action(
                                st.session_state.user_id,
                                "ROLE_CHANGED",
                                f"Changed user {username} role to {new_role}",
                                status="SUCCESS"
                            )
                        
                        st.success(f"✅ Updated {len(selected_users)} user(s) to role: {new_role.title()}")
                        st.rerun()
        
        with col2:
            st.markdown("#### 📊 Role Distribution")
            role_counts = df['role'].value_counts()
            st.bar_chart(role_counts)
        
        st.markdown("---")
        
        # Tab 2: Individual User Role Management
        st.markdown("#### 👤 Individual User Management")
        
        selected_user = st.selectbox(
            "Select a user to edit",
            options=df['username'].tolist(),
            key="individual_user_select"
        )
        
        if selected_user:
            user_data = df[df['username'] == selected_user].iloc[0]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Username:** {user_data['username']}")
                st.write(f"**Email:** {user_data['email']}")
            
            with col2:
                st.write(f"**Current Role:** **{user_data['role'].title()}**")
                st.write(f"**Status:** {user_data['status'].title()}")
            
            with col3:
                new_role = st.selectbox(
                    "Change role",
                    available_roles,
                    index=available_roles.index(user_data['role']),
                    key="individual_role_select"
                )
                
                new_status = st.selectbox(
                    "Change status",
                    ['active', 'disabled', 'pending'],
                    index=['active', 'disabled', 'pending'].index(user_data['status']),
                    key="status_select"
                )
            
            col_x, col_y, col_z = st.columns(3)
            
            with col_x:
                if st.button("💾 Save Changes", use_container_width=True):
                    if new_role != user_data['role'] or new_status != user_data['status']:
                        self.db.execute_query(
                            "UPDATE users SET role = ?, status = ? WHERE id = ?",
                            (new_role, new_status, user_data['id'])
                        )
                        
                        changes = []
                        if new_role != user_data['role']:
                            changes.append(f"Role: {user_data['role']} → {new_role}")
                        if new_status != user_data['status']:
                            changes.append(f"Status: {user_data['status']} → {new_status}")
                        
                        self.logger.log_action(
                            st.session_state.user_id,
                            "USER_UPDATED",
                            f"Updated user {selected_user}: {', '.join(changes)}",
                            status="SUCCESS"
                        )
                        
                        st.success("✅ Changes saved successfully")
                        st.rerun()
                    else:
                        st.info("ℹ️ No changes to save")
            
            with col_y:
                if st.button("🔑 Reset Password", use_container_width=True):
                    # Generate temporary password
                    temp_password = "TempPass123!"
                    password_hash = self.auth.security.hash_password(temp_password)
                    
                    self.db.execute_query(
                        "UPDATE users SET password_hash = ? WHERE id = ?",
                        (password_hash, user_data['id'])
                    )
                    
                    self.logger.log_action(
                        st.session_state.user_id,
                        "PASSWORD_RESET",
                        f"Reset password for user {selected_user}",
                        status="SUCCESS"
                    )
                    
                    st.success(f"✅ Password reset to: **{temp_password}**")
            
            with col_z:
                if st.button("🗑️ Delete User", use_container_width=True):
                    self.db.execute_query(
                        "DELETE FROM users WHERE id = ?",
                        (user_data['id'],)
                    )
                    
                    self.logger.log_action(
                        st.session_state.user_id,
                        "USER_DELETED",
                        f"Deleted user {selected_user}",
                        status="SUCCESS"
                    )
                    
                    st.success(f"✅ User {selected_user} deleted")
                    st.rerun()
        
        st.markdown("---")
        
        # Tab 3: Role Definitions
        st.markdown("#### 🔑 Role Definitions")
        
        role_definitions = {
            'user': 'Basic user - Can upload and view personal scans',
            'researcher': 'Researcher - Can upload, analyze, and share research data',
            'clinician': 'Clinician - Can access patient records and clinical tools',
            'admin': 'Administrator - Full system access and user management'
        }
        
        col1, col2 = st.columns(2)
        for idx, (role, description) in enumerate(role_definitions.items()):
            if idx % 2 == 0:
                col = col1
            else:
                col = col2
            
            with col:
                st.info(f"**{role.title()}:** {description}")
    
    def system_logs(self):
        """View system logs"""
        st.header("📋 System Logs")
        
        # Filters
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            days = st.number_input("Days", min_value=1, max_value=90, value=7)
        
        with col2:
            actions = self.db.execute_query(
                "SELECT DISTINCT action FROM system_logs ORDER BY action"
            )
            action_list = [a['action'] for a in actions] if actions else []
            selected_action = st.selectbox("Action", ["All"] + action_list)
        
        with col3:
            statuses = ['All', 'SUCCESS', 'FAILED', 'PENDING']
            selected_status = st.selectbox("Status", statuses)
        
        with col4:
            users = self.db.execute_query(
                "SELECT DISTINCT user_id, username FROM users WHERE user_id IS NOT NULL"
            )
            user_list = [f"{u['username']} (ID: {u['user_id']})" for u in users] if users else []
            selected_user = st.selectbox("User", ["All"] + user_list)
        
        # Get logs
        logs = self.logger.get_logs(days=days)
        
        if logs:
            df = pd.DataFrame(logs)
            
            # Apply filters
            if selected_action != "All":
                df = df[df['action'] == selected_action]
            if selected_status != "All":
                df = df[df['status'] == selected_status]
            if selected_user != "All":
                user_id = int(selected_user.split("ID: ")[1].rstrip(")"))
                df = df[df['user_id'] == user_id]
            
            # Display logs
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "timestamp": "Time",
                    "user_id": "User ID",
                    "action": "Action",
                    "details": "Details",
                    "status": "Status",
                    "ip_address": "IP Address"
                }
            )
            
            # Export option
            if st.button("📥 Export Logs"):
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    f"system_logs_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
        else:
            st.info("No logs found for the selected period")
    
    def analytics_dashboard(self):
        """Analytics dashboard"""
        st.header("📊 Analytics Dashboard")
        
        # System overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        # User growth over time
        user_growth = self.db.execute_query('''
            SELECT date(created_at) as date, COUNT(*) as cumulative_count
            FROM users
            WHERE created_at IS NOT NULL
            GROUP BY date(created_at)
            ORDER BY date
        ''')
        
        if user_growth:
            df = pd.DataFrame([dict(u) for u in user_growth])
            fig = px.line(df, x='date', y='cumulative_count', 
                         title='User Growth Over Time')
            st.plotly_chart(fig, use_container_width=True)
        
        # Activity heatmap
        activity = self.db.execute_query('''
            SELECT 
                strftime('%H', timestamp) as hour,
                strftime('%w', timestamp) as day,
                COUNT(*) as count
            FROM system_logs
            WHERE timestamp >= date('now', '-30 days')
            GROUP BY hour, day
        ''')
        
        if activity:
            df = pd.DataFrame([dict(a) for a in activity])
            df['day'] = df['day'].map({
                '0': 'Sun', '1': 'Mon', '2': 'Tue', '3': 'Wed',
                '4': 'Thu', '5': 'Fri', '6': 'Sat'
            })
            
            pivot = df.pivot(index='day', columns='hour', values='count')
            fig = px.imshow(pivot, title='Activity Heatmap (Last 30 Days)')
            st.plotly_chart(fig, use_container_width=True)