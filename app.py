"""
Main application entry point for Medical Image Analysis System
"""
import streamlit as st
import sys
from pathlib import Path
import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config import Config
from database import DatabaseManager
from auth import AuthenticationManager
from security import SecurityManager
from logging_system import LogManager
from pages import login, register, forgot_password, dashboard, analysis
from admin_panel import AdminPanel
from user_panel import UserPanel

# Initialize configuration
Config.init_directories()

# Page configuration
st.set_page_config(
    page_title="Medical Image Analysis System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    css_file = Path(Config.ASSETS_DIR) / "style.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'page' not in st.session_state:
    st.session_state.page = 'login'

# Initialize managers
auth_manager = AuthenticationManager()
db_manager = DatabaseManager()
security_manager = SecurityManager()
log_manager = LogManager()

# Application header
def render_header():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="academic-header">
            <h1>🏥 MEDICAL IMAGE ANALYSIS SYSTEM</h1>
            <h3>Advanced Deep Learning for Medical Diagnostics</h3>
            <p>ERIC NYAGA KIVUTI | B141/24868/2022 | University of Embu</p>
        </div>
        """, unsafe_allow_html=True)

# Application footer
def render_footer():
    st.markdown("""
    <div class="footer">
        <hr>
        <p style="text-align: center; color: #666;">
            © 2026 Medical Image Analysis System | 
            Research Proposal for Bachelor's Degree in Information Technology | 
            University of Embu
        </p>
    </div>
    """, unsafe_allow_html=True)

# Navigation sidebar
def render_sidebar():
    with st.sidebar:
        import os
        logo_path = "assets/images/medical_logo.png"
        if os.path.exists(logo_path):
            st.image(logo_path, use_column_width=True)
        else:
            st.markdown("🩺 **Medical App**")
        st.markdown("## Navigation")
        
        if st.session_state.authenticated:
            st.markdown(f"Welcome, **{st.session_state.get('username', 'User')}**")
            st.markdown(f"Role: **{st.session_state.get('role', 'user').title()}**")
            st.markdown("---")
            
            if st.button("🏠 Dashboard", use_container_width=True):
                st.session_state.page = 'dashboard'
                st.rerun()
            
            if st.button("📊 Analysis", use_container_width=True):
                st.session_state.page = 'analysis'
                st.rerun()
            
            if st.button("📁 My Studies", use_container_width=True):
                st.session_state.page = 'studies'
                st.rerun()
            
            if st.button("👤 Profile", use_container_width=True):
                st.session_state.page = 'profile'
                st.rerun()
            
            if st.session_state.role == 'admin':
                st.markdown("---")
                st.markdown("### Admin Panel")
                if st.button("⚙️ User Management", use_container_width=True):
                    st.session_state.page = 'admin_users'
                    st.rerun()
                if st.button("📋 System Logs", use_container_width=True):
                    st.session_state.page = 'admin_logs'
                    st.rerun()
                if st.button("📈 Analytics", use_container_width=True):
                    st.session_state.page = 'admin_analytics'
                    st.rerun()
            
            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True):
                auth_manager.logout_user()
                st.session_state.page = 'login'
                st.rerun()
        else:
            st.markdown("### Welcome")
            if st.button("🔑 Login", use_container_width=True, key="main_login_btn"):
                st.session_state.page = 'login'
                st.rerun()
            if st.button("📝 Register", use_container_width=True, key="main_register_btn"):
                st.session_state.page = 'register'
                st.rerun()
            if st.button("❓ Forgot Password", use_container_width=True, key="main_forgot_btn"):
                st.session_state.page = 'forgot_password'
                st.rerun()
        
        st.markdown("---")
        st.markdown("### System Info")
        st.info(f"Version: {Config.APP_VERSION}\n\nSession: {'Active' if st.session_state.authenticated else 'Inactive'}")

# Main application router
def main():
    # Check session validity
    if st.session_state.authenticated:
        if not auth_manager.check_session():
            st.session_state.authenticated = False
            st.session_state.page = 'login'
            st.warning("Session expired. Please login again.")
    
    # Render header
    render_header()
    
    # Render sidebar
    render_sidebar()
    
    # Main content area
    main_col = st.container()
    
    with main_col:
        # Route to appropriate page
        if not st.session_state.authenticated:
            if st.session_state.page == 'login':
                login.show(auth_manager)
            elif st.session_state.page == 'register':
                register.show(auth_manager)
            elif st.session_state.page == 'forgot_password':
                forgot_password.show(auth_manager)
            else:
                login.show(auth_manager)
        else:
            # allow analysis page for any authenticated user (including admins)
            if st.session_state.page == 'analysis':
                user_panel = UserPanel(auth_manager, db_manager, log_manager)
                user_panel.medical_analysis()
            elif st.session_state.role == 'admin':
                admin_panel = AdminPanel(auth_manager, db_manager, log_manager)
                
                if st.session_state.page == 'admin_users':
                    admin_panel.user_management()
                elif st.session_state.page == 'admin_logs':
                    admin_panel.system_logs()
                elif st.session_state.page == 'admin_analytics':
                    admin_panel.analytics_dashboard()
                else:
                    dashboard.show(auth_manager, db_manager, log_manager, is_admin=True)
            else:
                user_panel = UserPanel(auth_manager, db_manager, log_manager)
                
                if st.session_state.page == 'studies':
                    user_panel.my_studies()
                elif st.session_state.page == 'profile':
                    user_panel.profile()
                else:
                    dashboard.show(auth_manager, db_manager, log_manager, is_admin=False)
    
    # Render footer
    render_footer()

if __name__ == "__main__":
    main()