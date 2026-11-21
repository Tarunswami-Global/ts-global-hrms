import streamlit as st
import pandas as pd
import os
from automation.config import load_settings, save_settings

def render():
    st.subheader("⚙️ Administrator Master Control Panel & Universal Settings")
    
    if st.session_state.get('username') == 'Admin':
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
            st.markdown("### 🔒 User Access & Role-Based Control")
            users_data = [
                {"User ID": "Admin", "Role": "Super Administrator", "Status": "Active", "Module Access": "All Modules (Full Admin)", "Settings Control": "Enabled"},
                {"User ID": "darshan", "Role": "Plant HR Associate", "Status": "Active", "Module Access": "Registers, Slips, Letters", "Settings Control": "Disabled"}
            ]
            st.dataframe(pd.DataFrame(users_data), use_container_width=True)

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
