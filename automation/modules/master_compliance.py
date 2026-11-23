import streamlit as st
import json
import os
import datetime
import pandas as pd
from automation.config import (
    load_master_registry, 
    save_master_registry, 
    get_base64_image,
    has_permission,
    render_permission_guard
)

def get_logo_html(logo_path, default_text, max_height=48, max_width=140):
    if logo_path and os.path.exists(logo_path):
        ext = os.path.splitext(logo_path)[1].lower().replace('.', '')
        if ext == 'jpg': ext = 'jpeg'
        b64 = get_base64_image(logo_path)
        if b64:
            return f'<img src="data:image/{ext};base64,{b64}" style="max-height: {max_height}px; max-width: {max_width}px; object-fit: contain; border-radius: 6px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); background: #FFFFFF; padding: 2px;">'
    return f'<div style="background: #0F172A; color: #FFFFFF; font-weight: 800; font-size: 12px; padding: 6px 12px; border-radius: 8px; letter-spacing: 0.5px; display: inline-block;">{default_text[:14]}</div>'


today = datetime.date.today()

def render():
    reg = load_master_registry()
    if not reg or 'sites' not in reg:
        st.error("Master registry data not found or empty. Please check `data/master_registry.json`.")
        return

    # Styling (Oilforce Enterprise Light Theme)
    st.markdown("""
    <style>
        .header-box-m {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 16px 24px;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .kpi-card-m {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 16px 18px;
            box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
        }
        .status-badge-m {
            font-size: 11px;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 14px;
            display: inline-block;
        }
        .badge-green-m { background: #DCFCE7; color: #166534; border: 1px solid #86EFAC; }
        .badge-amber-m { background: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; }
        .badge-blue-m { background: #DBEAFE; color: #1E40AF; border: 1px solid #93C5FD; }
        .badge-red-m { background: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }
        .sim-payload-m {
            background: #FFFFFF;
            border: 1.5px solid #BFDBFE;
            border-radius: 12px;
            padding: 18px;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.08);
        }
        .cert-preview-box-m {
            background: #FDFCF7;
            border: 2px dashed #B45309;
            border-radius: 12px;
            padding: 24px;
            box-shadow: inset 0 0 15px rgba(180, 83, 9, 0.04);
            font-family: 'Times New Roman', serif;
        }
    </style>
    """, unsafe_allow_html=True)

    # Top Header
    st.markdown("""
    <div class="header-box-m">
        <div>
            <h2 style="margin: 0; font-size: 20px; font-weight: 800; color: #0F172A;">
                🛡️ Master Entity, Client PO & Statutory License Engine
            </h2>
            <p style="margin: 3px 0 0 0; font-size: 12.5px; color: #64748B;">
                Aai Krupa Group Central Backbone &bull; Principal Employer Form V &bull; CLRA Capacity Guard &bull; Stamped License Archive
            </p>
        </div>
        <div style="background: #EFF6FF; border: 1px solid #BFDBFE; color: #2563EB; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 12px;">
            ⚡ Enterprise Master Hub
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Top Metrics Row
    k1, k2, k3, k4 = st.columns(4)
    total_entities = len(reg.get('entities', {}))
    total_clients = len(reg.get('clients', {}))
    total_pos = len(reg.get('pos', {}))
    total_sites = len(reg.get('sites', {}))

    total_cap = sum(s.get('labour_cap', 0) for s in reg.get('sites', {}).values())
    total_active = sum(s.get('active_headcount', 0) for s in reg.get('sites', {}).values())
    pct_occ = int((total_active / total_cap * 100)) if total_cap > 0 else 0

    with k1:
        st.markdown(f"""
        <div class="kpi-card-m">
            <span style="font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;">Group Subsidiaries</span>
            <h2 style="margin: 4px 0 0 0; font-size: 24px; font-weight: 800; color: #0F172A;">{total_entities} Entities</h2>
            <span style="font-size: 11.5px; color: #2563EB; font-weight: 600;">AIPL, Ashapura, PM, GBBS</span>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="kpi-card-m">
            <span style="font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;">Principal Employers (PE)</span>
            <h2 style="margin: 4px 0 0 0; font-size: 24px; font-weight: 800; color: #0F172A;">{total_clients} Clients</h2>
            <span style="font-size: 11.5px; color: #10B981; font-weight: 600;">Adani, Linde, Tata, Jindal, KCL</span>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="kpi-card-m">
            <span style="font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;">Work Orders / POs</span>
            <h2 style="margin: 4px 0 0 0; font-size: 24px; font-weight: 800; color: #0F172A;">{total_pos} Active POs</h2>
            <span style="font-size: 11.5px; color: #D97706; font-weight: 600;">Form V Linked Contracts</span>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div class="kpi-card-m">
            <span style="font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;">CLRA Capacity & Deployment</span>
            <h2 style="margin: 4px 0 0 0; font-size: 24px; font-weight: 800; color: #0F172A;">{total_active} / {total_cap}</h2>
            <span style="font-size: 11.5px; color: #8B5CF6; font-weight: 600;">{pct_occ}% Group Capacity Utilized</span>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Navigation Tabs
    tab_options = [
        "📍 1. Site Codes & Capacity Guard (Add / Edit / Safe Delete)",
        "⚡ 2. Universal Data-Pull & Auto-Draft Simulator (Zero Typing)",
        "🛡️ 3. Statutory Expiry Radar & Stamped Copy Archive ('Kon Active Hai')",
        "🏢 4. Group Subsidiaries, Clients & PO Directory"
    ]

    tab_param = st.query_params.get("sub")
    if tab_param:
        if tab_param in ["1", "sites"]: st.session_state["master_nav_radio"] = tab_options[0]
        elif tab_param in ["2", "simulator"]: st.session_state["master_nav_radio"] = tab_options[1]
        elif tab_param in ["3", "radar"]: st.session_state["master_nav_radio"] = tab_options[2]
        elif tab_param in ["4", "directory", "logos"]: st.session_state["master_nav_radio"] = tab_options[3]

    if "master_nav_radio" not in st.session_state:
        st.session_state["master_nav_radio"] = tab_options[0]

    selected_nav = st.radio("Master Sections", tab_options, key="master_nav_radio", horizontal=True, label_visibility="collapsed")
    st.write("")

    # TAB 1: SITE CODES & CAPACITY GUARD
    if selected_nav == tab_options[0]:
        st.markdown("### 📍 Operating Site Codes Directory & Work Locations")
        st.caption("Har Site Code hamara unique compliance node hai jo Company, Client PE, Form V, CLRA License, aur Manpower Cap ko control karta hai:")
        
        sites = reg.get('sites', {})
        table_data = []
        
        for s_code, s_info in sites.items():
            ent_name = reg['entities'].get(s_info.get('entity_id'), {}).get('name', s_info.get('entity_id'))
            client_name = reg['clients'].get(s_info.get('client_id'), {}).get('name', s_info.get('client_id'))
            
            clra_exp_str = s_info.get('clra_valid_till', '2026-12-31')
            clra_status = s_info.get('clra_status', 'active')
            
            try:
                exp_date = datetime.datetime.strptime(clra_exp_str, "%Y-%m-%d").date()
                days_left = (exp_date - today).days
                if clra_status == "renewal_submitted":
                    status_str = f"🔵 Renewal In-Process (ALC)"
                elif days_left < 0:
                    status_str = f"🔴 Expired ({abs(days_left)}d ago)"
                elif days_left <= 60:
                    status_str = f"🟡 Expiring Soon ({days_left}d)"
                else:
                    status_str = f"🟢 Active ({days_left}d)"
            except Exception:
                status_str = "🟢 Active"

            fv_obj = s_info.get('form_v', {})
            fv_summary = f"{fv_obj.get('form_v_no', 'N/A')} (Cap: {fv_obj.get('pe_cap', s_info.get('labour_cap'))})"
            
            cap = s_info.get('labour_cap', 100)
            deployed = s_info.get('active_headcount', 0)
            util_pct = int(deployed / cap * 100) if cap > 0 else 0
            cap_str = f"{deployed}/{cap} ({util_pct}%)"

            table_data.append({
                "Site Code": s_code,
                "Operating Entity": ent_name.split()[0] if ent_name else "",
                "Client PE": client_name.split('(')[0].strip() if client_name else "",
                "Principal Emp Form V": fv_summary,
                "CLRA License No": s_info.get('clra_license_no'),
                "Manpower Capacity": cap_str,
                "WC Policy No": s_info.get('wc_policy_no'),
                "Compliance Status": status_str,
                "Site In-Charge": s_info.get('site_incharge')
            })
        
        st.dataframe(table_data, use_container_width=True)
        
        st.markdown("---")
        c_action1, c_action2 = st.columns(2)
        
        with c_action1:
            st.markdown("#### ➕ Add New Site Code (with Form V & CLRA)")
            with st.form("form_add_site_prod"):
                new_code = st.text_input("New Site Code", placeholder="e.g. MPL-CIVIL-03 or JINDAL-MAINT-01")
                new_name = st.text_input("Site / Project Name", placeholder="e.g. MPL Civil Foundation & Boundary Works")
                
                ent_keys = list(reg['entities'].keys())
                ent_sel = st.selectbox("Operating Subsidiary Entity", ent_keys, format_func=lambda x: f"{x} - {reg['entities'][x]['name']}")
                
                client_keys = list(reg['clients'].keys())
                client_sel = st.selectbox("Client (Principal Employer)", client_keys, format_func=lambda x: f"{reg['clients'][x]['name']}")
                
                po_keys = list(reg['pos'].keys())
                po_sel = st.selectbox("Associated Purchase Order / Work Order", po_keys, format_func=lambda x: f"{x} ({reg['pos'][x]['title'][:35]}...)")
                
                st.markdown("##### 📜 Principal Employer Form V & CLRA License")
                cfv1, cfv2 = st.columns(2)
                with cfv1:
                    fv_no_in = st.text_input("Form V Certificate Number", placeholder="e.g. ADANI-MPL-FV-2026-99")
                    fv_date_in = st.date_input("Form V Issue Date", value=today - datetime.timedelta(days=30))
                with cfv2:
                    fv_cap_in = st.number_input("Form V Max Approved Workers", min_value=10, max_value=2000, value=150)
                    fv_issued_by = st.text_input("Form V Signatory / Authority", placeholder="e.g. Mr. R. K. Varma (Head Contracts)")

                nature = st.text_input("Nature of Work", placeholder="e.g. Heavy Rigging, Plant Maintenance, Piping")
                location = st.text_area("Detailed Site Location Address", placeholder="Full plant / site address for official documentation")
                incharge = st.text_input("Site In-Charge / Compliance Head", value="Darshan Sir")
                
                c_cap1, c_cap2 = st.columns(2)
                with c_cap1:
                    labour_cap = st.number_input("Max Permitted Labour Cap (CLRA)", min_value=10, max_value=2000, value=int(fv_cap_in))
                with c_cap2:
                    active_hc = st.number_input("Initial Deployed Manpower", min_value=0, max_value=2000, value=50)
                    
                clra_no = st.text_input("CLRA Labour License Number", placeholder="e.g. 1199597230 or GJ-01-CLRA-998877")
                clra_exp = st.date_input("CLRA License Expiry Date", value=today + datetime.timedelta(days=365))
                
                st.markdown("##### 🏥 Workmen Compensation / Insurance Policy")
                wc_no = st.text_input("Workmen Compensation (WC) Policy No", placeholder="e.g. WC-NIA-2026-001")
                wc_ins = st.text_input("Insurance Company", value="The New India Assurance Co. Ltd.")
                wc_exp = st.date_input("WC Policy Expiry Date", value=today + datetime.timedelta(days=365))
                
                submit_site = st.form_submit_button("➕ Save & Register Site Code", type="primary", use_container_width=True)
                if submit_site:
                    if new_code.strip() and new_name.strip():
                        clean_code = new_code.strip().upper()
                        reg['sites'][clean_code] = {
                            "site_code": clean_code,
                            "site_name": new_name.strip(),
                            "entity_id": ent_sel,
                            "client_id": client_sel,
                            "po_no": po_sel,
                            "nature_of_work": nature.strip(),
                            "site_location": location.strip(),
                            "site_incharge": incharge.strip(),
                            "labour_cap": int(labour_cap),
                            "active_headcount": int(active_hc),
                            "form_v": {
                                "form_v_no": fv_no_in.strip(),
                                "form_v_date": str(fv_date_in),
                                "pe_cap": int(fv_cap_in),
                                "issued_by": fv_issued_by.strip()
                            },
                            "clra_license_no": clra_no.strip(),
                            "clra_valid_till": str(clra_exp),
                            "clra_status": "active",
                            "clra_challan_ref": "",
                            "clra_amendments": [],
                            "clra_doc_file": f"CLRA_{clean_code}.pdf",
                            "wc_policy_no": wc_no.strip(),
                            "wc_insurer": wc_ins.strip(),
                            "wc_valid_till": str(wc_exp),
                            "wc_coverage": f"{labour_cap} Workers",
                            "wc_doc_file": f"WC_{clean_code}.pdf"
                        }
                        save_master_registry(reg)
                        st.success(f"✅ Site Code '{clean_code}' successfully created and saved!")
                        st.rerun()
                    else:
                        st.error("Please enter both Site Code and Site Name.")

        with c_action2:
            st.markdown("#### ✏️ Edit or 🗑️ Delete Existing Site Code")
            site_keys = list(reg['sites'].keys())
            if site_keys:
                edit_code = st.selectbox("Select Site Code to Edit or Delete", site_keys, key="sel_edit_site_prod")
                cur = reg['sites'][edit_code]
                
                with st.form("form_edit_site_prod"):
                    st.caption(f"Editing Site Code: **{edit_code}**")
                    e_name = st.text_input("Site / Project Name", value=cur.get('site_name', ''))
                    
                    ent_idx = list(reg['entities'].keys()).index(cur.get('entity_id')) if cur.get('entity_id') in reg['entities'] else 0
                    e_ent = st.selectbox("Operating Subsidiary", list(reg['entities'].keys()), index=ent_idx)
                    
                    client_idx = list(reg['clients'].keys()).index(cur.get('client_id')) if cur.get('client_id') in reg['clients'] else 0
                    e_client = st.selectbox("Client", list(reg['clients'].keys()), index=client_idx)
                    
                    po_idx = list(reg['pos'].keys()).index(cur.get('po_no')) if cur.get('po_no') in reg['pos'] else 0
                    e_po = st.selectbox("Purchase Order / PO", list(reg['pos'].keys()), index=po_idx)
                    
                    e_nature = st.text_input("Nature of Work", value=cur.get('nature_of_work', ''))
                    e_location = st.text_area("Site Location Address", value=cur.get('site_location', ''))
                    e_incharge = st.text_input("Site In-Charge", value=cur.get('site_incharge', 'Darshan Sir'))
                    
                    c_ec1, c_ec2 = st.columns(2)
                    with c_ec1:
                        e_cap = st.number_input("Max Labour Cap", min_value=1, max_value=5000, value=cur.get('labour_cap', 100))
                    with c_ec2:
                        e_hc = st.number_input("Active Deployed", min_value=0, max_value=5000, value=cur.get('active_headcount', 50))
                    
                    e_clra = st.text_input("CLRA License No", value=cur.get('clra_license_no', ''))
                    e_wc = st.text_input("WC Policy No", value=cur.get('wc_policy_no', ''))
                    
                    update_btn = st.form_submit_button("💾 Save Changes to Site Code", type="primary", use_container_width=True)
                    if update_btn:
                        reg['sites'][edit_code].update({
                            "site_name": e_name,
                            "entity_id": e_ent,
                            "client_id": e_client,
                            "po_no": e_po,
                            "nature_of_work": e_nature,
                            "site_location": e_location,
                            "site_incharge": e_incharge,
                            "labour_cap": int(e_cap),
                            "active_headcount": int(e_hc),
                            "clra_license_no": e_clra,
                            "wc_policy_no": e_wc
                        })
                        save_master_registry(reg)
                        st.success(f"✅ Site Code '{edit_code}' updated successfully!")
                        st.rerun()

                st.write("")
                st.markdown("##### 🚨 Safe Delete Protection")
                deployed_workers = cur.get('active_headcount', 0)
                
                if deployed_workers > 0:
                    st.warning(f"⚠️ **Protection Lock:** Site Code `{edit_code}` has **{deployed_workers} active workers deployed**. Direct delete is disabled to prevent orphan records in Salary/Offer Letters.")
                    confirm_force = st.checkbox(f"I understand the audit risk. Force delete site `{edit_code}` and de-link workers.", key="chk_force_del")
                    if st.button(f"🗑️ Force Delete Site Code '{edit_code}'", disabled=(not confirm_force), use_container_width=True):
                        del reg['sites'][edit_code]
                        save_master_registry(reg)
                        st.warning(f"Force-deleted Site Code '{edit_code}'.")
                        st.rerun()
                else:
                    if st.button(f"🗑️ Delete Site Code '{edit_code}' (0 Active Workers)", use_container_width=True, key="btn_clean_del"):
                        del reg['sites'][edit_code]
                        save_master_registry(reg)
                        st.success(f"Cleanly deleted empty Site Code '{edit_code}'.")
                        st.rerun()

    # TAB 2: UNIVERSAL DATA PULL SIMULATOR
    elif selected_nav == tab_options[1]:
        st.markdown("### ⚡ Universal Data-Pull Simulator & Headcount Guard")
        st.caption("Jab operator sirf **Site Code** select karega, toh system kaise legal data inherit karega aur CLRA capacity check karega:")
        
        sim_sites = list(reg['sites'].keys())
        sel_sim_site = st.selectbox("👉 Choose Site Code to Simulate Data Pull:", sim_sites, index=0, key="sel_sim_site_prod")
        
        s_obj = reg['sites'][sel_sim_site]
        e_obj = reg['entities'].get(s_obj.get('entity_id'), {})
        c_obj = reg['clients'].get(s_obj.get('client_id'), {})
        po_obj = reg['pos'].get(s_obj.get('po_no'), {})
        fv_obj = s_obj.get('form_v', {})
        
        cap = s_obj.get('labour_cap', 100)
        deployed = s_obj.get('active_headcount', 0)
        slots_left = cap - deployed
        
        if slots_left <= 0:
            st.error(f"🔴 **HEADCOUNT BREACH / LIMIT REACHED!** Deployed: {deployed}/{cap} workers. No new Offer Letters can be issued until Form VII CLRA Amendment is approved.")
        elif slots_left <= 10:
            st.warning(f"🟡 **CLRA CAPACITY WARNING:** Deployed: {deployed}/{cap} workers. Only **{slots_left} slots remaining** before license breach!")
        else:
            st.success(f"🟢 **CAPACITY SAFE:** Deployed: {deployed}/{cap} workers. **{slots_left} slots available** under CLRA Form XXI.")

        col_s1, col_s2 = st.columns([1, 1.3])
        
        with col_s1:
            e_logo_tag = get_logo_html(e_obj.get('logo_path'), e_obj.get('name', 'Contractor'), max_height=40, max_width=130)
            c_logo_tag = get_logo_html(c_obj.get('logo_path'), c_obj.get('short_name', 'Client'), max_height=40, max_width=130)
            st.markdown(f"""
            <div class="sim-payload-m">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed #CBD5E1; padding-bottom: 10px; margin-bottom: 12px;">
                    <div>{e_logo_tag}</div>
                    <div style="text-align: center; font-size: 10.5px; font-weight: 800; color: #64748B; letter-spacing: 0.5px;">CONTRACTOR &rarr; CLIENT</div>
                    <div>{c_logo_tag}</div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <strong style="color: #0F172A; font-size: 13.5px;">📦 Inherited Master Payload</strong>
                    <span class="status-badge-m badge-green-m">100% ZERO-TYPING</span>
                </div>
                <div style="font-size: 12.5px; line-height: 1.8;">
                    <div><b>Operating Firm:</b> <span style="color: #2563EB;">{e_obj.get('name')}</span></div>
                    <div><b>Company CIN:</b> {e_obj.get('cin')}</div>
                    <div><b>Master PF / ESIC:</b> <code>{e_obj.get('pf_code')}</code> / <code>{e_obj.get('esic_code')}</code></div>
                    <div><b>Client (PE):</b> <strong>{c_obj.get('name')}</strong></div>
                    <div><b>Principal Emp RC No:</b> <code>{c_obj.get('rc_no')}</code></div>
                    <div><b>Form V Certificate:</b> <code>{fv_obj.get('form_v_no', 'N/A')}</code> (Dated: {fv_obj.get('form_v_date', 'N/A')})</div>
                    <div><b>Client PO Number:</b> <code>{po_obj.get('po_no')}</code> (Valid till: {po_obj.get('valid_till')})</div>
                    <div><b>Nature of Work:</b> {s_obj.get('nature_of_work')}</div>
                    <div><b>CLRA Labour License:</b> <code>{s_obj.get('clra_license_no')}</code> (Cap: {cap} Workers)</div>
                    <div><b>Workmen Comp (WC):</b> <code>{s_obj.get('wc_policy_no')}</code> ({s_obj.get('wc_insurer', 'NIA')})</div>
                    <div><b>Work Location Address:</b> {s_obj.get('site_location')}</div>
                    <div><b>Authorized Signatory:</b> {e_obj.get('signatory_name')} ({e_obj.get('signatory_title')})</div>
                    <div><b>Site Compliance Head:</b> {s_obj.get('site_incharge')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_s2:
            st.markdown("#### 📄 How This Auto-Powers Other HRMS Modules:")
            
            m_tab1, m_tab2, m_tab3, m_tab4 = st.tabs([
                "🤝 Offer Letter", 
                "📄 Form XIX Wage Slip", 
                "📝 Appointment Letter",
                "📋 Form V & CLRA Audit Sheet"
            ])
            
            with m_tab1:
                st.markdown(f"""
                <div style="background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 10px; padding: 14px; font-size: 12px; line-height: 1.6;">
                    <strong>Candidate Offer Letter Auto-Draft:</strong><br>
                    "We are pleased to offer you employment with <b>{e_obj.get('name')}</b> for the position at 
                    <b>{c_obj.get('name')}</b> against Work Order <code>{po_obj.get('po_no')}</code>.<br>
                    Your primary site location will be <b>{s_obj.get('site_location')}</b> under 
                    CLRA License No: <code>{s_obj.get('clra_license_no')}</code>. Reporting to <b>{s_obj.get('site_incharge')}</b>."<br><br>
                    <i>CLRA Capacity Status:</i> {'🟢 Approved for Issuance' if slots_left > 0 else '🔴 Issuance Blocked (Limit Reached)'}<br>
                    <i>Authorized Signatory:</i> <b>{e_obj.get('signatory_name')}</b>
                </div>
                """, unsafe_allow_html=True)
                
            with m_tab2:
                st.markdown(f"""
                <div style="background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 10px; padding: 14px; font-size: 12px; line-height: 1.6;">
                    <strong>Form XIX Statutory Wage Slip Header (Labour Laws):</strong><br>
                    &bull; Name of Contractor: <b>{e_obj.get('name')}</b><br>
                    &bull; Principal Employer: <b>{c_obj.get('name')}</b> (RC No: <code>{c_obj.get('rc_no')}</code>)<br>
                    &bull; Nature and Location of Work: <b>{s_obj.get('nature_of_work')}</b>, {s_obj.get('site_location')}<br>
                    &bull; Establishment PF/ESIC: <code>{e_obj.get('pf_code')}</code> / <code>{e_obj.get('esic_code')}</code><br>
                    &bull; CLRA License No.: <code>{s_obj.get('clra_license_no')}</code>
                </div>
                """, unsafe_allow_html=True)
                
            with m_tab3:
                st.markdown(f"""
                <div style="background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 10px; padding: 14px; font-size: 12px; line-height: 1.6;">
                    <strong>Appointment Contract Agreement Clause:</strong><br>
                    Contract between <b>{e_obj.get('name')}</b> and Employee deployed at client site <b>{c_obj.get('name')}</b>.<br>
                    Governed by Principal Employer Form V <code>{fv_obj.get('form_v_no', 'N/A')}</code>, 
                    CLRA License <code>{s_obj.get('clra_license_no')}</code> and WC Policy <code>{s_obj.get('wc_policy_no')}</code>.<br>
                    <i>Statutory Insurance:</i> Covered under {s_obj.get('wc_insurer')} Policy No. <code>{s_obj.get('wc_policy_no')}</code>.
                </div>
                """, unsafe_allow_html=True)

            with m_tab4:
                st.markdown(f"""
                <div style="background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 10px; padding: 14px; font-size: 12px; line-height: 1.6;">
                    <strong>Form V & CLRA Audit Compliance Sheet:</strong><br>
                    &bull; <b>PE Certificate (Form V):</b> <code>{fv_obj.get('form_v_no', 'N/A')}</code> issued on {fv_obj.get('form_v_date', 'N/A')}<br>
                    &bull; <b>PE Signatory:</b> {fv_obj.get('issued_by', 'Principal Employer Contracts')}<br>
                    &bull; <b>Form V Approved Cap:</b> {fv_obj.get('pe_cap', cap)} Workers<br>
                    &bull; <b>CLRA License Form XXI No:</b> <code>{s_obj.get('clra_license_no')}</code> (Expiry: {s_obj.get('clra_valid_till')})<br>
                    &bull; <b>CLRA Amendment History:</b> {len(s_obj.get('clra_amendments', []))} revisions logged<br>
                    &bull; <b>Stamped Digital Copy:</b> <code>{s_obj.get('clra_doc_file', 'Pending Upload')}</code>
                </div>
                """, unsafe_allow_html=True)

    # TAB 3: STATUTORY EXPIRY RADAR & CERTIFICATE ARCHIVE
    elif selected_nav == tab_options[2]:
        st.markdown("### 🛡️ Statutory License Expiry Radar & Compliance Status ('Kon Active Hai')")
        st.caption("CLRA Form XXI, WC Policies, Form V, aur DISH Factory Licenses ka live status tracker aur Stamped Copy Archive:")
        
        radar_data = []
        for s_code, s_info in reg['sites'].items():
            clra_no = s_info.get('clra_license_no')
            clra_exp = s_info.get('clra_valid_till', '2026-12-31')
            clra_st = s_info.get('clra_status', 'active')
            wc_no = s_info.get('wc_policy_no')
            wc_exp = s_info.get('wc_valid_till', '2026-12-31')
            
            try:
                exp_d = datetime.datetime.strptime(clra_exp, "%Y-%m-%d").date()
                diff = (exp_d - today).days
                if clra_st == "renewal_submitted":
                    st_badge = "🔵 Renewal In-Process"
                    action_text = "📋 Challan Logged"
                elif diff < 0:
                    st_badge = f"🔴 Expired ({abs(diff)}d ago)"
                    action_text = "🚨 Urgent Renew"
                elif diff <= 60:
                    st_badge = f"🟡 Expiring ({diff}d left)"
                    action_text = "🔄 Submit Renewal"
                else:
                    st_badge = f"🟢 Active ({diff}d left)"
                    action_text = "👁️ View Copy"
            except Exception:
                st_badge = "🟢 Active"
                diff = 999
                action_text = "👁️ View Copy"
                
            radar_data.append({
                "Site Code": s_code,
                "Document Type": "Contract Labour Licence (CLRA Form XXI)",
                "License / Policy No": clra_no,
                "Permitted Limit": f"{s_info.get('labour_cap')} Workers",
                "Expiry Date": clra_exp,
                "Days Remaining": f"{diff} days" if diff != 999 else "N/A",
                "Validity Status": st_badge,
                "Action": action_text
            })
            
            try:
                exp_w = datetime.datetime.strptime(wc_exp, "%Y-%m-%d").date()
                diff_w = (exp_w - today).days
                if diff_w < 0:
                    st_badge_w = f"🔴 Expired ({abs(diff_w)}d ago)"
                    action_w = "🚨 Renew Policy"
                elif diff_w <= 60:
                    st_badge_w = f"🟡 Expiring ({diff_w}d left)"
                    action_w = "🔄 Renew Policy"
                else:
                    st_badge_w = f"🟢 Active ({diff_w}d left)"
                    action_w = "👁️ View Copy"
            except Exception:
                st_badge_w = "🟢 Active"
                diff_w = 999
                action_w = "👁️ View Copy"
                
            radar_data.append({
                "Site Code": s_code,
                "Document Type": "Workmen's Compensation (WC Policy)",
                "License / Policy No": wc_no,
                "Permitted Limit": f"{s_info.get('labour_cap')} Workers",
                "Expiry Date": wc_exp,
                "Days Remaining": f"{diff_w} days" if diff_w != 999 else "N/A",
                "Validity Status": st_badge_w,
                "Action": action_w
            })

        filter_val = st.radio(
            "Filter Compliance Status:", 
            ["All Documents", "🟢 Active Only", "🟡 Expiring Soon (<60 Days)", "🔵 Renewal In-Process", "🔴 Expired Only"], 
            horizontal=True,
            key="rad_filter_prod"
        )
        
        filtered_radar = radar_data
        if "Active" in filter_val:
            filtered_radar = [x for x in radar_data if "🟢" in x['Validity Status']]
        elif "Expiring" in filter_val:
            filtered_radar = [x for x in radar_data if "🟡" in x['Validity Status']]
        elif "Renewal" in filter_val:
            filtered_radar = [x for x in radar_data if "🔵" in x['Validity Status']]
        elif "Expired" in filter_val:
            filtered_radar = [x for x in radar_data if "🔴" in x['Validity Status']]
            
        st.dataframe(filtered_radar, use_container_width=True)

        st.markdown("---")
        r_col1, r_col2 = st.columns([1.2, 1])

        with r_col1:
            st.markdown("#### 👁️ Stamped Statutory Document Archive & Certificate Viewer")
            st.write("Darshan sir client HR audit ya ALC inspection ke waqt stamped copy yahan se direct preview kar sakte hain:")
            
            sel_view_site = st.selectbox("Select Site to View Stamped Certificate:", list(reg['sites'].keys()), key="sel_cert_site_prod")
            s_v = reg['sites'][sel_view_site]
            e_v = reg['entities'].get(s_v.get('entity_id'), {})
            c_v = reg['clients'].get(s_v.get('client_id'), {})
            
            doc_choice = st.radio("Choose Document to Inspect:", ["CLRA Form XXI Labour License (Govt. of Gujarat)", "Workmen's Compensation Policy Schedule"], horizontal=True, key="rad_doc_choice_prod")
            
            if "CLRA" in doc_choice:
                st.markdown(f"""
                <div class="cert-preview-box-m">
                    <div style="text-align: center; border-bottom: 2px solid #92400E; padding-bottom: 10px; margin-bottom: 14px;">
                        <div style="font-size: 13px; font-weight: bold; letter-spacing: 1px; color: #78350F;">GOVERNMENT OF GUJARAT &bull; LABOUR & EMPLOYMENT DEPARTMENT</div>
                        <div style="font-size: 16px; font-weight: bold; color: #1E293B; margin-top: 4px;">OFFICE OF THE LICENSING OFFICER & ASSISTANT LABOUR COMMISSIONER, KUTCH</div>
                        <div style="font-size: 12px; font-style: italic; color: #64748B;">Form XXI [See Rule 25(1)] — LICENCE UNDER THE CONTRACT LABOUR (R&A) ACT, 1970</div>
                    </div>
                    <div style="font-size: 13px; line-height: 1.8; color: #0F172A;">
                        <div><b>Licence Number:</b> <code style="font-size: 14px; color: #B45309; font-weight: bold;">{s_v.get('clra_license_no')}</code></div>
                        <div><b>Date of Issue:</b> 01-Jan-2026 &nbsp;|&nbsp; <b>Valid Until:</b> <span style="color: #DC2626; font-weight: bold;">{s_v.get('clra_valid_till')}</span></div>
                        <div><b>Name of Contractor:</b> <b>{e_v.get('name')}</b></div>
                        <div><b>Principal Employer:</b> <b>{c_v.get('name')}</b> (RC No: <code>{c_v.get('rc_no')}</code>)</div>
                        <div><b>Site / Nature of Work:</b> {s_v.get('nature_of_work')} at {s_v.get('site_location')}</div>
                        <div><b>Maximum Permitted Labour Cap:</b> <span style="background: #FEF3C7; padding: 2px 8px; border-radius: 6px; font-weight: bold;">{s_v.get('labour_cap')} WORKERS ONLY</span></div>
                    </div>
                    <div style="margin-top: 20px; display: flex; justify-content: space-between; align-items: flex-end;">
                        <div style="border: 1px dashed #64748B; padding: 6px 12px; font-size: 10px; border-radius: 6px; color: #475569;">
                            [OFFICIAL DIGITAL STAMP & QR]<br>
                            Govt of Gujarat Portal Verified
                        </div>
                        <div style="text-align: right; font-size: 12px;">
                            <b>Sd/-</b><br>
                            Licensing Officer & ALC<br>
                            Kutch Division, Gandhidham
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="cert-preview-box-m">
                    <div style="text-align: center; border-bottom: 2px solid #1E40AF; padding-bottom: 10px; margin-bottom: 14px;">
                        <div style="font-size: 14px; font-weight: bold; color: #1E40AF;">{s_v.get('wc_insurer', 'THE NEW INDIA ASSURANCE CO. LTD.')}</div>
                        <div style="font-size: 15px; font-weight: bold; color: #0F172A;">EMPLOYEES' COMPENSATION INSURANCE POLICY SCHEDULE</div>
                    </div>
                    <div style="font-size: 13px; line-height: 1.8; color: #0F172A;">
                        <div><b>Policy Number:</b> <code style="font-size: 14px; color: #1D4ED8; font-weight: bold;">{s_v.get('wc_policy_no')}</code></div>
                        <div><b>Insured Name:</b> <b>{e_v.get('name')}</b></div>
                        <div><b>Principal Employer:</b> {c_v.get('name')}</div>
                        <div><b>Risk Location:</b> {s_v.get('site_location')}</div>
                        <div><b>Covered Workers:</b> {s_v.get('labour_cap')} Deployed Workmen &bull; <b>Valid Till:</b> {s_v.get('wc_valid_till')}</div>
                    </div>
                    <div style="margin-top: 15px; text-align: right; font-size: 11px; color: #475569;">
                        <b>Authorized Insurer Stamp & Seal</b> &bull; Premium Paid in Full
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with r_col2:
            st.markdown("#### 🔄 Statutory Renewal & Challan Logger")
            st.write("Jab ALC office me renewal file ya government treasury challan bhara jaye, toh status yahan se update karein:")
            
            with st.form("form_log_renewal_prod"):
                ren_site = st.selectbox("Site Code for Renewal", list(reg['sites'].keys()), key="sel_ren_site_prod")
                cur_s = reg['sites'][ren_site]
                
                st.caption(f"Current CLRA: **{cur_s.get('clra_license_no')}** (Exp: {cur_s.get('clra_valid_till')})")
                
                n_challan = st.text_input("Govt. Treasury Challan Reference No.", placeholder="e.g. GJ-TREASURY-CHALLAN-992144")
                n_challan_date = st.date_input("Challan Payment Date", value=today, key="ren_date_prod")
                n_status = st.selectbox("Renewal Stage", [
                    "renewal_submitted (Challan Paid & Submitted to ALC)",
                    "active (Approved & New License Issued)",
                    "expiring_soon (Pending Submission)"
                ], key="ren_stage_prod")
                n_extended_date = st.date_input("New Extended Expiry Date (if renewed)", value=today + datetime.timedelta(days=365), key="ren_exp_prod")
                
                submit_ren = st.form_submit_button("💾 Save Statutory Renewal Stage", type="primary", use_container_width=True)
                if submit_ren:
                    clean_status = n_status.split()[0]
                    reg['sites'][ren_site]['clra_status'] = clean_status
                    reg['sites'][ren_site]['clra_challan_ref'] = n_challan.strip()
                    if clean_status == "active":
                        reg['sites'][ren_site]['clra_valid_till'] = str(n_extended_date)
                    save_master_registry(reg)
                    st.success(f"✅ Renewal stage updated for Site '{ren_site}'!")
                    st.rerun()

    # TAB 4: GROUP SUBSIDIARIES, CLIENTS & PO DIRECTORY
    elif selected_nav == tab_options[3]:
        st.markdown("### 🏢 Level 1 & 2: Group Entities, Clients & Client PO Directory")
        
        can_manage = has_permission("can_manage_master_licenses")
        can_delete = has_permission("can_delete_master_entities")
        
        if not can_manage:
            render_permission_guard("can_manage_master_licenses", "Manage Master Entities, Clients, POs & Licenses")
            st.info("ℹ️ Your role is authorized to view master data in Read-Only mode. Registering new subsidiaries, modifying client records, or deleting work orders is restricted to Compliance Heads and Super Admins.")
            
            # Read-only summary tables
            st.markdown("#### 🏢 Active Group Subsidiaries")
            ent_summary = [{"Entity ID": k, "Legal Name": v.get('name'), "CIN": v.get('cin'), "GSTIN": v.get('gstin'), "PF Code": v.get('pf_code')} for k, v in reg.get('entities', {}).items()]
            st.dataframe(pd.DataFrame(ent_summary), use_container_width=True)
            
            st.markdown("#### 🤝 Principal Employers (Clients)")
            cl_summary = [{"Client ID": k, "Client Name": v.get('name'), "Short Name": v.get('short_name'), "RC Number": v.get('rc_no'), "Location": v.get('location')} for k, v in reg.get('clients', {}).items()]
            st.dataframe(pd.DataFrame(cl_summary), use_container_width=True)
            return

        st.caption("Aap yahan se kisi bhi company, client ya PO ko edit kar sakte hain ya galat ban gaya ho toh delete kar sakte hain:")
        
        sub_opts = [
            "🏢 1. Group Subsidiary Entities", 
            "🤝 2. Principal Employers (Clients)", 
            "📑 3. Client Work Orders & POs"
        ]
        
        sub_param = st.query_params.get("sec")
        if sub_param:
            if sub_param in ["1", "entities"]: st.session_state["rad_dir_sec_prod"] = sub_opts[0]
            elif sub_param in ["2", "clients"]: st.session_state["rad_dir_sec_prod"] = sub_opts[1]
            elif sub_param in ["3", "pos"]: st.session_state["rad_dir_sec_prod"] = sub_opts[2]

        selected_sub4 = st.radio("Directory Section", sub_opts, horizontal=True, label_visibility="collapsed", key="rad_dir_sec_prod")
        st.write("")
        
        if selected_sub4 == sub_opts[0]:
            st.markdown("#### 🏢 Group Subsidiaries Master (Companies & Brand Logos)")
            st.caption("Aap yahan se subsidiaries create kar sakte hain, existing companies ko edit kar sakte hain, aur har company ka official logo upload/update kar sakte hain:")
            
            sub_col1, sub_col2 = st.columns([1.3, 1])
            
            with sub_col1:
                st.markdown("##### ✏️ Edit Subsidiaries & Brand Logos")
                for idx, (e_id, e_val) in enumerate(reg['entities'].items()):
                    with st.expander(f"🏢 {e_id} — {e_val.get('name')}", expanded=(idx == 0)):
                        # Logo row
                        l_c1, l_c2 = st.columns([1, 2])
                        with l_c1:
                            logo_p = e_val.get('logo_path', f'assets/logos/entities/{e_id}.png')
                            st.caption("Current Company Logo:")
                            st.html(get_logo_html(logo_p, e_id, max_height=55, max_width=140))
                        with l_c2:
                            new_logo = st.file_uploader(f"Upload New Logo for {e_id}", type=['png', 'jpg', 'jpeg', 'webp'], key=f"upl_e_logo_{e_id}")
                            if new_logo:
                                os.makedirs("assets/logos/entities", exist_ok=True)
                                ext = os.path.splitext(new_logo.name)[1].lower() or ".png"
                                target_save = f"assets/logos/entities/{e_id}{ext}"
                                with open(target_save, "wb") as f_out:
                                    f_out.write(new_logo.getbuffer())
                                reg['entities'][e_id]['logo_path'] = target_save
                                save_master_registry(reg)
                                st.success(f"Logo uploaded for {e_id}!")
                                st.rerun()

                        with st.form(f"form_e_prod_{e_id}"):
                            c1, c2 = st.columns(2)
                            with c1:
                                n_name = st.text_input("Entity Registered Legal Name", value=e_val.get('name'))
                                n_cin = st.text_input("CIN / Incorporation No", value=e_val.get('cin'))
                                n_gst = st.text_input("GSTIN Number", value=e_val.get('gstin'))
                            with c2:
                                n_pf = st.text_input("Master PF Establishment Code", value=e_val.get('pf_code'))
                                n_esic = st.text_input("Master ESIC Code", value=e_val.get('esic_code'))
                                n_sig = st.text_input("Authorized Signatory Name", value=e_val.get('signatory_name'))
                                n_sig_title = st.text_input("Signatory Designation", value=e_val.get('signatory_title', 'Authorized Signatory'))
                            n_addr = st.text_area("Registered Office Address", value=e_val.get('address'))
                            
                            if st.form_submit_button("💾 Save Entity Changes", type="primary"):
                                reg['entities'][e_id].update({
                                    "name": n_name, "cin": n_cin, "gstin": n_gst,
                                    "pf_code": n_pf, "esic_code": n_esic,
                                    "address": n_addr, "signatory_name": n_sig,
                                    "signatory_title": n_sig_title
                                })
                                save_master_registry(reg)
                                st.success(f"✅ Entity {e_id} updated successfully!")
                                st.rerun()

                        # Safe Delete Entity
                        linked_s = [sc for sc, s in reg.get('sites', {}).items() if s.get('entity_id') == e_id]
                        if linked_s:
                            st.caption(f"🔒 Cannot delete: Linked to {len(linked_s)} site(s) (`{', '.join(linked_s)}`)")
                        else:
                            if st.button(f"🗑️ Delete Entity '{e_id}'", key=f"del_e_prod_{e_id}"):
                                del reg['entities'][e_id]
                                save_master_registry(reg)
                                st.warning(f"Deleted entity '{e_id}'.")
                                st.rerun()

            with sub_col2:
                st.markdown("##### ➕ Register New Group Subsidiary Entity")
                with st.form("form_add_new_entity_prod"):
                    new_e_id = st.text_input("Entity ID / Short Code", placeholder="e.g. SHREE_RAM")
                    new_e_name = st.text_input("Registered Legal Name", placeholder="e.g. SHREE RAM ENTERPRISES")
                    new_e_cin = st.text_input("CIN or Registration No.", placeholder="e.g. U28112GJ2026PTC...")
                    new_e_gst = st.text_input("GSTIN Number", placeholder="e.g. 24AAAFX1234D1Z8")
                    new_e_pf = st.text_input("Master PF Code", placeholder="e.g. GJRJK9988776000")
                    new_e_esic = st.text_input("Master ESIC Code", placeholder="e.g. 37000554430000001")
                    new_e_sig = st.text_input("Signatory Name", placeholder="e.g. Tarun Swami")
                    new_e_title = st.text_input("Signatory Designation", placeholder="e.g. Managing Director")
                    new_e_addr = st.text_area("Registered Office Address", placeholder="Registered corporate address")
                    new_e_logo = st.file_uploader("Upload Company Logo (PNG/JPG)", type=['png', 'jpg', 'jpeg', 'webp'], key="upl_new_e_logo")

                    submit_new_e = st.form_submit_button("➕ Create Group Entity", type="primary", use_container_width=True)
                    if submit_new_e:
                        if new_e_id.strip() and new_e_name.strip():
                            clean_eid = new_e_id.strip().upper().replace(" ", "_")
                            logo_target = f"assets/logos/entities/{clean_eid}.png"
                            if new_e_logo:
                                os.makedirs("assets/logos/entities", exist_ok=True)
                                ext = os.path.splitext(new_e_logo.name)[1].lower() or ".png"
                                logo_target = f"assets/logos/entities/{clean_eid}{ext}"
                                with open(logo_target, "wb") as f_out:
                                    f_out.write(new_e_logo.getbuffer())
                            
                            reg['entities'][clean_eid] = {
                                "id": clean_eid,
                                "name": new_e_name.strip(),
                                "cin": new_e_cin.strip(),
                                "gstin": new_e_gst.strip(),
                                "pf_code": new_e_pf.strip(),
                                "esic_code": new_e_esic.strip(),
                                "address": new_e_addr.strip(),
                                "signatory_name": new_e_sig.strip(),
                                "signatory_title": new_e_title.strip() or "Authorized Signatory",
                                "logo_path": logo_target
                            }
                            save_master_registry(reg)
                            st.success(f"✅ Entity '{clean_eid}' created successfully!")
                            st.rerun()
                        else:
                            st.error("Please enter Entity ID and Registered Name.")

        elif selected_sub4 == sub_opts[1]:
            st.markdown("#### 🤝 Clients / Principal Employers (PE & Client Logos)")
            st.caption("Aap yahan se naye client add kar sakte hain, client details edit kar sakte hain, aur har client ka logo upload kar sakte hain:")
            
            cl_col1, cl_col2 = st.columns([1.3, 1])
            
            with cl_col1:
                st.markdown("##### ✏️ Edit Clients & Client Logos")
                cl_items = list(reg.get('clients', {}).items())
                for idx, (c_id, c_val) in enumerate(cl_items):
                    with st.expander(f"🤝 {c_val.get('name')}", expanded=(idx == 0)):
                        # Logo row
                        cl_l1, cl_l2 = st.columns([1, 2])
                        with cl_l1:
                            logo_p = c_val.get('logo_path', f'assets/logos/clients/{c_id}.png')
                            st.caption("Client Brand Logo:")
                            st.html(get_logo_html(logo_p, c_val.get('short_name', c_id), max_height=55, max_width=140))
                        with cl_l2:
                            new_c_logo = st.file_uploader(f"Upload Logo for {c_id}", type=['png', 'jpg', 'jpeg', 'webp'], key=f"upl_c_logo_{c_id}")
                            if new_c_logo:
                                os.makedirs("assets/logos/clients", exist_ok=True)
                                ext = os.path.splitext(new_c_logo.name)[1].lower() or ".png"
                                target_save = f"assets/logos/clients/{c_id}{ext}"
                                with open(target_save, "wb") as f_out:
                                    f_out.write(new_c_logo.getbuffer())
                                reg['clients'][c_id]['logo_path'] = target_save
                                save_master_registry(reg)
                                st.success(f"Logo uploaded for Client {c_id}!")
                                st.rerun()

                        with st.form(f"form_c_prod_{c_id}"):
                            cn_name = st.text_input("Principal Employer Full Name", value=c_val.get('name'))
                            cn_short = st.text_input("Short Name / Code", value=c_val.get('short_name', c_id))
                            cn_rc = st.text_input("Principal Employer RC No", value=c_val.get('rc_no', ''))
                            cn_contact = st.text_input("Contact Person", value=c_val.get('contact_person', ''))
                            cn_loc = st.text_area("Client Plant / Site Address", value=c_val.get('location', ''))
                            
                            c_save = st.form_submit_button("💾 Save Client Details", type="primary")
                            if c_save:
                                reg['clients'][c_id].update({
                                    "name": cn_name,
                                    "short_name": cn_short,
                                    "rc_no": cn_rc,
                                    "contact_person": cn_contact,
                                    "location": cn_loc
                                })
                                save_master_registry(reg)
                                st.success(f"✅ Client '{c_id}' updated!")
                                st.rerun()
                        
                        linked_cs = [sc for sc, s in reg.get('sites', {}).items() if s.get('client_id') == c_id]
                        if linked_cs:
                            st.caption(f"🔒 Cannot delete: Linked to {len(linked_cs)} site(s) (`{', '.join(linked_cs)}`)")
                        else:
                            if st.button(f"🗑️ Delete Client '{c_id}'", key=f"del_c_prod_{c_id}"):
                                del reg['clients'][c_id]
                                save_master_registry(reg)
                                st.warning(f"Deleted Client '{c_id}'.")
                                st.rerun()
                            
            with cl_col2:
                st.markdown("##### ➕ Add New Client & Logo")
                with st.form("form_add_new_client_prod"):
                    new_c_id = st.text_input("Client ID / Key", placeholder="e.g. ULTRA_TECH")
                    new_c_name = st.text_input("Principal Employer Legal Name", placeholder="e.g. ULTRATECH CEMENT LIMITED")
                    new_c_short = st.text_input("Short Display Name", placeholder="e.g. UltraTech Kutch")
                    new_c_rc = st.text_input("Principal Employer RC Number", placeholder="e.g. RC-UTC-2026-99")
                    new_c_contact = st.text_input("Contact Person / Manager", placeholder="e.g. Mr. H. Mehta (HR Head)")
                    new_c_loc = st.text_area("Client Works Location", placeholder="Plant location address")
                    new_client_logo = st.file_uploader("Upload Client Logo (PNG/JPG)", type=['png', 'jpg', 'jpeg', 'webp'], key="upl_new_client_logo")
                    
                    add_c_btn = st.form_submit_button("➕ Register Client", type="primary", use_container_width=True)
                    if add_c_btn:
                        if new_c_id.strip() and new_c_name.strip():
                            c_key = new_c_id.strip().upper().replace(" ", "_")
                            logo_target = f"assets/logos/clients/{c_key}.png"
                            if new_client_logo:
                                os.makedirs("assets/logos/clients", exist_ok=True)
                                ext = os.path.splitext(new_client_logo.name)[1].lower() or ".png"
                                logo_target = f"assets/logos/clients/{c_key}{ext}"
                                with open(logo_target, "wb") as f_out:
                                    f_out.write(new_client_logo.getbuffer())
                            
                            reg['clients'][c_key] = {
                                "id": c_key,
                                "name": new_c_name.strip(),
                                "short_name": new_c_short.strip(),
                                "rc_no": new_c_rc.strip(),
                                "contact_person": new_c_contact.strip(),
                                "contact_email": "",
                                "location": new_c_loc.strip(),
                                "logo_path": logo_target
                            }
                            save_master_registry(reg)
                            st.success(f"✅ Client '{c_key}' added!")
                            st.rerun()
                        else:
                            st.error("Please enter Client ID and Legal Name.")

        elif selected_sub4 == sub_opts[2]:
            st.markdown("#### 📑 Purchase Orders / Work Orders (PO)")
            po_col1, po_col2 = st.columns([1.2, 1])
            
            with po_col1:
                st.markdown("##### ✏️ Edit or 🗑️ Delete Existing POs")
                po_items = list(reg.get('pos', {}).items())
                for idx, (po_id, po_val) in enumerate(po_items):
                    c_name = reg['clients'].get(po_val.get('client_id'), {}).get('short_name', po_val.get('client_id'))
                    with st.expander(f"📑 {po_id} ({c_name})", expanded=(idx == 0)):
                        with st.form(f"form_po_prod_{po_id}"):
                            po_title = st.text_input("PO Title / Work Scope", value=po_val.get('title'))
                            
                            all_c_keys = list(reg['clients'].keys())
                            cur_c_idx = all_c_keys.index(po_val.get('client_id')) if po_val.get('client_id') in all_c_keys else 0
                            po_client = st.selectbox("Associated Client", all_c_keys, index=cur_c_idx, key=f"sel_cl_prod_{po_id}")
                            
                            cp1, cp2 = st.columns(2)
                            with cp1:
                                po_vfrom = st.date_input("Valid From", value=datetime.datetime.strptime(po_val.get('valid_from'), "%Y-%m-%d").date(), key=f"vf_prod_{po_id}")
                            with cp2:
                                po_vtill = st.date_input("Valid Till", value=datetime.datetime.strptime(po_val.get('valid_till'), "%Y-%m-%d").date(), key=f"vt_prod_{po_id}")
                                
                            po_cap = st.number_input("Allocated Headcount Limit", value=po_val.get('allocated_headcount', 100), key=f"cap_prod_{po_id}")
                            
                            if st.form_submit_button("💾 Save PO Changes", type="primary"):
                                reg['pos'][po_id].update({
                                    "title": po_title,
                                    "client_id": po_client,
                                    "valid_from": str(po_vfrom),
                                    "valid_till": str(po_vtill),
                                    "allocated_headcount": int(po_cap)
                                })
                                save_master_registry(reg)
                                st.success(f"✅ PO {po_id} updated!")
                                st.rerun()
                                
                        if st.button(f"🗑️ Delete PO '{po_id}'", key=f"del_po_prod_{po_id}"):
                            del reg['pos'][po_id]
                            save_master_registry(reg)
                            st.warning(f"Deleted PO '{po_id}'.")
                            st.rerun()
                            
            with po_col2:
                st.markdown("##### ➕ Add New Work Order / PO")
                with st.form("form_add_new_po_prod"):
                    new_po_no = st.text_input("PO Number", placeholder="e.g. PO-ADANI-2026-990")
                    new_po_title = st.text_input("PO Scope / Title", placeholder="e.g. Piping & Fabrication Unit 4")
                    
                    cl_options = list(reg['clients'].keys())
                    new_po_cl = st.selectbox("Client", cl_options, format_func=lambda x: reg['clients'][x]['name'])
                    
                    c_pfrom, c_ptill = st.columns(2)
                    with c_pfrom:
                        new_po_vfrom = st.date_input("Start Date", value=datetime.date.today(), key="n_po_vf_prod")
                    with c_ptill:
                        new_po_vtill = st.date_input("Expiry Date", value=datetime.date.today() + datetime.timedelta(days=365), key="n_po_vt_prod")
                    
                    new_po_hc = st.number_input("Approved Manpower Cap", min_value=1, max_value=5000, value=100)
                    
                    add_po_btn = st.form_submit_button("➕ Register Purchase Order", type="primary", use_container_width=True)
                    if add_po_btn:
                        if new_po_no.strip() and new_po_title.strip():
                            po_clean = new_po_no.strip().upper()
                            reg['pos'][po_clean] = {
                                "po_no": po_clean,
                                "client_id": new_po_cl,
                                "title": new_po_title.strip(),
                                "valid_from": str(new_po_vfrom),
                                "valid_till": str(new_po_vtill),
                                "allocated_headcount": int(new_po_hc)
                            }
                            save_master_registry(reg)
                            st.success(f"✅ Purchase Order '{po_clean}' registered!")
                            st.rerun()
                        else:
                            st.error("Please enter PO Number and Title.")
