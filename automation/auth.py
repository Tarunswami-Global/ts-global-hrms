import streamlit as st
import time
import os
import base64
from automation.config import load_settings, load_users, hash_password, ROLE_DEFINITIONS

def get_base64_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""

def render_login_transition():
    """Renders the sleek video animation transition from login to dashboard."""
    video_path = os.path.join("assets", "login_transition.webm")
    video_b64 = get_base64_file(video_path)
    
    st.markdown("<br>", unsafe_allow_html=True)
    c_left, c_center, c_right = st.columns([1, 2.2, 1])
    
    with c_center:
        st.markdown("""<div class="transition-box">
<div style="display: inline-flex; align-items: center; gap: 8px; background: #EFF6FF; color: #2563EB; padding: 4px 12px; border-radius: 20px; font-size: 11.5px; font-weight: 700; margin-bottom: 8px;">
⚡ AUTHORIZING SECURE SESSION
</div>
<h2 style="margin: 4px 0 6px 0; color: #0F172A; font-size: 22px; font-weight: 800;">
TS Global HRMS Terminal
</h2>
<p style="margin: 0 0 16px 0; color: #64748B; font-size: 13px;">
Initializing Enterprise Compliance & Operations Engines...
</p>
</div>""", unsafe_allow_html=True)
        
        if video_b64:
            st.markdown(f"""<div style="text-align: center; margin-top: 15px; border-radius: 14px; overflow: hidden; box-shadow: 0 10px 25px rgba(37, 99, 235, 0.2); border: 1.5px solid #2563EB;">
<video width="100%" autoplay muted playsinline loop style="display: block; border-radius: 14px;">
<source src="data:video/webm;base64,{video_b64}" type="video/webm">
</video>
</div>""", unsafe_allow_html=True)
        else:
            st.info("🚀 Launching TS Global Workspace...")

        st.markdown("""<div style="text-align: center; margin: 18px 0 12px 0;">
<p style="color: #10B981; font-weight: 700; font-size: 14px; margin: 0;">
✅ Verification Complete | Loading Site Operations...
</p>
</div>""", unsafe_allow_html=True)

        if st.button("Enter Dashboard ➔", type="primary", use_container_width=True):
            st.session_state['in_transition'] = False
            st.session_state['authenticated'] = True
            st.session_state['username'] = st.session_state.get('pending_username', 'Admin')
            st.rerun()

    time.sleep(3.2)
    st.session_state['in_transition'] = False
    st.session_state['authenticated'] = True
    st.session_state['username'] = st.session_state.get('pending_username', 'Admin')
    st.rerun()

