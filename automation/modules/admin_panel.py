import streamlit as st
import pandas as pd
import os
from automation.config import load_settings, save_settings, load_users, save_users, hash_password, ROLE_DEFINITIONS

def render():
    st.subheader("⚙️ Administrator Master Control Panel & Universal Settings")
    
    current_role = st.session_state.get('user_role', '')
    current_user = st.session_state.get('username', '')
    is_super_admin = (current_role == 'super_admin' or current_user.lower() == 'admin')
    
    if is_super_admin:
        st.markdown('<div class="success-box">✅ Welcome, Super Administrator. You have full global control over the TS Global HRMS Suite.</div>', unsafe_allow_html=True)
        
        # Persistent Storage Setup for Logos
        os.makedirs("assets", exist_ok=True)
        logo1_path = "assets/logo1.png"
        logo2_path = "assets/logo2.png"
        
        settings = load_settings()

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🎨 Universal Logo Manager", 
            "🏢 Universal Company Defaults", 
            "📍 Operating Sites Manager",
            "👥 User Rights Control", 
            "📊 System Development Tracker"
        ])
        
        with tab1:
            st.markdown("### 🖼️ Enterprise Logo Management")
            st.write("Upload **Logo 1** (Primary Header Logo) and **Logo 2** (Secondary / Client Logo). Logos persist and reflect across all documents and headers.")
            
            col_l1, col_l2 = st.columns(2)
            
            with col_l1:
                st.markdown("#### Primary Logo (Logo 1)")
                up_logo1 = st.file_uploader("Upload Logo 1 (.png/.jpg)", type=["png", "jpg", "jpeg"], key="upl1_key")
                if up_logo1 is not None:
                    with open(logo1_path, "wb") as f:
                        f.write(up_logo1.getbuffer())
                    st.success("✅ Logo 1 successfully uploaded and saved!")
                    st.rerun()
                
                if os.path.exists(logo1_path):
                    st.image(logo1_path, width=120, caption="Active Primary Logo")
                else:
                    st.info("Using default system logo.")

            with col_l2:
                st.markdown("#### Secondary Logo (Logo 2)")
                up_logo2 = st.file_uploader("Upload Logo 2 (.png/.jpg)", type=["png", "jpg", "jpeg"], key="upl2_key")
                if up_logo2 is not None:
                    with open(logo2_path, "wb") as f:
                        f.write(up_logo2.getbuffer())
                    st.success("✅ Logo 2 successfully uploaded and saved!")
                    st.rerun()
                
                if os.path.exists(logo2_path):
                    st.image(logo2_path, width=120, caption="Active Secondary Logo")
                else:
                    st.info("No secondary logo uploaded yet.")

        with tab2:
            st.markdown("### 📋 Universal Company & Statutory Defaults")
            st.write("These settings are persistently saved in `data/settings.json` and automatically populate all compliance registers and letters.")
            
            with st.form("compliance_defaults_form"):
                new_est = st.text_input("Default Establishment / Contractor Name", value=settings.get('establishment_name', ''))
                new_pe = st.text_input("Default Principal Employer & Address", value=settings.get('principal_employer', ''))
                new_lic = st.text_input("Factory / Contractor License No.", value=settings.get('license_no', ''))
                
                c_s1, c_s2 = st.columns(2)
                with c_s1:
                    new_sig_name = st.text_input("Default Authorized Signatory Name", value=settings.get('signatory_name', 'Tarun Swami'))
                with c_s2:
                    new_sig_title = st.text_input("Signatory Designation / Title", value=settings.get('signatory_title', 'Authorized Signatory / Managing Director'))
                
                new_addr = st.text_area("Registered Office Address", value=settings.get('company_address', ''), height=70)
                
                save_settings_btn = st.form_submit_button("💾 Save Settings to Persistent Storage", type="primary")
                if save_settings_btn:
                    settings['establishment_name'] = new_est
                    settings['principal_employer'] = new_pe
                    settings['license_no'] = new_lic
                    settings['signatory_name'] = new_sig_name
                    settings['signatory_title'] = new_sig_title
                    settings['company_address'] = new_addr
                    
                    if save_settings(settings):
                        st.session_state['global_establishment'] = new_est
                        st.session_state['global_principal_employer'] = new_pe
                        st.success("✅ Universal defaults successfully saved and persisted across system restarts!")
                    else:
                        st.error("❌ Failed to save settings to file.")

        with tab3:
            st.markdown("### 📍 Operating Sites Management")
            st.write("Manage project locations that appear in the global site selector and on all generated documents.")
            
            current_sites = settings.get('sites', [])
            st.markdown("#### Active Operating Sites:")
            for idx, site in enumerate(current_sites):
                st.markdown(f"• **{idx + 1}.** `{site}`")
            
            st.markdown("---")
            st.markdown("#### Add New Operating Site")
            new_site_input = st.text_input("New Site Name & Location", placeholder="e.g. Adani Solar Project Site (Mundra)")
            if st.button("➕ Add Site to System", type="secondary"):
                if new_site_input.strip() and new_site_input.strip() not in current_sites:
                    current_sites.append(new_site_input.strip())
                    settings['sites'] = current_sites
                    save_settings(settings)
                    st.success(f"✅ Added site: '{new_site_input.strip()}'")
                    st.rerun()

        with tab4:
            st.markdown("### 👥 User Accounts & Role-Based Access Control (RBAC)")
            st.caption("Aap yahan se naye users create kar sakte hain, existing users ke passwords reset kar sakte hain, aur unke roles & module permissions define kar sakte hain:")
            
            # Role Matrix Summary Pills
            st.markdown("""
            <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 16px;">
                <div style="background: #FEE2E2; border: 1px solid #FCA5A5; color: #991B1B; padding: 6px 12px; border-radius: 8px; font-size: 11.5px; font-weight: 700;">
                    👑 Super Admin (Full Control)
                </div>
                <div style="background: #DBEAFE; border: 1px solid #93C5FD; color: #1E40AF; padding: 6px 12px; border-radius: 8px; font-size: 11.5px; font-weight: 700;">
                    🛡️ Compliance Head (Licenses & Billing)
                </div>
                <div style="background: #D1FAE5; border: 1px solid #6EE7B7; color: #065F46; padding: 6px 12px; border-radius: 8px; font-size: 11.5px; font-weight: 700;">
                    👥 HR Executive (Slips & Letters)
                </div>
                <div style="background: #FEF3C7; border: 1px solid #FCD34D; color: #92400E; padding: 6px 12px; border-radius: 8px; font-size: 11.5px; font-weight: 700;">
                    🏗️ Site Supervisor (Site Checklist)
                </div>
                <div style="background: #F3F4F6; border: 1px solid #D1D5DB; color: #374151; padding: 6px 12px; border-radius: 8px; font-size: 11.5px; font-weight: 700;">
                    🔍 Client Auditor (Read-Only)
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            all_users = load_users()
            sites_options = settings.get('sites', [])
            role_keys = list(ROLE_DEFINITIONS.keys())
            role_labels = [f"{k} — {ROLE_DEFINITIONS[k]['title']}" for k in role_keys]
            
            # 1. Existing Users Table
            st.markdown("#### 📋 Active System Users Directory")
            u_table_rows = []
            for u_k, u_v in all_users.items():
                r_key = u_v.get('role', 'hr_manager')
                r_info = ROLE_DEFINITIONS.get(r_key, {})
                st_badge = "🟢 Active" if u_v.get('active', True) else "🔴 Suspended"
                allowed_s = ", ".join(u_v.get('allowed_sites', ['ALL']))
                
                u_table_rows.append({
                    "Username": u_k,
                    "Full Name": u_v.get('full_name', u_k),
                    "Assigned Role": r_info.get('title', r_key),
                    "Email Address": u_v.get('email', 'N/A'),
                    "Account Status": st_badge,
                    "Operating Sites": allowed_s
                })
            st.dataframe(pd.DataFrame(u_table_rows), use_container_width=True)
            
            with st.expander("🔐 View Role Action & Document Creation Rights Matrix ('Kon Kya Bna Skta Hai')", expanded=True):
                st.caption("Central Governance Matrix: Granular CRUD & Document Generation Permissions across all 5 System Roles:")
                perm_matrix_data = [
                    {
                        "Capability / Action Right": "1. 👔 Executive Director Cockpit",
                        "Super Admin (MD)": "✅ Full Access",
                        "Compliance Head": "✅ Presentation Ready",
                        "HR Manager": "⛔ Hidden",
                        "Site Supervisor": "⛔ Hidden",
                        "Client Auditor": "⛔ Hidden"
                    },
                    {
                        "Capability / Action Right": "2. 📄 Generate Form XIX Salary Slips",
                        "Super Admin (MD)": "✅ Create & Issue",
                        "Compliance Head": "✅ Verify & Issue",
                        "HR Manager": "✅ Create & Issue",
                        "Site Supervisor": "🔒 Read-Only",
                        "Client Auditor": "🔒 Read-Only"
                    },
                    {
                        "Capability / Action Right": "3. 📝 Issue Appointment Letters",
                        "Super Admin (MD)": "✅ Issue & Sign",
                        "Compliance Head": "✅ Issue & Sign",
                        "HR Manager": "✅ Issue & Sign",
                        "Site Supervisor": "⛔ Restricted",
                        "Client Auditor": "⛔ Restricted"
                    },
                    {
                        "Capability / Action Right": "4. 🤝 Candidate Joining Offer Letters",
                        "Super Admin (MD)": "✅ Issue & Sign",
                        "Compliance Head": "🔒 View Only",
                        "HR Manager": "✅ Issue & Sign",
                        "Site Supervisor": "⛔ Restricted",
                        "Client Auditor": "⛔ Restricted"
                    },
                    {
                        "Capability / Action Right": "5. 📈 Salary Increment Letters",
                        "Super Admin (MD)": "✅ Issue & Sign",
                        "Compliance Head": "🔒 View Only",
                        "HR Manager": "✅ Issue & Sign",
                        "Site Supervisor": "⛔ Restricted",
                        "Client Auditor": "⛔ Restricted"
                    },
                    {
                        "Capability / Action Right": "6. ⚠️ Issue Disciplinary & Warning Memos",
                        "Super Admin (MD)": "✅ Issue Notice",
                        "Compliance Head": "🔒 View Only",
                        "HR Manager": "✅ Issue Notice",
                        "Site Supervisor": "⛔ Restricted",
                        "Client Auditor": "⛔ Restricted"
                    },
                    {
                        "Capability / Action Right": "7. 🛡️ Master Licenses, Sites & POs CRUD",
                        "Super Admin (MD)": "✅ Full Add/Edit/Del",
                        "Compliance Head": "✅ Add & Renew (No Del)",
                        "HR Manager": "🔒 Reference Only",
                        "Site Supervisor": "🔒 Reference Only",
                        "Client Auditor": "🔒 Reference Only"
                    },
                    {
                        "Capability / Action Right": "8. 📑 Sign Form 21(4) & Approve Bill Clearance",
                        "Super Admin (MD)": "✅ Authority to Approve",
                        "Compliance Head": "✅ Authorized Sign-off",
                        "HR Manager": "⛔ Restricted",
                        "Site Supervisor": "⛔ Restricted",
                        "Client Auditor": "🔒 View Audit Proofs"
                    },
                    {
                        "Capability / Action Right": "9. 📎 Upload Challans & Site Muster",
                        "Super Admin (MD)": "✅ Allowed",
                        "Compliance Head": "✅ Allowed",
                        "HR Manager": "⛔ Restricted",
                        "Site Supervisor": "✅ Allowed (Site Level)",
                        "Client Auditor": "🔒 Inspection Only"
                    },
                    {
                        "Capability / Action Right": "10. ⚙️ User Creation & Role Assignment",
                        "Super Admin (MD)": "✅ Full Control",
                        "Compliance Head": "⛔ Restricted",
                        "HR Manager": "⛔ Restricted",
                        "Site Supervisor": "⛔ Restricted",
                        "Client Auditor": "⛔ Restricted"
                    }
                ]
                st.dataframe(pd.DataFrame(perm_matrix_data), use_container_width=True)

            st.write("")
            col_u1, col_u2 = st.columns([1, 1], gap="large")
            
            # 2. Add New User Account Form
            with col_u1:
                st.markdown("#### ➕ Create New User Login")
                with st.form("form_create_user_admin"):
                    n_username = st.text_input("New Username (Login ID)", placeholder="e.g. rohan_hr or site_mundra")
                    n_name = st.text_input("User Full Name", placeholder="e.g. Rohan Mehta")
                    n_email = st.text_input("Official Email Address", placeholder="e.g. rohan@aaikrupainfra.com")
                    
                    sel_role_label = st.selectbox("Assign System Role", role_labels, index=2)
                    n_role = role_keys[role_labels.index(sel_role_label)]
                    
                    c_pw1, c_pw2 = st.columns(2)
                    with c_pw1:
                        n_pw = st.text_input("Set Password", type="password", placeholder="Secret password")
                    with c_pw2:
                        n_pw_conf = st.text_input("Confirm Password", type="password", placeholder="Confirm password")
                        
                    sel_sites = st.multiselect("Allowed Site Operations", ["ALL"] + sites_options, default=["ALL"])
                    n_active = st.checkbox("Active Account Immediately", value=True)
                    
                    btn_create_u = st.form_submit_button("➕ Create User Account", type="primary", use_container_width=True)
                    if btn_create_u:
                        clean_u = n_username.strip().lower()
                        if not clean_u or not n_name.strip():
                            st.error("Please provide both Username and Full Name.")
                        elif clean_u in all_users:
                            st.error(f"Username '{clean_u}' already exists! Choose another.")
                        elif not n_pw or n_pw != n_pw_conf:
                            st.error("Passwords do not match or are empty.")
                        else:
                            all_users[clean_u] = {
                                "username": clean_u,
                                "password_hash": hash_password(n_pw.strip()),
                                "full_name": n_name.strip(),
                                "role": n_role,
                                "role_title": ROLE_DEFINITIONS[n_role]['title'],
                                "email": n_email.strip(),
                                "active": n_active,
                                "allowed_sites": sel_sites if sel_sites else ["ALL"],
                                "created_at": str(pd.Timestamp.now())[:19]
                            }
                            save_users(all_users)
                            st.success(f"✅ User account '{clean_u}' created successfully with role '{ROLE_DEFINITIONS[n_role]['title']}'!")
                            st.rerun()

            # 3. Edit Existing User / Password Reset / Deactivate Form
            with col_u2:
                st.markdown("#### ✏️ Manage User, Role & Password Reset")
                u_choices = list(all_users.keys())
                sel_edit_u = st.selectbox("Select User Account to Modify", u_choices, index=0)
                target_u_data = all_users[sel_edit_u]
                
                with st.form(f"form_edit_user_{sel_edit_u}"):
                    e_name = st.text_input("Full Name", value=target_u_data.get('full_name', ''))
                    e_email = st.text_input("Email", value=target_u_data.get('email', ''))
                    
                    cur_r = target_u_data.get('role', 'hr_manager')
                    cur_r_idx = role_keys.index(cur_r) if cur_r in role_keys else 0
                    e_role_label = st.selectbox("Change Role", role_labels, index=cur_r_idx)
                    e_role = role_keys[role_labels.index(e_role_label)]
                    
                    st.caption("Leave password blank if you do not want to change it:")
                    new_reset_pw = st.text_input("Reset Password (Optional)", type="password", placeholder="Enter new password to change")
                    
                    e_active = st.checkbox("Account Status: Active", value=target_u_data.get('active', True))
                    
                    btn_save_u = st.form_submit_button("💾 Save User Modifications", type="primary", use_container_width=True)
                    if btn_save_u:
                        target_u_data['full_name'] = e_name.strip()
                        target_u_data['email'] = e_email.strip()
                        target_u_data['role'] = e_role
                        target_u_data['role_title'] = ROLE_DEFINITIONS[e_role]['title']
                        target_u_data['active'] = e_active
                        
                        if new_reset_pw.strip():
                            target_u_data['password_hash'] = hash_password(new_reset_pw.strip())
                            
                        save_users(all_users)
                        st.success(f"✅ User account '{sel_edit_u}' successfully updated!")
                        st.rerun()

                # Delete User Button (with safety guard)
                if sel_edit_u == 'admin':
                    st.caption("🔒 Primary 'admin' super-administrator cannot be deleted.")
                elif sel_edit_u == current_user.lower():
                    st.caption("🔒 Cannot delete yourself while logged in.")
                else:
                    if st.button(f"🗑️ Delete Account '{sel_edit_u}'", type="secondary", key=f"btn_del_u_{sel_edit_u}"):
                        del all_users[sel_edit_u]
                        save_users(all_users)
                        st.warning(f"Deleted user account '{sel_edit_u}'.")
                        st.rerun()

        with tab5:
            st.markdown("### 📊 System Status & Feature Completion Tracker")
            dev_df = pd.DataFrame([
                {"Module / Feature": "Core Architecture & Alignment", "Status": "Completed ✅", "Description": "Unified modular engine with persistent configuration."},
                {"Module / Feature": "Statutory Hub (Form 18)", "Status": "Completed ✅", "Description": "Consolidated Excel scanning, safe columns, A4 PDF & Word."},
                {"Module / Feature": "Forms A, B, C, D Templates", "Status": "Completed ✅", "Description": "Pre-formatted blank statutory Excel template generators."},
                {"Module / Feature": "Salary Slip Generator", "Status": "Completed ✅", "Description": "Single entry live calculator + Excel bulk upload with PDF/Word."},
                {"Module / Feature": "Appointment Letter Module", "Status": "Completed ✅", "Description": "Custom terms, probation, CTC breakdown, Word & PDF."},
                {"Module / Feature": "Salary Increment Letter Module", "Status": "Completed ✅", "Description": "Current vs Revised salary, hike % auto-calc, Word & PDF."},
                {"Module / Feature": "Joining Offer Letter Module", "Status": "Completed ✅", "Description": "Offer terms, reporting date, document checklist, Word & PDF."},
                {"Module / Feature": "Review & Confirmation Letter", "Status": "Completed ✅", "Description": "Probation completion, performance grading, Word & PDF."},
                {"Module / Feature": "Letter & Warning Templates", "Status": "Completed ✅", "Description": "Multi-tier show-cause & safety violation memos, Word & PDF."}
            ])
            st.dataframe(dev_df, use_container_width=True)
            
    else:
        st.error("⛔ Access Denied! This section is strictly restricted for Super Administrators only.")
