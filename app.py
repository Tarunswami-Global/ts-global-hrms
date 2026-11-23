import streamlit as st
import os
from automation.config import load_page_config, load_settings, ROLE_DEFINITIONS, load_users
from automation.auth import check_authentication
from automation.modules import (
    dashboard, 
    master_compliance,
    monthly_compliance,
    compliance_hub, 
    admin_panel,
    salary_slip,
    appointment,
    increment,
    joining_offer,
    review_letter,
    experience,
    warning_templates
)

# 1. Load Page Config, Fixed Background Watermark & Custom Animations CSS
load_page_config()

# 2. Check Authentication (Includes Animation Video Transition)
if not check_authentication():
    st.stop()

# 3. Fixed Background Watermark of Personal Logo
st.markdown('<div class="fixed-bg-watermark"></div>', unsafe_allow_html=True)

# 4. Load Persistent Enterprise Settings
settings = load_settings()
establishment_name = settings.get('establishment_name', "AAIKRUPA INFRATECH PVT. LTD.")
owner_name = settings.get('signatory_name', "Tarun Swami")
sites_list = settings.get('sites', [
    "M/S. MUNDRA PETROCHEM LIMITED (Mundra)",
    "ANIL Project Site",
    "Aaikrupa Registered Office (Mundra)",
    "Other Client Site"
])

# 5. User Role & Security Context
current_user = st.session_state.get('username', 'admin')
current_role = st.session_state.get('user_role', 'super_admin')
current_display_name = st.session_state.get('user_display_name', 'Tarun Swami')
current_role_title = st.session_state.get('user_role_title', 'Super Administrator & MD')
allowed_sites_list = st.session_state.get('allowed_sites', ['ALL'])

role_info = ROLE_DEFINITIONS.get(current_role, ROLE_DEFINITIONS['super_admin'])
allowed_nav = role_info.get('allowed_nav', [])
badge_color = role_info.get('badge_color', '#DC2626')

effective_sites = sites_list
if allowed_sites_list and "ALL" not in allowed_sites_list:
    effective_sites = [s for s in sites_list if s in allowed_sites_list] or sites_list