def render_login_form():
    """Renders modern Sellora-style split-screen login portal."""
    settings = load_settings()
    est_name = settings.get('establishment_name', "AAIKRUPA INFRATECH PVT. LTD.")
    
    logo_path = os.path.join("assets", "ts_global_logo.webp")
    logo_b64 = get_base64_file(logo_path)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Outer Card Container
    col_out1, col_center, col_out2 = st.columns([0.15, 3.7, 0.15])
    
    with col_center:
        st.markdown("""<style>
.login-card-container {
background: #FFFFFF;
border-radius: 24px;
border: 1px solid #E2E8F0;
box-shadow: 0 20px 45px -10px rgba(15, 23, 42, 0.08);
overflow: hidden;
padding: 24px;
}
.hero-blue-panel {
background: linear-gradient(145deg, #1D4ED8 0%, #2563EB 55%, #3B82F6 100%);
border-radius: 18px;
padding: 34px 28px;
color: #FFFFFF;
height: 100%;
box-shadow: 0 10px 25px rgba(37, 99, 235, 0.25);
}
.glass-mini-card {
background: rgba(255, 255, 255, 0.95);
color: #0F172A;
border-radius: 12px;
padding: 14px 16px;
box-shadow: 0 8px 20px rgba(15, 23, 42, 0.12);
}
.donut-preview-box {
width: 54px;
height: 54px;
border-radius: 50%;
background: conic-gradient(#2563EB 0% 78%, #10B981 78% 92%, #F59E0B 92% 100%);
display: flex;
align-items: center;
justify-content: center;
}
.donut-inner-box {
width: 38px;
height: 38px;
background: #FFFFFF;
border-radius: 50%;
display: flex;
align-items: center;
justify-content: center;
font-size: 11px;
font-weight: 800;
color: #0F172A;
}
.login-badge-pill {
display: inline-block;
font-size: 11px;
font-weight: 700;
background: #EFF6FF;
color: #2563EB;
padding: 3px 8px;
border-radius: 6px;
}
</style>""", unsafe_allow_html=True)
        
        c_left, c_right = st.columns([1.1, 1.25], gap="large")
        
        # ----------------------------------------------------------------------
        # LEFT COLUMN: SIGN IN FORM (SELLORA STYLE)
        # ----------------------------------------------------------------------
        with c_left:
            logo_img = ""
            if logo_b64:
                logo_img = f'<img src="data:image/webp;base64,{logo_b64}" width="36" style="vertical-align: middle; margin-right: 8px;" />'
            
            st.markdown(f"""<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 20px;">
{logo_img}
<span style="font-size: 18px; font-weight: 800; color: #0F172A; letter-spacing: -0.3px;">TS Global</span>
<span class="login-badge-pill">HRMS 2.0</span>
</div>
<h1 style="font-size: 28px; font-weight: 800; color: #0F172A; letter-spacing: -0.5px; margin-bottom: 4px;">Welcome Back</h1>
<p style="font-size: 13px; color: #64748B; margin-bottom: 20px;">
Enter your credentials to access the TS Global Compliance & HRMS Terminal.
</p>""", unsafe_allow_html=True)
            
            with st.form("sellora_login_form"):
                username_input = st.text_input("Username / Operator Email", placeholder="e.g. admin or darshan")
                password_input = st.text_input("Password", type="password", placeholder="Enter your secret password")
                
                col_rem, col_fgt = st.columns([1, 1])
                with col_rem:
                    st.checkbox("Remember Me", value=True)
                with col_fgt:
                    st.caption("🔒 SHA-256 Encrypted")
                
                submit_login = st.form_submit_button("Sign In to Dashboard ➔", type="primary", use_container_width=True)
                
                if submit_login:
                    u = username_input.strip().lower()
                    p = password_input.strip()
                    
                    if not u or not p:
                        st.error("⚠️ Please enter both Username and Password.")
                    else:
                        users = load_users()
                        if u in users:
                            user = users[u]
                            if not user.get('active', True):
                                st.error("⛔ Account Suspended: Your access has been deactivated by Super Administrator.")
                            else:
                                expected_hash = user.get('password_hash')
                                given_hash = hash_password(p)
                                
                                # Validate hashed password or direct match
                                if given_hash == expected_hash or p == user.get('password'):
                                    st.session_state['pending_username'] = user.get('username', u)
                                    st.session_state['user_role'] = user.get('role', 'super_admin')
                                    st.session_state['user_display_name'] = user.get('full_name', u)
                                    st.session_state['user_role_title'] = user.get('role_title', 'Staff')
                                    st.session_state['allowed_sites'] = user.get('allowed_sites', ['ALL'])
                                    st.session_state['in_transition'] = True
                                    st.rerun()
                                else:
                                    st.error("❌ Invalid Password. Access Denied.")
                        else:
                            st.error("❌ Username not recognized. Please contact Super Administrator.")

            st.markdown("""<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px; margin-top: 18px;">
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
    <strong style="color: #0F172A; font-size: 12px;">🛡️ Enterprise Security Policy</strong>
    <span style="background: #DCFCE7; color: #15803D; font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 8px;">Active</span>
</div>
<div style="font-size: 11px; color: #64748B; line-height: 1.5;">
    Direct passwordless login has been permanently disabled. Outer perimeter and inner module rights are strictly enforced by user role.
</div>
</div>
<div style="margin-top: 18px; display: flex; justify-content: space-between; font-size: 11px; color: #94A3B8;">
<span>© 2026 TS Global HRMS Ltd.</span>
<span>Security Level: Enterprise High</span>
</div>""", unsafe_allow_html=True)

        # ----------------------------------------------------------------------
        # RIGHT COLUMN: SAAS SHOWCASE HERO (SELLORA STYLE)
        # ----------------------------------------------------------------------
        with c_right:
            st.markdown(f"""<div class="hero-blue-panel">
<h2 style="font-size: 24px; font-weight: 800; color: #FFFFFF; line-height: 1.3; margin-bottom: 8px;">
Effortlessly manage your workforce and operations.
</h2>
<p style="font-size: 13px; color: #DBEAFE; line-height: 1.5; margin-bottom: 22px;">
Unified statutory compliance, salary calculations, and automated HR documentation for Mundra & all client sites.
</p>
<div style="display: flex; gap: 12px; margin-bottom: 14px;">
<div class="glass-mini-card" style="flex: 1;">
<div style="font-size: 10.5px; font-weight: 700; color: #64748B; text-transform: uppercase;">ACTIVE WORKFORCE</div>
<div style="font-size: 22px; font-weight: 800; color: #0F172A; margin: 3px 0;">900 Staff</div>
<span style="font-size: 10.5px; color: #10B981; font-weight: 700; background: #DCFCE7; padding: 2px 6px; border-radius: 4px;">▲ 100% Onboarded</span>
</div>
<div class="glass-mini-card" style="flex: 1.1; display: flex; align-items: center; justify-content: space-between;">
<div>
<div style="font-size: 10.5px; font-weight: 700; color: #64748B; text-transform: uppercase;">COMPLIANCE RATE</div>
<div style="font-size: 20px; font-weight: 800; color: #0F172A; margin: 2px 0;">98.5%</div>
<span style="font-size: 11px; color: #64748B;">Forms A, B, C, D</span>
</div>
<div class="donut-preview-box">
<div class="donut-inner-box">98%</div>
</div>
</div>
</div>
<div class="glass-mini-card" style="padding: 16px;">
<div style="display: flex; justify-content: space-between; font-size: 12px; font-weight: 700; color: #334155; margin-bottom: 10px;">
<span>Recent Site Operations</span>
<span style="color: #2563EB; font-weight: 600;">Live Feed</span>
</div>
<div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #F1F5F9; font-size: 12px;">
<div>
<strong style="color: #0F172A;">Manish R. Joshi</strong>
<div style="font-size: 10.5px; color: #64748B;">Offer Letter • Sr. QC Inspector</div>
</div>
<span style="background: #DCFCE7; color: #15803D; padding: 2px 8px; border-radius: 10px; font-weight: 700; font-size: 10.5px;">₹37,234 Gross</span>
</div>
<div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #F1F5F9; font-size: 12px;">
<div>
<strong style="color: #0F172A;">Mundra Petrochem Limited</strong>
<div style="font-size: 10.5px; color: #64748B;">Labour License: 1199597230</div>
</div>
<span style="background: #DBEAFE; color: #1D4ED8; padding: 2px 8px; border-radius: 10px; font-weight: 700; font-size: 10.5px;">Active Site</span>
</div>
<div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0; font-size: 12px;">
<div>
<strong style="color: #0F172A;">Statutory Form A (Attendance)</strong>
<div style="font-size: 10.5px; color: #64748B;">Muster Roll Register</div>
</div>
<span style="background: #DCFCE7; color: #15803D; padding: 2px 8px; border-radius: 10px; font-weight: 700; font-size: 10.5px;">Verified</span>
</div>
</div>
<div style="margin-top: 20px; font-size: 11.5px; color: #DBEAFE; display: flex; justify-content: space-between;">
<span>🔒 TLS 1.3 / ISO 27001 Certified</span>
<span>{est_name}</span>
</div>
</div>""", unsafe_allow_html=True)

def check_authentication():
    """Handles secure login, video transition animation, and session state validation."""
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
        st.session_state['username'] = ''
        st.session_state['in_transition'] = False

    if st.session_state.get('in_transition'):
        render_login_transition()
        return False

    if not st.session_state['authenticated']:
        render_login_form()
        return False
    
    return True
