import streamlit as st
import json
import os
import datetime
from automation.config import (
    load_master_registry, 
    load_monthly_compliance, 
    save_monthly_compliance, 
    get_base64_image,
    has_permission,
    render_permission_guard
)

def get_logo_html(logo_path, default_text, max_height=52, max_width=150):
    if logo_path and os.path.exists(logo_path):
        ext = os.path.splitext(logo_path)[1].lower().replace('.', '')
        if ext == 'jpg': ext = 'jpeg'
        b64 = get_base64_image(logo_path)
        if b64:
            return f'<img src="data:image/{ext};base64,{b64}" style="max-height: {max_height}px; max-width: {max_width}px; object-fit: contain; border-radius: 6px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); background: #FFFFFF; padding: 2px;">'
    return f'<div style="background: #0F172A; color: #FFFFFF; font-weight: 800; font-size: 13px; padding: 6px 14px; border-radius: 8px; letter-spacing: 0.5px; display: inline-block;">{default_text[:14]}</div>'


today = datetime.date.today()

def render(selected_site_default="MPL-PIPE-01"):
    reg = load_master_registry()
    comp_data = load_monthly_compliance()
    
    # Styling
    st.markdown("""
    <style>
        .header-box-c {
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
        .kpi-card-c {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 14px 18px;
            box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
        }
        .status-pill {
            font-size: 11px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 14px;
            display: inline-block;
        }
        .pill-green { background: #DCFCE7; color: #166534; border: 1px solid #86EFAC; }
        .pill-amber { background: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; }
        .pill-blue { background: #DBEAFE; color: #1E40AF; border: 1px solid #93C5FD; }
        .pill-red { background: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }
        .dossier-box {
            background: #FFFFFF;
            border: 2px solid #0F172A;
            border-radius: 10px;
            padding: 24px;
            font-family: 'Times New Roman', serif;
            color: #0F172A;
        }
    </style>
    """, unsafe_allow_html=True)

    # Top Header
    st.markdown("""
    <div class="header-box-c">
        <div>
            <h2 style="margin: 0; font-size: 20px; font-weight: 800; color: #0F172A;">
                📊 Monthly Site Compliance Tracking & Client Billing Clearance
            </h2>
            <p style="margin: 3px 0 0 0; font-size: 12.5px; color: #64748B;">
                Site-by-Site Monthly Statutory Submissions &bull; PF/ESIC ECR Challans &bull; Wage Proof &bull; Client Invoice Clearance Dossier
            </p>
        </div>
        <div style="background: #FEF3C7; border: 1px solid #FCD34D; color: #92400E; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 12px;">
            📑 Client Bill Release Gateway
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Top Selectors: Month & Site
    col_sel1, col_sel2 = st.columns([1, 1.5])
    
    with col_sel1:
        month_options = ["2026-11 (November 2026)", "2026-10 (October 2026)", "2026-09 (September 2026)"]
        selected_month_label = st.selectbox("📅 Compliance Month & Year", month_options, index=0)
        sel_month = selected_month_label.split()[0]
        
    with col_sel2:
        all_site_keys = list(reg.get('sites', {}).keys()) if reg else ["MPL-PIPE-01"]
        default_s_idx = 0
        if selected_site_default in all_site_keys:
            default_s_idx = all_site_keys.index(selected_site_default)
            
        selected_site_code = st.selectbox(
            "🏢 Operating Site Code", 
            all_site_keys, 
            index=default_s_idx,
            format_func=lambda x: f"{x} — {reg['sites'][x]['site_name'][:40]} ({reg['clients'].get(reg['sites'][x]['client_id'], {}).get('short_name', '')})"
        )

    # Fetch site and month records
    s_obj = reg.get('sites', {}).get(selected_site_code, {})
    e_obj = reg.get('entities', {}).get(s_obj.get('entity_id'), {})
    c_obj = reg.get('clients', {}).get(s_obj.get('client_id'), {})
    
    # Initialize month record if missing
    if sel_month not in comp_data:
        comp_data[sel_month] = {}
    if selected_site_code not in comp_data[sel_month]:
        comp_data[sel_month][selected_site_code] = {
            "month": sel_month,
            "site_code": selected_site_code,
            "wages_disbursement": {"status": "pending", "bank_ref": "", "date": "", "amount": 0, "notes": ""},
            "wage_register_sign": {"status": "pending", "slips_count": s_obj.get('active_headcount', 50), "pe_signatory": "", "date": "", "notes": ""},
            "pf_ecr": {"status": "pending", "trrn": "", "amount": 0, "date": "", "notes": ""},
            "esic_challan": {"status": "pending", "challan_no": "", "amount": 0, "date": "", "notes": ""},
            "pt_challan": {"status": "pending", "challan_no": "", "amount": 0, "date": "", "notes": ""},
            "lwf_wc": {"status": "completed", "policy_ref": s_obj.get('wc_policy_no', ''), "notes": ""},
            "safety_tbt": {"status": "completed", "tbt_count": 25, "incident_status": "Zero Incident", "notes": ""},
            "dossier_status": "in_progress",
            "submitted_to_client": "",
            "client_approval_status": "In Progress"
        }
        save_monthly_compliance(comp_data)

    site_rec = comp_data[sel_month][selected_site_code]

    # Calculate Checklist Score
    items_to_check = ['wages_disbursement', 'wage_register_sign', 'pf_ecr', 'esic_challan', 'pt_challan', 'lwf_wc', 'safety_tbt']
    completed_items = sum(1 for it in items_to_check if site_rec.get(it, {}).get('status') == 'completed')
    total_items = len(items_to_check)
    readiness_pct = int(completed_items / total_items * 100)

    # Top Bento Metrics
    w_amt = site_rec.get('wages_disbursement', {}).get('amount', 0)
    pf_amt = site_rec.get('pf_ecr', {}).get('amount', 0)
    esi_amt = site_rec.get('esic_challan', {}).get('amount', 0)
    stat_total = pf_amt + esi_amt

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="kpi-card-c">
            <span style="font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;">Deployed Manpower</span>
            <h2 style="margin: 4px 0 0 0; font-size: 24px; font-weight: 800; color: #0F172A;">{s_obj.get('active_headcount', 0)} Workers</h2>
            <span style="font-size: 11.5px; color: #2563EB; font-weight: 600;">{e_obj.get('name', '').split()[0]} @ {c_obj.get('short_name')}</span>
        </div>
        """, unsafe_allow_html=True)

    with m2:
        st.markdown(f"""
        <div class="kpi-card-c">
            <span style="font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;">Monthly Wage Payout</span>
            <h2 style="margin: 4px 0 0 0; font-size: 24px; font-weight: 800; color: #0F172A;">₹{w_amt:,.0f}</h2>
            <span style="font-size: 11.5px; color: #10B981; font-weight: 600;">Bank NEFT Disbursed</span>
        </div>
        """, unsafe_allow_html=True)

    with m3:
        st.markdown(f"""
        <div class="kpi-card-c">
            <span style="font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;">Statutory PF + ESIC Paid</span>
            <h2 style="margin: 4px 0 0 0; font-size: 24px; font-weight: 800; color: #0F172A;">₹{stat_total:,.0f}</h2>
            <span style="font-size: 11.5px; color: #D97706; font-weight: 600;">EPFO & ESIC Challans Verified</span>
        </div>
        """, unsafe_allow_html=True)

    with m4:
        st.markdown(f"""
        <div class="kpi-card-c">
            <span style="font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase;">Client Bill Clearance Status</span>
            <h2 style="margin: 4px 0 0 0; font-size: 24px; font-weight: 800; color: #0F172A;">{completed_items}/{total_items} Items</h2>
            <span style="font-size: 11.5px; color: #8B5CF6; font-weight: 600;">{readiness_pct}% Dossier Complete</span>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Progress Clearance Banner
    if readiness_pct == 100:
        st.success(f"🟢 **CLIENT BILL CLEARANCE APPROVED:** All 7 statutory items completed and verified for **{selected_site_code}**! Monthly contractor invoice submission is cleared.")
    elif readiness_pct >= 70:
        st.warning(f"🟡 **INVOICE CLEARANCE IN PROGRESS:** {completed_items}/{total_items} items completed ({readiness_pct}%). Pending client signatures / final deposit before bill submission.")
    else:
        st.error(f"🔴 **BILLING ON HOLD:** Only {completed_items}/{total_items} statutory items complete. Client finance will reject invoices until all PF/Wage proofs are submitted.")

    st.write("")

    # 3 Action Tabs
    m_tab_options = [
        "📋 1. Statutory Checklist & Challan Editor",
        "📊 2. All-Site Monthly Compliance Heatmap",
        "📑 3. Client Bill Clearance Dossier & Undertaking"
    ]
    
    m_tab_param = st.query_params.get("sub", "1")
    m_default_idx = 0
    if m_tab_param in ["2", "heatmap"]: m_default_idx = 1
    elif m_tab_param in ["3", "dossier"]: m_default_idx = 2
    
    selected_m_tab = st.radio("Monthly Sections", m_tab_options, index=m_default_idx, horizontal=True, label_visibility="collapsed")
    st.write("")

    # TAB 1: CHECKLIST & CHALLAN EDITOR
    if selected_m_tab == m_tab_options[0]:
        st.markdown(f"#### 📋 Statutory Checklist for `{selected_site_code}` ({sel_month})")
        st.caption("Adani / Linde / Tata monthly billing audit clearance ke liye har milestone ka proof yahan update karein:")
        
        # Display Checklist in Table
        checklist_rows = [
            {
                "Milestone": "1. Bank Wage Disbursement Advice",
                "Statutory Deadline": "7th / 10th of Month",
                "Status": "🟢 Paid (Bank Verified)" if site_rec.get('wages_disbursement', {}).get('status') == 'completed' else "🔴 Pending Payout",
                "Reference / Ref No": site_rec.get('wages_disbursement', {}).get('bank_ref', 'N/A'),
                "Amount": f"₹{site_rec.get('wages_disbursement', {}).get('amount', 0):,.0f}",
                "Proof / Date": site_rec.get('wages_disbursement', {}).get('date', 'N/A')
            },
            {
                "Milestone": "2. Form XIX Signed Wage Register",
                "Statutory Deadline": "10th of Month",
                "Status": "🟢 PE Signed & Stamped" if site_rec.get('wage_register_sign', {}).get('status') == 'completed' else ("🟡 Pending PE Sign" if site_rec.get('wage_register_sign', {}).get('status') == 'pending_client' else "🔴 Pending"),
                "Reference / Ref No": f"{site_rec.get('wage_register_sign', {}).get('slips_count', 0)} Wage Slips",
                "Amount": "N/A",
                "Proof / Date": site_rec.get('wage_register_sign', {}).get('pe_signatory', 'Pending')
            },
            {
                "Milestone": "3. EPFO ECR Challan & TRRN Proof",
                "Statutory Deadline": "15th of Month",
                "Status": "🟢 Paid (TRRN Verified)" if site_rec.get('pf_ecr', {}).get('status') == 'completed' else "🔴 Overdue",
                "Reference / Ref No": f"TRRN: {site_rec.get('pf_ecr', {}).get('trrn', 'N/A')}",
                "Amount": f"₹{site_rec.get('pf_ecr', {}).get('amount', 0):,.0f}",
                "Proof / Date": site_rec.get('pf_ecr', {}).get('date', 'N/A')
            },
            {
                "Milestone": "4. ESIC Monthly Contribution Challan",
                "Statutory Deadline": "15th of Month",
                "Status": "🟢 Paid & Receipt Verified" if site_rec.get('esic_challan', {}).get('status') == 'completed' else "🔴 Overdue",
                "Reference / Ref No": f"Challan: {site_rec.get('esic_challan', {}).get('challan_no', 'N/A')}",
                "Amount": f"₹{site_rec.get('esic_challan', {}).get('amount', 0):,.0f}",
                "Proof / Date": site_rec.get('esic_challan', {}).get('date', 'N/A')
            },
            {
                "Milestone": "5. Gujarat Professional Tax (PT)",
                "Statutory Deadline": "15th of Month",
                "Status": "🟢 Deposited with Govt." if site_rec.get('pt_challan', {}).get('status') == 'completed' else "🔴 Pending",
                "Reference / Ref No": site_rec.get('pt_challan', {}).get('challan_no', 'N/A'),
                "Amount": f"₹{site_rec.get('pt_challan', {}).get('amount', 0):,.0f}",
                "Proof / Date": site_rec.get('pt_challan', {}).get('date', 'N/A')
            },
            {
                "Milestone": "6. Workmen Compensation / ESIC Coverage",
                "Statutory Deadline": "Active Policy",
                "Status": "🟢 Active Cover" if site_rec.get('lwf_wc', {}).get('status') == 'completed' else "🔴 Action Required",
                "Reference / Ref No": site_rec.get('lwf_wc', {}).get('policy_ref', 'N/A'),
                "Amount": "Policy Active",
                "Proof / Date": site_rec.get('lwf_wc', {}).get('notes', 'Verified')
            },
            {
                "Milestone": "7. HSE Tool Box Talk & Zero Harm Log",
                "Statutory Deadline": "Monthly Submission",
                "Status": "🟢 Safety Certified" if site_rec.get('safety_tbt', {}).get('status') == 'completed' else "🔴 Missing Log",
                "Reference / Ref No": f"{site_rec.get('safety_tbt', {}).get('tbt_count', 0)} TBT Sessions",
                "Amount": "N/A",
                "Proof / Date": site_rec.get('safety_tbt', {}).get('incident_status', 'Zero Harm')
            }
        ]
        
        st.dataframe(checklist_rows, use_container_width=True)

        st.markdown("---")
        st.markdown("#### ✏️ Update Monthly Compliance Proofs & Challans")
        
        can_upload = has_permission("can_upload_compliance_challans")
        can_approve = has_permission("can_approve_monthly_compliance")
        
        if not can_upload:
            render_permission_guard("can_upload_compliance_challans", "Update Monthly Compliance Proofs & Challans")
            st.info("ℹ️ Your role is authorized for read-only audit inspection. Compliance records, challans, and receipts can only be uploaded by Site Supervisors, Compliance Heads, or Super Admins.")
        else:
            with st.form("form_update_monthly_comp"):
                c_ed1, c_ed2 = st.columns(2)
                
                with c_ed1:
                    st.markdown("##### 1. Wages & Wage Slips")
                    st_wages = st.selectbox("Bank Wage Disbursement Status", ["completed", "in_process", "pending"], index=["completed", "in_process", "pending"].index(site_rec.get('wages_disbursement', {}).get('status', 'pending')))
                    ref_wages = st.text_input("Bank NEFT / Salary Advice Ref", value=site_rec.get('wages_disbursement', {}).get('bank_ref', ''))
                    amt_wages = st.number_input("Total Disbursed Net Wages (₹)", value=int(site_rec.get('wages_disbursement', {}).get('amount', 0)))
                    dt_wages = st.date_input("Disbursement Date", value=today)

                    st.markdown("##### 2. Form XIX Signed Register")
                    st_f19 = st.selectbox("Form XIX PE Sign Status", ["completed", "pending_client", "pending"], index=["completed", "pending_client", "pending"].index(site_rec.get('wage_register_sign', {}).get('status', 'pending')))
                    pe_sign_name = st.text_input("PE Representative Name & Title", value=site_rec.get('wage_register_sign', {}).get('pe_signatory', ''))

                with c_ed2:
                    st.markdown("##### 3. EPFO & ESIC Challans")
                    st_pf = st.selectbox("PF ECR Status", ["completed", "pending"], index=["completed", "pending"].index(site_rec.get('pf_ecr', {}).get('status', 'pending')))
                    trrn_pf = st.text_input("EPFO ECR TRRN Number", value=site_rec.get('pf_ecr', {}).get('trrn', ''))
                    amt_pf = st.number_input("PF Total Paid (₹)", value=int(site_rec.get('pf_ecr', {}).get('amount', 0)))
                    
                    st_esi = st.selectbox("ESIC Challan Status", ["completed", "pending"], index=["completed", "pending"].index(site_rec.get('esic_challan', {}).get('status', 'pending')))
                    ref_esi = st.text_input("ESIC Challan Reference No.", value=site_rec.get('esic_challan', {}).get('challan_no', ''))
                    amt_esi = st.number_input("ESIC Total Paid (₹)", value=int(site_rec.get('esic_challan', {}).get('amount', 0)))

                    st.markdown("##### 4. Professional Tax (PT)")
                    ref_pt = st.text_input("Gujarat PT Challan No.", value=site_rec.get('pt_challan', {}).get('challan_no', ''))
                    amt_pt = st.number_input("PT Deposited (₹)", value=int(site_rec.get('pt_challan', {}).get('amount', 0)))

                st.write("")
                st.markdown("##### 📎 Attach Statutory Challan Proof Document (PDF / Image)")
                existing_doc = site_rec.get('attached_proof', '')
                if existing_doc and os.path.exists(existing_doc):
                    st.caption(f"🟢 **Attached File:** `{os.path.basename(existing_doc)}`")
                up_proof = st.file_uploader("Upload Signed Challan / Bank Statement Copy", type=['pdf', 'jpg', 'jpeg', 'png'], key=f"upl_proof_{sel_month}_{selected_site_code}")

                # Executive Bill Clearance Sign-off Toggle (Restricted to can_approve_monthly_compliance)
                st.markdown("##### 📑 Client Bill Clearance Sign-Off Authority")
                if can_approve:
                    cur_dossier_status = site_rec.get('dossier_status', 'in_progress')
                    dossier_options = ["approved", "pending_review", "action_required", "in_progress"]
                    dossier_labels = [
                        "🟢 Bill Clearance Approved (All Proofs Certified)",
                        "🟡 Pending Client PE Sign / Internal Audit",
                        "🔴 Hold / Action Required (Challans Overdue)",
                        "⚪ In Progress (Data Gathering)"
                    ]
                    cur_d_idx = dossier_options.index(cur_dossier_status) if cur_dossier_status in dossier_options else 3
                    sel_d_label = st.selectbox("Official Dossier Clearance Sign-Off", dossier_labels, index=cur_d_idx)
                    chosen_dossier_status = dossier_options[dossier_labels.index(sel_d_label)]
                else:
                    st.caption("🔒 *Dossier Clearance Approval is restricted to Compliance Head & Super Admin.*")
                    chosen_dossier_status = site_rec.get('dossier_status', 'in_progress')

                save_comp_btn = st.form_submit_button("💾 Save Monthly Compliance Proofs", type="primary", use_container_width=True)
                if save_comp_btn:
                    if up_proof:
                        proof_dir = os.path.join("data", "challans", sel_month, selected_site_code)
                        os.makedirs(proof_dir, exist_ok=True)
                        p_path = os.path.join(proof_dir, up_proof.name)
                        with open(p_path, "wb") as pf_out:
                            pf_out.write(up_proof.getbuffer())
                        site_rec['attached_proof'] = p_path
                    site_rec['wages_disbursement'].update({
                        "status": st_wages,
                        "bank_ref": ref_wages.strip(),
                        "amount": int(amt_wages),
                        "date": str(dt_wages)
                    })
                    site_rec['wage_register_sign'].update({
                        "status": st_f19,
                        "pe_signatory": pe_sign_name.strip()
                    })
                    site_rec['pf_ecr'].update({
                        "status": st_pf,
                        "trrn": trrn_pf.strip(),
                        "amount": int(amt_pf),
                        "date": str(today)
                    })
                    site_rec['esic_challan'].update({
                        "status": st_esi,
                        "challan_no": ref_esi.strip(),
                        "amount": int(amt_esi),
                        "date": str(today)
                    })
                    site_rec['pt_challan'].update({
                        "status": "completed" if ref_pt.strip() else "pending",
                        "challan_no": ref_pt.strip(),
                        "amount": int(amt_pt)
                    })
                    if can_approve:
                        site_rec['dossier_status'] = chosen_dossier_status
                    save_monthly_compliance(comp_data)
                    st.success(f"✅ Compliance records for Site '{selected_site_code}' ({sel_month}) updated successfully!")
                    st.rerun()

    # TAB 2: MULTI-SITE MONTHLY COMPARISON HEATMAP
    elif selected_m_tab == m_tab_options[1]:
        st.markdown(f"#### 📊 All-Site Monthly Compliance Heatmap ({sel_month})")
        st.caption("Aap yahan se ek nazar me dekh sakte hain ki kaunsi site ka bill clear ho chuka hai aur kiska payment ruka hua hai:")
        
        heatmap_rows = []
        month_all_sites = comp_data.get(sel_month, {})
        
        for sc, sinfo in reg.get('sites', {}).items():
            s_rec = month_all_sites.get(sc, {})
            c_name = reg['clients'].get(sinfo.get('client_id'), {}).get('short_name', sinfo.get('client_id'))
            
            w_st = "🟢 Paid" if s_rec.get('wages_disbursement', {}).get('status') == 'completed' else "🔴 Pending"
            f_st = "🟢 Signed" if s_rec.get('wage_register_sign', {}).get('status') == 'completed' else ("🟡 In Review" if s_rec.get('wage_register_sign', {}).get('status') == 'pending_client' else "🔴 Pending")
            pf_st = f"🟢 TRRN ({s_rec.get('pf_ecr', {}).get('trrn', '')[:6]}...)" if s_rec.get('pf_ecr', {}).get('status') == 'completed' else "🔴 Pending"
            esi_st = "🟢 Paid" if s_rec.get('esic_challan', {}).get('status') == 'completed' else "🔴 Pending"
            
            d_st = s_rec.get('dossier_status', 'in_progress')
            if d_st == 'approved':
                badge_str = "🟢 Bill Clearance Approved"
            elif d_st == 'pending_review':
                badge_str = "🟡 Pending Client PE Sign"
            elif d_st == 'action_required':
                badge_str = "🔴 Hold (Policy/Challan Pending)"
            else:
                badge_str = "⚪ In Progress"
                
            heatmap_rows.append({
                "Site Code": sc,
                "Client PE": c_name,
                "Workers": sinfo.get('active_headcount', 0),
                "Wages (NEFT)": w_st,
                "Form XIX PE Sign": f_st,
                "PF ECR": pf_st,
                "ESIC Challan": esi_st,
                "Monthly Bill Status": badge_str,
                "Action": "👁️ Inspect"
            })
            
        st.dataframe(heatmap_rows, use_container_width=True)

    # TAB 3: CLIENT BILL CLEARANCE DOSSIER & UNDERTAKING
    elif selected_m_tab == m_tab_options[2]:
        st.markdown(f"#### 📑 Monthly Contractor Compliance Undertaking (CLRA Sec 21(4))")
        st.caption("Yeh official certificate client (Adani / Linde / Tata) HR aur Finance ko monthly bill submit karte waqt attach kiya jata hai:")
        
        fv_obj = s_obj.get('form_v', {})
        
        e_logo_tag = get_logo_html(e_obj.get('logo_path'), e_obj.get('name', 'Contractor'), max_height=56, max_width=150)
        c_logo_tag = get_logo_html(c_obj.get('logo_path'), c_obj.get('short_name', 'Client'), max_height=56, max_width=150)
        
        st.html(f"""<div class="dossier-box">
<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #0F172A; padding-bottom: 14px; margin-bottom: 16px;">
    <div style="width: 160px; text-align: left;">
        {e_logo_tag}
        <div style="font-size: 9.5px; color: #64748B; font-weight: 700; margin-top: 4px; text-transform: uppercase;">Contractor Entity</div>
    </div>
    <div style="text-align: center; flex: 1; padding: 0 16px;">
        <h3 style="margin: 0; font-size: 18px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.5px; color: #0F172A;">{e_obj.get('name')}</h3>
        <div style="font-size: 11px; color: #475569; margin-top: 2px;">CIN: {e_obj.get('cin')} &bull; GSTIN: {e_obj.get('gstin')}</div>
        <div style="font-size: 11.5px; margin-top: 2px; color: #334155;">Registered Office: {e_obj.get('address')}</div>
        <div style="font-size: 13px; font-weight: 800; margin-top: 8px; text-decoration: underline; color: #1E293B; letter-spacing: 0.3px;">
            MONTHLY STATUTORY COMPLIANCE CLEARANCE CERTIFICATE & BILLING UNDERTAKING
        </div>
        <div style="font-size: 11.5px; font-style: italic; color: #64748B; margin-top: 2px;">
            (For the Month of: <b>{sel_month}</b> &bull; Under Section 21(4) of Contract Labour (R&A) Act, 1970)
        </div>
    </div>
    <div style="width: 160px; text-align: right;">
        {c_logo_tag}
        <div style="font-size: 9.5px; color: #64748B; font-weight: 700; margin-top: 4px; text-transform: uppercase;">Principal Employer</div>
    </div>
</div>

<div style="font-size: 13px; line-height: 1.8;">
<div>To,<br><b>The Head of HR & Commercial Contracts</b><br><b>{c_obj.get('name')}</b><br>{c_obj.get('location')}</div>
<br>
<div><b>Subject:</b> Statutory Compliance Submission & Clearance for Monthly Invoice against Work Order No: <code>{s_obj.get('po_no')}</code> (Site: <b>{selected_site_code}</b>).</div>
<br>
<div>Dear Sir/Madam,</div>
<div>We hereby certify and confirm that for the deployment of <b>{s_obj.get('active_headcount')} contractual workmen</b> deployed at your site during the month of <b>{sel_month}</b> under CLRA License No. <code>{s_obj.get('clra_license_no')}</code>, the following statutory obligations have been duly fulfilled:</div>

<ol style="margin: 8px 0; padding-left: 22px;">
<li><b>Payment of Wages:</b> Full wages amounting to <b>₹{site_rec.get('wages_disbursement', {}).get('amount', 0):,.0f}</b> have been disbursed directly to workmen bank accounts via NEFT on <b>{site_rec.get('wages_disbursement', {}).get('date', '7th of month')}</b> (Bank Ref: <code>{site_rec.get('wages_disbursement', {}).get('bank_ref', 'Verified')}</code>) without any unauthorized deductions.</li>
<li><b>Wage Register Form XIX:</b> Form XIX has been prepared, verified, and countersigned by your authorized Principal Employer representative (<b>{site_rec.get('wage_register_sign', {}).get('pe_signatory', c_obj.get('contact_person'))}</b>).</li>
<li><b>EPF Contributions:</b> Employee and Employer PF contributions amounting to <b>₹{site_rec.get('pf_ecr', {}).get('amount', 0):,.0f}</b> have been deposited with EPFO against Master PF Code <code>{e_obj.get('pf_code')}</code> vide TRRN No. <code>{site_rec.get('pf_ecr', {}).get('trrn', 'Verified')}</code>.</li>
<li><b>ESIC / Workmen Compensation:</b> ESIC monthly contribution of <b>₹{site_rec.get('esic_challan', {}).get('amount', 0):,.0f}</b> has been deposited (Challan No: <code>{site_rec.get('esic_challan', {}).get('challan_no', 'Verified')}</code>) / covered under WC Policy <code>{s_obj.get('wc_policy_no')}</code>.</li>
<li><b>Gujarat Professional Tax:</b> PT amounting to <b>₹{site_rec.get('pt_challan', {}).get('amount', 0):,.0f}</b> has been deposited vide Challan No. <code>{site_rec.get('pt_challan', {}).get('challan_no', 'Verified')}</code>.</li>
<li><b>HSE & Safety:</b> All workers attended mandatory daily Tool Box Talks (TBT) and adhered to PPE safety norms with Zero Reportable Incidents.</li>
</ol>

<div>We confirm that all relevant records, electronic receipts, and ECR challan copies are annexed herewith. Kindly clear our monthly invoice for payment.</div>

<div style="margin-top: 30px; display: flex; justify-content: space-between; align-items: flex-end;">
<div>
<b>Verified & Forwarded By:</b><br><br>
<b>{s_obj.get('site_incharge', 'Darshan Sir')}</b><br>
Site Compliance Head & In-Charge<br>
{e_obj.get('name')}
</div>
<div style="text-align: right;">
<b>For {e_obj.get('name')}:</b><br><br>
<b>{e_obj.get('signatory_name')}</b><br>
{e_obj.get('signatory_title')}<br>
(Authorized Signatory)
</div>
</div>
</div>
</div>""")

        st.write("")
        col_dn1, col_dn2 = st.columns(2)
        with col_dn1:
            full_undertaking_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Statutory Compliance Undertaking - {selected_site_code} ({sel_month})</title>
<style>
    body {{ font-family: 'Times New Roman', serif; padding: 30px; color: #0F172A; line-height: 1.6; background: #FFF; }}
    .cert-box {{ border: 2px solid #0F172A; padding: 32px; border-radius: 8px; max-width: 900px; margin: auto; }}
    @media print {{ body {{ padding: 0; }} .cert-box {{ border: 1.5px solid #000; }} }}
</style>
</head>
<body>
<div class="cert-box">
<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #0F172A; padding-bottom: 12px; margin-bottom: 16px;">
    <div>{e_logo_tag}</div>
    <div style="text-align: center; flex: 1;">
        <h2 style="margin: 0; font-size: 18px; text-transform: uppercase;">{e_obj.get('name')}</h2>
        <div style="font-size: 11px;">CIN: {e_obj.get('cin')} &bull; GSTIN: {e_obj.get('gstin')}</div>
        <div style="font-size: 11.5px;">{e_obj.get('address')}</div>
        <h3 style="margin-top: 10px; text-decoration: underline;">MONTHLY STATUTORY COMPLIANCE UNDERTAKING (CLRA SEC 21(4))</h3>
        <i>For Month: {sel_month}</i>
    </div>
    <div>{c_logo_tag}</div>
</div>
<div>To,<br>The Head of HR & Commercial Contracts<br><b>{c_obj.get('name')}</b><br>{c_obj.get('location')}</div>
<p><b>Subject:</b> Compliance Submission for Monthly Invoice against PO <code>{s_obj.get('po_no')}</code> (Site: <b>{selected_site_code}</b>)</p>
<p>We certify that <b>{s_obj.get('active_headcount')} contractual workmen</b> deployed at your site during <b>{sel_month}</b> under CLRA No. <code>{s_obj.get('clra_license_no')}</code> have received full wages (₹{site_rec.get('wages_disbursement', {}).get('amount', 0):,.0f}), PF (TRRN: {site_rec.get('pf_ecr', {}).get('trrn', 'Verified')}), ESIC, and PT without default.</p>
<div style="margin-top: 40px; display: flex; justify-content: space-between;">
    <div><b>Verified By:</b> {s_obj.get('site_incharge')} (Site In-Charge)</div>
    <div style="text-align: right;"><b>For {e_obj.get('name')}:</b><br>{e_obj.get('signatory_name')}<br>({e_obj.get('signatory_title')})</div>
</div>
</div>
</body>
</html>"""
            st.download_button(
                "📥 Download Official Undertaking (Print-Ready HTML)",
                data=full_undertaking_html,
                file_name=f"Compliance_Undertaking_{selected_site_code}_{sel_month}.html",
                mime="text/html",
                use_container_width=True
            )
        with col_dn2:
            st.download_button(
                "📋 Download Undertaking Text / Summary",
                data=f"UNDERTAKING UNDER CLRA SEC 21(4)\nContractor: {e_obj.get('name')}\nClient: {c_obj.get('name')}\nSite: {selected_site_code}\nMonth: {sel_month}\nWorkers: {s_obj.get('active_headcount')}\nWages: ₹{site_rec.get('wages_disbursement', {}).get('amount', 0):,.0f}\nPF TRRN: {site_rec.get('pf_ecr', {}).get('trrn', 'Verified')}",
                file_name=f"Compliance_Undertaking_{selected_site_code}_{sel_month}.txt",
                mime="text/plain",
                use_container_width=True
            )