with st.sidebar:
    # Brand Zone
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px; padding: 6px 4px 16px 4px; border-bottom: 1px solid rgba(255, 255, 255, 0.08);">
            <div style="width: 38px; height: 38px; background: #F59E0B; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; color: #0F172A; font-weight: 800;">⚡</div>
            <div>
                <h3 style="margin: 0; font-size: 16px; font-weight: 800; color: #FFFFFF; letter-spacing: -0.3px;">TS Global HRMS</h3>
                <p style="margin: 2px 0 0 0; font-size: 11px; color: #94A3B8;">Aaikrupa Infratech Pvt. Ltd.</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    selected_site = st.selectbox(
        "🏢 Select Operating Site",
        effective_sites,
        index=0
    )
    
    st.markdown("""
        <div style="font-size: 10.5px; text-transform: uppercase; font-weight: 700; letter-spacing: 1px; color: #64748B; margin: 16px 0 6px 4px;">
            Main Navigation
        </div>
    """, unsafe_allow_html=True)

    nav_buttons_master = [
        ("🏠 Dashboard Overview", "🏠 Dashboard Overview"),
        ("🛡️ Master License & Site Hub", "🛡️ Master License & Site Hub"),
        ("📊 Monthly Site Compliance", "📊 Monthly Site Compliance Tracker"),
        ("⚖️ Statutory Registers (Forms A-D)", "⚖️ Compliance Portal (Forms A-D & 18)"),
        ("📄 1. Salary Slip Generator", "📄 1. Salary Slip Generate"),
        ("📝 2. Appointment Letter", "📝 2. Appointment Generate"),
        ("📈 3. Salary Increment Letter", "📈 3. Increment Letter"),
        ("🤝 4. Joining Offer Letter", "🤝 4. Joining Offer Letter"),
        ("⭐ 5. Performance Review Letter", "⭐ 5. Review Letter"),
        ("📜 6. Experience Certificate", "📜 6. Experience Certificate"),
        ("⚠️ 7. Disciplinary Notice", "⚠️ 7. Disciplinary & Warning Notice"),
    ]

    # Inner Security: Filter navigation buttons strictly by role permissions
    visible_nav_buttons = [
        (lbl, tgt) for (lbl, tgt) in nav_buttons_master
        if lbl in allowed_nav
    ]

    if 'nav_selection' not in st.session_state:
        st.session_state['nav_selection'] = visible_nav_buttons[0][1] if visible_nav_buttons else "🏠 Dashboard Overview"

    # Query parameter support with role verification
    q_nav = st.query_params.get("nav")
    if q_nav:
        q_target = None
        if q_nav in ["master", "license"] and "🛡️ Master License & Site Hub" in allowed_nav:
            q_target = "🛡️ Master License & Site Hub"
        elif q_nav in ["monthly", "month"] and "📊 Monthly Site Compliance" in allowed_nav:
            q_target = "📊 Monthly Site Compliance Tracker"
        elif q_nav in ["dashboard", "home"]:
            q_target = "🏠 Dashboard Overview"
        elif q_nav in ["admin", "settings"] and current_role == "super_admin":
            q_target = "⚙️ Admin Control Panel"
        
        if q_target:
            st.session_state['nav_selection'] = q_target

    current_target = st.session_state.get('nav_selection', visible_nav_buttons[0][1] if visible_nav_buttons else "🏠 Dashboard Overview")

    # Safety: ensure current target is permitted for this role
    valid_targets = [tgt for (_, tgt) in visible_nav_buttons]
    if current_role == 'super_admin':
        valid_targets.append("⚙️ Admin Control Panel")

    if current_target not in valid_targets and visible_nav_buttons:
        current_target = visible_nav_buttons[0][1]
        st.session_state['nav_selection'] = current_target
    
    for label, target in visible_nav_buttons:
        is_active = (current_target == target)
        btn_type = "primary" if is_active else "secondary"
        if st.button(label, key=f"nav_{target}", type=btn_type, use_container_width=True):
            st.session_state['nav_selection'] = target
            st.rerun()

    # Administration (Restricted to Super Admin only)
    if current_role == 'super_admin':
        st.markdown("""
            <div style="font-size: 10.5px; text-transform: uppercase; font-weight: 700; letter-spacing: 1px; color: #64748B; margin: 16px 0 6px 4px;">
                Administration
            </div>
        """, unsafe_allow_html=True)
        is_admin_active = (current_target == "⚙️ Admin Control Panel")
        if st.button("⚙️ Admin Settings & Control", key="nav_admin_panel", type="primary" if is_admin_active else "secondary", use_container_width=True):
            st.session_state['nav_selection'] = "⚙️ Admin Control Panel"
            st.rerun()

    portal_section = st.session_state['nav_selection']

    # Bottom Health Diagnostics Widget (Oilforce Style)
    st.markdown("""
        <div style="margin-top: 24px; background: #0F172A; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 11.5px;">
                <span style="color: #94A3B8;">System Compliance</span>
                <span style="color: #10B981; font-weight: 700;">● Normal 98%</span>
            </div>
            <div style="height: 5px; background: #334155; border-radius: 3px; margin: 8px 0; overflow: hidden;">
                <div style="height: 100%; width: 98%; background: #10B981;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 10.5px; color: #64748B;">
                <span>Forms A-D Verified</span>
                <span>ISO 27001</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()

# 6. Modern Top Header Bar (Oilforce Solutions Style)
logo1_path = "assets/logo1.png"
col_h_left, col_h_right = st.columns([2.5, 1.2])

with col_h_left:
    st.markdown(f"""
        <div class="main-header">
            <div>
                <h1 style="margin: 0; font-size: 21px; font-weight: 800; color: #0F172A; letter-spacing: -0.4px;">
                    {portal_section.split('(')[0].strip()}
                </h1>
                <p style="margin: 4px 0 0 0; font-size: 12.5px; color: #64748B;">
                    Home &bull; Operations &bull; <strong style="color: #2563EB;">{selected_site}</strong>
                </p>
            </div>
        </div>
    """, unsafe_allow_html=True)

with col_h_right:
    user_initials = "".join([part[0] for part in current_display_name.split()[:2]]).upper() or "TS"
    st.markdown(f"""
        <div class="main-header" style="justify-content: flex-end; gap: 12px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 36px; height: 36px; border-radius: 50%; background: {badge_color}; color: #FFFFFF; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 13px;">
                    {user_initials}
                </div>
                <div style="line-height: 1.2;">
                    <div style="font-size: 13px; font-weight: 700; color: #0F172A;">{current_display_name}</div>
                    <div style="font-size: 10.5px; font-weight: 700; color: {badge_color};">{current_role_title}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

st.write("")

# 7. Security Route Guard & Module Routing
if portal_section not in valid_targets:
    st.error(f"⛔ Access Denied! Your assigned role '{current_role_title}' does not have permission to access '{portal_section}'.")
    st.info("Please select an authorized module from the sidebar.")
    st.stop()

if portal_section == "🏠 Dashboard Overview":
    dashboard.render(selected_site)
elif portal_section == "🛡️ Master License & Site Hub":
    master_compliance.render()
elif portal_section == "📊 Monthly Site Compliance Tracker":
    monthly_compliance.render(selected_site)
elif portal_section == "⚖️ Compliance Portal (Forms A-D & 18)":
    compliance_hub.render(selected_site)
elif portal_section == "📄 1. Salary Slip Generate":
    salary_slip.render(selected_site)
elif portal_section == "📝 2. Appointment Generate":
    appointment.render(selected_site)
elif portal_section == "📈 3. Increment Letter":
    increment.render(selected_site)
elif portal_section == "🤝 4. Joining Offer Letter":
    joining_offer.render(selected_site)
elif portal_section == "⭐ 5. Review Letter":
    review_letter.render(selected_site)
elif portal_section == "📜 6. Experience Certificate":
    experience.render(selected_site)
elif portal_section == "⚠️ 7. Disciplinary & Warning Notice":
    warning_templates.render(selected_site)
elif portal_section == "⚙️ Admin Control Panel":
    admin_panel.render()
else:
    st.subheader(f"🛠️ Module — {selected_site}")
    st.warning("The selected module interface is active.")

st.markdown("---")
st.markdown(f"<p style='text-align: center; color: #64748B; font-size: 12.5px;'>TS Global HR Automation Suite &bull; Enterprise HRMS &copy; 2026 | Developed for {establishment_name} | Owner: {owner_name}</p>", unsafe_allow_html=True)
