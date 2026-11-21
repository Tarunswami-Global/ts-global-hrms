import streamlit as st
import io
import os
import textwrap
import pandas as pd
from datetime import datetime, timedelta
from automation.config import load_settings
from automation.utils.letter_generators import (
    generate_joining_offer_docx,
    generate_joining_offer_pdf,
    generate_joining_offer_bulk_zip,
    generate_consolidated_joining_offer_pdf,
    compute_salary_breakdown,
    solve_gross_from_inhand,
    solve_gross_from_annual_ctc,
    solve_gross_from_monthly_ctc,
    excel_round
)

def render(selected_site):
    settings = load_settings()
    default_est = settings.get('establishment_name', "AAIKRUPA INFRATECH PVT. LTD.")
    default_addr = settings.get('company_address', "Shop No. 18, Ashok Vatika, Dhrab, Mundra, Kutch, Gujarat - 370421")
    sig_name = settings.get('signatory_name', "Tarun Swami")
    sig_title = settings.get('signatory_title', "Authorized Signatory / Managing Director")

    st.subheader("🤝 Official Offer of Employment & Salary Annexure-A Generator")
    st.markdown(
        "<p style='color:#64748B; font-size:13px; margin-top:-10px;'>"
        "Tri-Directional Salary Calculator (Gross ⇄ In-Hand ⇄ Annual CTC) • Strict 3-Page A4 Geometry • "
        "Multi-Company & Project Site Support • Dual Letterhead Modes"
        "</p>",
        unsafe_allow_html=True
    )

    # =========================================================================
    # GLOBAL SETTINGS: COMPANY & SITE SELECTION
    # =========================================================================
    st.markdown("### 🏢 Company & Work Site Configuration")
    cfg_c1, cfg_c2 = st.columns(2)

    with cfg_c1:
        comp_choice = st.selectbox(
            "Select Issuing Company Entity",
            [
                "AAIKRUPA INFRATECH PVT. LTD.",
                "ASHAPURA INFRATECH",
                "ASHAPURA ENTERPRISE",
                "➕ Custom Company Name"
            ],
            index=0,
            key="offer_comp_choice"
        )
        if comp_choice == "➕ Custom Company Name":
            est_name = st.text_input("Enter Company Full Name", value="ASHAPURA INFRATECH", key="offer_custom_comp")
        else:
            est_name = comp_choice

        comp_addr = st.text_input("Company Address (For Header / Notice)", value=default_addr, key="offer_comp_addr")

    with cfg_c2:
        site_choice = st.selectbox(
            "Select Operating Project Site / Location",
            [
                "M/S. MUNDRA PETROCHEM LIMITED (MPL Piping 250)",
                "M/S. MUNDRA PETROCHEM LIMITED (MPL Struct 250)",
                "ADANI NEW INDUSTRIES LTD. (ANIL Project Site)",
                "TATA PROJECTS / LINDE INDIA SITE",
                "CENTRAL FABRICATION YARD (Mundra)",
                "➕ Custom Site / Work Location"
            ],
            index=0 if "MUNDRA" in selected_site.upper() else 2,
            key="offer_site_choice"
        )
        if site_choice == "➕ Custom Site / Work Location":
            site_loc = st.text_input("Enter Work Site / Location", value=selected_site, key="offer_custom_site")
        else:
            site_loc = site_choice

    st.markdown("---")

    # =========================================================================
    # 🧮 TRI-DIRECTIONAL SALARY CALCULATOR ENGINE (ANNEXURE - A)
    # =========================================================================
    st.markdown("### 🧮 Smart Bidirectional Salary Calculator (Annexure – A)")
    st.caption("Calculate accurate salary bifurcation by entering any ONE of: **Gross Salary**, **In-Hand (Net Pay)**, or **Annual CTC**. The system automatically reverse-calculates the other two with zero manual math.")

    calc_m1, calc_m2 = st.columns([1.2, 1.8])

    with calc_m1:
        calc_mode = st.radio(
            "Choose Target Input Mode:",
            [
                "💵 Enter Monthly Gross Salary (₹)",
                "💰 Enter Desired Net In-Hand Salary (₹)",
                "📦 Enter Offered Annual CTC (₹)"
            ],
            index=0,
            key="offer_calc_mode"
        )

        cat_choice = st.selectbox(
            "Candidate Wage Category:",
            [
                "Staff / Skilled (Basic Min ₹13,897)",
                "Helper / Semi-Skilled (Basic Min ₹13,351)"
            ],
            index=0,
            key="offer_cat_choice"
        )
        is_helper = "Helper" in cat_choice

        c_sub1, c_sub2 = st.columns(2)
        with c_sub1:
            esic_mode = st.selectbox("ESIC Applicability:", ["AUTO (if Gross ≤ ₹21,000)", "YES (Deduct ESIC)", "NO (Exempt)"], key="offer_esic_mode")
        with c_sub2:
            pt_choice = st.selectbox("Professional Tax (PT):", ["₹0 (Standard / Exempt)", "₹200 (Applicable)"], key="offer_pt_choice")
            pt_val = 200.0 if "200" in pt_choice else 0.0

    with calc_m2:
        if "Gross" in calc_mode:
            input_gross = st.number_input("Monthly Gross Salary (₹):", min_value=13351.0, max_value=500000.0, value=35000.0, step=1000.0, key="in_gross")
            esic_rule = "YES" if ("YES" in esic_mode or ("AUTO" in esic_mode and input_gross <= 21000)) else "NO"
            brk = compute_salary_breakdown(input_gross, is_staff=(not is_helper), is_helper=is_helper, esic_opt=esic_rule, pt_val=pt_val)
            derived_gross = input_gross

        elif "In-Hand" in calc_mode:
            input_inhand = st.number_input("Desired Monthly Net In-Hand (₹):", min_value=12000.0, max_value=450000.0, value=35000.0, step=1000.0, key="in_inhand")
            esic_rule = "YES" if ("YES" in esic_mode or ("AUTO" in esic_mode and input_inhand <= 21000)) else "NO"
            derived_gross = solve_gross_from_inhand(input_inhand, is_staff=(not is_helper), is_helper=is_helper, esic_opt=esic_rule, pt_val=pt_val)
            # Re-evaluate ESIC rule with derived gross
            if "AUTO" in esic_mode:
                esic_rule = "YES" if derived_gross <= 21000 else "NO"
                derived_gross = solve_gross_from_inhand(input_inhand, is_staff=(not is_helper), is_helper=is_helper, esic_opt=esic_rule, pt_val=pt_val)
            brk = compute_salary_breakdown(derived_gross, is_staff=(not is_helper), is_helper=is_helper, esic_opt=esic_rule, pt_val=pt_val)

        else: # Annual CTC
            input_ctc = st.number_input("Offered Annual CTC (₹):", min_value=150000.0, max_value=6000000.0, value=450000.0, step=10000.0, key="in_ctc")
            esic_rule = "YES" if ("YES" in esic_mode or ("AUTO" in esic_mode and (input_ctc/12.0) <= 22000)) else "NO"
            derived_gross = solve_gross_from_annual_ctc(input_ctc, is_staff=(not is_helper), is_helper=is_helper, esic_opt=esic_rule, pt_val=pt_val)
            if "AUTO" in esic_mode:
                esic_rule = "YES" if derived_gross <= 21000 else "NO"
                derived_gross = solve_gross_from_annual_ctc(input_ctc, is_staff=(not is_helper), is_helper=is_helper, esic_opt=esic_rule, pt_val=pt_val)
            brk = compute_salary_breakdown(derived_gross, is_staff=(not is_helper), is_helper=is_helper, esic_opt=esic_rule, pt_val=pt_val)

        # Visual KPI Badges
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("💵 Monthly Gross", f"₹ {brk['gross']:,.2f}")
        k2.metric("💰 Net In-Hand", f"₹ {brk['in_hand']:,.2f}")
        k3.metric("📦 Annual CTC", f"₹ {brk['annual_ctc']:,.2f}", delta=f"Monthly: ₹{brk['monthly_ctc']:,.2f}")
        k4.metric("📉 Deductions", f"₹ {brk['tot_ded']:,.2f}")

    with st.expander("📊 View Complete 17-Component Salary Structure Details (Annexure – A)", expanded=False):
        bifur_html = f"""<table style="width:100%; border-collapse:collapse; font-size:12.5px; border:1px solid #CBD5E1;">
<thead>
<tr style="background:#1E3A8A; color:#ffffff; font-weight:bold;">
<th style="padding:6px 12px; border:1px solid #CBD5E1; text-align:left;">Component</th>
<th style="padding:6px 12px; border:1px solid #CBD5E1; text-align:right;">Monthly (₹)</th>
<th style="padding:6px 12px; border:1px solid #CBD5E1; text-align:right;">Annual (₹)</th>
</tr>
</thead>
<tbody>
<tr><td style="padding:5px 12px; border:1px solid #CBD5E1;">Basic Salary</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['basic']:,.2f}</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['basic']*12:,.2f}</td></tr>
<tr><td style="padding:5px 12px; border:1px solid #CBD5E1;">HRA</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['hra']:,.2f}</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['hra']*12:,.2f}</td></tr>
<tr><td style="padding:5px 12px; border:1px solid #CBD5E1;">Advance / Variable Bonus</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['bonus']:,.2f}</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['bonus']*12:,.2f}</td></tr>
<tr><td style="padding:5px 12px; border:1px solid #CBD5E1;">Leave Component</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['leave']:,.2f}</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['leave']*12:,.2f}</td></tr>
<tr><td style="padding:5px 12px; border:1px solid #CBD5E1;">Other Earnings</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['other']:,.2f}</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['other']*12:,.2f}</td></tr>
<tr><td style="padding:5px 12px; border:1px solid #CBD5E1;">Special Allowance</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['special']:,.2f}</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['special']*12:,.2f}</td></tr>
<tr style="background:#EFF6FF; font-weight:bold; color:#1E3A8A;"><td style="padding:6px 12px; border:1px solid #CBD5E1;">GROSS SALARY</td><td style="padding:6px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['gross']:,.2f}</td><td style="padding:6px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['gross']*12:,.2f}</td></tr>
<tr><td style="padding:5px 12px; border:1px solid #CBD5E1;">Employee PF Contribution</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['emp_pf']:,.2f}</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['emp_pf']*12:,.2f}</td></tr>
<tr><td style="padding:5px 12px; border:1px solid #CBD5E1;">Professional Tax</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['pt']:,.2f}</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['pt']*12:,.2f}</td></tr>
<tr><td style="padding:5px 12px; border:1px solid #CBD5E1;">ESIC / Other Deductions</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['emp_esic']:,.2f}</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['emp_esic']*12:,.2f}</td></tr>
<tr style="background:#FEF2F2; font-weight:bold; color:#DC2626;"><td style="padding:6px 12px; border:1px solid #CBD5E1;">TOTAL DEDUCTIONS</td><td style="padding:6px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['tot_ded']:,.2f}</td><td style="padding:6px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['tot_ded']*12:,.2f}</td></tr>
<tr style="background:#ECFDF5; font-weight:bold; color:#065F46; font-size:13.5px;"><td style="padding:7px 12px; border:1px solid #CBD5E1;">NET PAY (IN HAND)</td><td style="padding:7px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['in_hand']:,.2f}</td><td style="padding:7px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['in_hand']*12:,.2f}</td></tr>
<tr><td style="padding:5px 12px; border:1px solid #CBD5E1;">Employer PF Contribution</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['empr_pf']:,.2f}</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['empr_pf']*12:,.2f}</td></tr>
<tr><td style="padding:5px 12px; border:1px solid #CBD5E1;">Employer ESIC Contribution</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['empr_esic']:,.2f}</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['empr_esic']*12:,.2f}</td></tr>
<tr><td style="padding:5px 12px; border:1px solid #CBD5E1;">Other Employer Contributions</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['empr_other']:,.2f}</td><td style="padding:5px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['empr_other']*12:,.2f}</td></tr>
<tr style="background:#F0FDF4; font-weight:bold; color:#15803D; font-size:13.5px;"><td style="padding:7px 12px; border:1px solid #CBD5E1;">TOTAL CTC</td><td style="padding:7px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['monthly_ctc']:,.2f}</td><td style="padding:7px 12px; border:1px solid #CBD5E1; text-align:right;">₹ {brk['annual_ctc']:,.2f}</td></tr>
</tbody>
</table>"""
        st.markdown(bifur_html, unsafe_allow_html=True)

    st.markdown("---")

    # =========================================================================
    # DUAL OPERATION MODE TABS
    # =========================================================================
    tab1, tab2 = st.tabs([
        "👤 Mode 1: Single Candidate Offer Letter",
        "📂 Mode 2: Bulk Offer Letters (Mail Merge Excel)"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: SINGLE CANDIDATE OFFER LETTER
    # -------------------------------------------------------------------------
    with tab1:
        st.markdown("#### 📋 Fill Candidate & Job Offer Details")
        c1, c2 = st.columns(2)

        with c1:
            ref_no = st.text_input("Offer Reference No.", value=f"AIPL/HR/OFFER/{datetime.today().year}/055", key="s_offer_ref")
            letter_date = st.text_input("Offer Issue Date (DD/MM/YYYY)", value=datetime.today().strftime('%d/%m/%Y'), key="s_offer_date")
            c_name = st.text_input("Candidate Full Name", value="MANISH R. JOSHI", key="s_offer_name")
            mobile = st.text_input("Contact Mobile", value="+91 94270 55678", key="s_offer_mobile")
            email = st.text_input("Email Address", value="manish.joshi@example.com", key="s_offer_email")
            emp_id = st.text_input("Candidate ID / Code", value="AIPL-2026-881", key="s_offer_id")

        with c2:
            designation = st.text_input("Offered Designation / Position", value="Senior Quality Control Inspector", key="s_offer_desig")
            department = st.text_input("Department / Division", value="Quality Assurance & Quality Control", key="s_offer_dept")
            doj = st.text_input("Proposed Date of Joining (DD/MM/YYYY)", value=(datetime.today() + timedelta(days=10)).strftime('%d/%m/%Y'), key="s_offer_doj")
            rep_to = st.text_input("Reporting Authority", value="Project Head / Site In-charge", key="s_offer_repto")
            prob_period = st.text_input("Probation Period", value="90 Calendar Days", key="s_offer_prob")
            notice_period = st.text_input("Notice Period", value="30 Calendar Days", key="s_offer_notice")

        single_data = {
            'establishment_name': est_name,
            'company_name': est_name,
            'company_address': comp_addr,
            'ref_no': ref_no,
            'date': letter_date,
            'candidate_name': c_name,
            'mobile': mobile,
            'phone': mobile,
            'email': email,
            'emp_id': emp_id,
            'designation': designation,
            'department': department,
            'doj': doj,
            'reporting_date': doj,
            'location': site_loc,
            'site': site_loc,
            'reporting_to': rep_to,
            'probation_period': prob_period,
            'notice_period': notice_period,
            'gross': brk['gross'],
            'salary_breakdown': brk,
            'brk': brk,
            'annual_ctc': brk['annual_ctc'],
            'monthly_ctc': brk['monthly_ctc'],
            'in_hand': brk['in_hand'],
            'signatory_name': sig_name,
            'signatory_title': sig_title
        }

        # Live HTML Preview (Zero-indenting to guarantee NO markdown code block triggers)
        with st.expander("👁️ View Live 3-Page Offer Letter & Annexure-A Preview", expanded=True):
            preview_html = f"""<div class="letter-preview-box" style="background:#ffffff; border:1px solid #CBD5E1; border-radius:8px; padding:28px; font-family:'Aptos Narrow', Arial, sans-serif; color:#0F172A; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);">
<div style="border-bottom: 2px solid #1E3A8A; padding-bottom: 8px; margin-bottom: 12px;">
<div style="display: flex; justify-content: space-between; align-items: baseline;">
<div>
<h3 style="margin: 0; color: #1E3A8A;">{est_name.upper()}</h3>
<p style="margin: 2px 0; font-size: 12px; color: #64748B;">{comp_addr}</p>
</div>
<div style="text-align: right; font-size: 12.5px;">
<b>Ref No:</b> {ref_no}<br/>
<b>Date:</b> {letter_date}
</div>
</div>
</div>

<div style="text-align: center; margin: 12px 0;">
<h4 style="margin: 0; color: #0F172A; text-decoration: underline; font-size: 15px;">OFFER OF EMPLOYMENT</h4>
</div>

<p style="font-size: 13px; margin: 4px 0;">
<b>To,</b><br/>
<b>Mr. {c_name}</b><br/>
Email ID: {email} | Mobile No.: {mobile}
</p>

<p style="font-size: 13px; font-weight: bold; margin: 10px 0 6px 0; color: #1E3A8A;">
Subject: Letter of Employment Offer
</p>

<p style="font-size: 13px; margin: 4px 0;">Dear <b>{c_name}</b>,</p>
<p style="font-size: 13px; line-height: 1.5; margin: 6px 0;">
We are pleased to inform you that, following the selection process, you have been selected for the position of <b>'{designation}'</b> with <b>{est_name}</b>. The summary terms of your offer are detailed below:
</p>

<table style="width: 100%; border-collapse: collapse; font-size: 12.5px; margin: 10px 0; border: 1px solid #94A3B8;">
<tr style="background: #F1F5F9; font-weight: bold;">
<td style="border: 1px solid #94A3B8; padding: 5px 10px; width: 35%;">Particulars</td>
<td style="border: 1px solid #94A3B8; padding: 5px 10px;">Details</td>
</tr>
<tr><td style="border: 1px solid #94A3B8; padding: 5px 10px;">Designation</td><td style="border: 1px solid #94A3B8; padding: 5px 10px;"><b>{designation}</b></td></tr>
<tr><td style="border: 1px solid #94A3B8; padding: 5px 10px;">Department</td><td style="border: 1px solid #94A3B8; padding: 5px 10px;">{department}</td></tr>
<tr><td style="border: 1px solid #94A3B8; padding: 5px 10px;">Date of Joining</td><td style="border: 1px solid #94A3B8; padding: 5px 10px;"><b>{doj}</b></td></tr>
<tr><td style="border: 1px solid #94A3B8; padding: 5px 10px;">Work Location</td><td style="border: 1px solid #94A3B8; padding: 5px 10px;">{site_loc}</td></tr>
<tr><td style="border: 1px solid #94A3B8; padding: 5px 10px;">Reporting Authority</td><td style="border: 1px solid #94A3B8; padding: 5px 10px;">{rep_to}</td></tr>
<tr><td style="border: 1px solid #94A3B8; padding: 5px 10px;">Probation Period</td><td style="border: 1px solid #94A3B8; padding: 5px 10px;">{prob_period}</td></tr>
<tr><td style="border: 1px solid #94A3B8; padding: 5px 10px;">Notice Period</td><td style="border: 1px solid #94A3B8; padding: 5px 10px;">{notice_period}</td></tr>
<tr style="background: #EFF6FF; font-weight: bold; color: #1E3A8A;">
<td style="border: 1px solid #94A3B8; padding: 5px 10px;">Total Remuneration (CTC)</td>
<td style="border: 1px solid #94A3B8; padding: 5px 10px;">₹ {brk['annual_ctc']:,.2f} (As specified in Annexure – A)</td>
</tr>
</table>

<div style="border-top: 1px dashed #CBD5E1; margin: 18px 0; padding-top: 10px;">
<div style="font-weight: bold; color: #1E3A8A; font-size: 13.5px; margin-bottom: 6px;">📄 Page 2 Summary: Key Terms, Joining Documents & Offer Acceptance</div>
<p style="font-size: 12.5px; color: #475569; margin: 4px 0;">Includes mandatory joining checklist (Aadhaar, PAN, Bank Details, Education, Experience, Medical Fitness) and formal candidate acceptance sign-off block.</p>
</div>

<div style="border-top: 1px dashed #CBD5E1; margin: 18px 0; padding-top: 10px;">
<div style="font-weight: bold; color: #1E3A8A; font-size: 13.5px; margin-bottom: 6px;">📊 Page 3 Summary: Annexure – A Complete CTC Salary Structure</div>
<p style="font-size: 12.5px; color: #475569; margin: 4px 0;">Official 17-row bifurcation: Basic Salary (₹{brk['basic']:,.2f}), HRA (₹{brk['hra']:,.2f}), Advance / Variable Bonus (₹{brk['bonus']:,.2f}), Leave Component (₹{brk['leave']:,.2f}), Employee PF Contribution (₹{brk['emp_pf']:,.2f}), Net Pay (In Hand) (₹{brk['in_hand']:,.2f}), and Total CTC (₹{brk['annual_ctc']:,.2f}/yr).</p>
</div>

<div style="margin-top: 20px; display: flex; justify-content: space-between; font-size: 12.5px;">
<div>
<b>For, {est_name}</b><br/><br/><br/>
<b>{sig_name}</b><br/>{sig_title}
</div>
<div style="text-align: right;">
<b>Candidate Acceptance:</b><br/><br/><br/>
Signature: __________________<br/>
<b>{c_name}</b>
</div>
</div>
</div>"""
            st.markdown(preview_html, unsafe_allow_html=True)

        st.markdown("### 📥 Generate & Download Joining Offer Letter")
        b1, b2, b3 = st.columns(3)

        # 1. Letterhead PDF (With Header Artwork)
        with b1:
            if st.button("📄 Generate PDF (With Letterhead)", key="btn_offer_pdf_lh", type="primary", use_container_width=True):
                with st.spinner("Generating 3-page Letterhead PDF via Microsoft Word COM engine..."):
                    pdf_lh_buf = generate_joining_offer_pdf(single_data, with_letterhead=True)
                    st.session_state['s_offer_pdf_lh_bytes'] = pdf_lh_buf.getvalue()
                    st.session_state['s_offer_pdf_lh_name'] = f"Offer_{emp_id}_{c_name.replace(' ', '_')}_Letterhead.pdf"

                    # Generate visual snapshot of pages 1, 2, 3
                    try:
                        import pypdfium2 as pdfium
                        pdf_doc = pdfium.PdfDocument(pdf_lh_buf.getvalue())
                        st.session_state['s_offer_lh_pages'] = [page.render(scale=1.5).to_pil() for page in pdf_doc]
                        pdf_doc.close()
                    except Exception:
                        pass
                    st.success("✅ 3-Page Letterhead PDF ready!")

            if st.session_state.get('s_offer_pdf_lh_bytes'):
                st.download_button(
                    "⬇️ Download PDF (With Letterhead)",
                    data=st.session_state['s_offer_pdf_lh_bytes'],
                    file_name=st.session_state['s_offer_pdf_lh_name'],
                    mime="application/pdf",
                    use_container_width=True
                )
            if st.session_state.get('s_offer_lh_pages'):
                with st.expander("👁️ View Letterhead PDF Snapshots (Strict 3 Pages)", expanded=False):
                    tabs_p = st.tabs(["Page 1: Terms", "Page 2: Checklist & Acceptance", "Page 3: Annexure-A"])
                    for p_i, tab_p in enumerate(tabs_p):
                        with tab_p:
                            if p_i < len(st.session_state['s_offer_lh_pages']):
                                st.image(st.session_state['s_offer_lh_pages'][p_i], caption=f"Letterhead PDF - Page {p_i+1}", use_container_width=True)

        # 2. Plain Paper PDF (Without Letterhead / 1.80" Top Margin)
        with b2:
            if st.button("🖨️ Generate PDF (Pre-Printed Stationery)", key="btn_offer_pdf_plain", use_container_width=True):
                with st.spinner("Generating 3-page Plain Stationery PDF (1.80\" Top Margin)..."):
                    pdf_plain_buf = generate_joining_offer_pdf(single_data, with_letterhead=False)
                    st.session_state['s_offer_pdf_plain_bytes'] = pdf_plain_buf.getvalue()
                    st.session_state['s_offer_pdf_plain_name'] = f"Offer_{emp_id}_{c_name.replace(' ', '_')}_PlainPaper.pdf"

                    # Generate visual snapshot of plain pages 1, 2, 3
                    try:
                        import pypdfium2 as pdfium
                        pdf_doc2 = pdfium.PdfDocument(pdf_plain_buf.getvalue())
                        st.session_state['s_offer_plain_pages'] = [page.render(scale=1.5).to_pil() for page in pdf_doc2]
                        pdf_doc2.close()
                    except Exception:
                        pass
                    st.success("✅ 3-Page Plain Stationery PDF ready!")

            if st.session_state.get('s_offer_pdf_plain_bytes'):
                st.download_button(
                    "⬇️ Download PDF (Pre-Printed Stationery)",
                    data=st.session_state['s_offer_pdf_plain_bytes'],
                    file_name=st.session_state['s_offer_pdf_plain_name'],
                    mime="application/pdf",
                    use_container_width=True
                )
            if st.session_state.get('s_offer_plain_pages'):
                with st.expander("👁️ View Plain Stationery PDF Snapshots (Strict 3 Pages)", expanded=False):
                    tabs_p2 = st.tabs(["Page 1: Terms", "Page 2: Checklist & Acceptance", "Page 3: Annexure-A"])
                    for p_i, tab_p in enumerate(tabs_p2):
                        with tab_p:
                            if p_i < len(st.session_state['s_offer_plain_pages']):
                                st.image(st.session_state['s_offer_plain_pages'][p_i], caption=f"Plain Stationery PDF - Page {p_i+1} (1.80\" Top Margin)", use_container_width=True)

        # 3. Word Document (.docx)
        with b3:
            if st.button("📝 Generate Word (.docx)", key="btn_offer_docx", use_container_width=True):
                docx_buf = generate_joining_offer_docx(single_data, with_letterhead=True)
                st.session_state['s_offer_docx_bytes'] = docx_buf.getvalue()
                st.session_state['s_offer_docx_name'] = f"Offer_{emp_id}_{c_name.replace(' ', '_')}.docx"
                st.success("✅ Word document generated!")

            if st.session_state.get('s_offer_docx_bytes'):
                st.download_button(
                    "⬇️ Download Word (.docx)",
                    data=st.session_state['s_offer_docx_bytes'],
                    file_name=st.session_state['s_offer_docx_name'],
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )

    # -------------------------------------------------------------------------
    # TAB 2: BULK OFFER LETTERS (MAIL MERGE EXCEL)
    # -------------------------------------------------------------------------
    with tab2:
        st.markdown("#### 📂 Bulk Offer Letters Generation (Excel Mail Merge)")
        st.caption("Upload an Excel file with candidates and their Gross, In-Hand, or Annual CTC. The system automatically computes all 17 components of Annexure-A and generates individual or consolidated PDFs.")

        # Download Sample Template
        st.markdown("##### 1. Download Blank Sample Excel Template")
        sample_rows = [
            {
                'candidate_name': 'MANISH R. JOSHI',
                'mobile': '+91 94270 55678',
                'email': 'manish.joshi@example.com',
                'emp_id': 'AIPL-2026-881',
                'designation': 'Senior QC Inspector',
                'department': 'Quality Assurance & Control',
                'doj': '01/12/2026',
                'location': site_loc,
                'reporting_to': 'Project Head / Site In-charge',
                'salary_mode': 'InHand',
                'salary_value': 35000.0,
                'category': 'Staff',
                'esic_opt': 'AUTO',
                'pt_val': 0.0
            },
            {
                'candidate_name': 'VIKRAM SINGH CHAUHAN',
                'mobile': '+91 98250 12345',
                'email': 'vikram.chauhan@example.com',
                'emp_id': 'AIPL-2026-882',
                'designation': 'Mechanical Site Engineer',
                'department': 'Piping & Fabrication',
                'doj': '05/12/2026',
                'location': site_loc,
                'reporting_to': 'Plant General Manager',
                'salary_mode': 'CTC',
                'salary_value': 450000.0,
                'category': 'Staff',
                'esic_opt': 'AUTO',
                'pt_val': 0.0
            },
            {
                'candidate_name': 'DINESH B. MEHTA',
                'mobile': '+91 97123 99881',
                'email': 'dinesh.mehta@example.com',
                'emp_id': 'AIPL-2026-883',
                'designation': 'Senior Electrical Supervisor',
                'department': 'Electrical & Instrumentation',
                'doj': '10/12/2026',
                'location': site_loc,
                'reporting_to': 'Site In-charge',
                'salary_mode': 'Gross',
                'salary_value': 38000.0,
                'category': 'Staff',
                'esic_opt': 'NO',
                'pt_val': 200.0
            }
        ]
        df_sample = pd.DataFrame(sample_rows)
        sample_buf = io.BytesIO()
        df_sample.to_excel(sample_buf, index=False, engine='openpyxl')
        sample_buf.seek(0)

        st.download_button(
            "📥 Download Blank Sample Bulk Offer Template (.xlsx)",
            data=sample_buf.getvalue(),
            file_name="Offer_Letter_Bulk_Template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="btn_down_offer_tpl"
        )

        st.markdown("---")
        st.markdown("##### 2. Upload Completed Candidate List")
        up_file = st.file_uploader("Upload Excel File (.xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"], key="offer_bulk_upload")

        if up_file:
            try:
                if up_file.name.endswith('.csv'):
                    df_up = pd.read_csv(up_file)
                else:
                    df_up = pd.read_excel(up_file)
            except Exception as e:
                st.error(f"Failed to read file: {e}")
                df_up = None

            if df_up is not None and not df_up.empty:
                st.success(f"✅ Loaded {len(df_up)} candidates successfully!")

                # Process candidates and compute salary
                processed_records = []
                for idx, row in df_up.iterrows():
                    rec = row.to_dict()
                    c_name_val = str(rec.get('candidate_name', f'Candidate_{idx+1}')).strip()
                    desig_val = str(rec.get('designation', 'Staff')).strip()
                    is_h = 'HELPER' in desig_val.upper() or 'HELPER' in str(rec.get('category', '')).upper()
                    mode = str(rec.get('salary_mode', 'Gross')).strip().lower()
                    val = float(rec.get('salary_value', 35000.0))
                    esic_val = str(rec.get('esic_opt', 'AUTO')).strip().upper()
                    pt_v = float(rec.get('pt_val', 0.0))

                    if 'inhand' in mode or 'in_hand' in mode or 'net' in mode:
                        esic_r = "YES" if ("YES" in esic_val or ("AUTO" in esic_val and val <= 21000)) else "NO"
                        g = solve_gross_from_inhand(val, is_staff=(not is_h), is_helper=is_h, esic_opt=esic_r, pt_val=pt_v)
                        if "AUTO" in esic_val:
                            esic_r = "YES" if g <= 21000 else "NO"
                            g = solve_gross_from_inhand(val, is_staff=(not is_h), is_helper=is_h, esic_opt=esic_r, pt_val=pt_v)
                    elif 'ctc' in mode:
                        esic_r = "YES" if ("YES" in esic_val or ("AUTO" in esic_val and (val/12.0) <= 22000)) else "NO"
                        g = solve_gross_from_annual_ctc(val, is_staff=(not is_h), is_helper=is_h, esic_opt=esic_r, pt_val=pt_v)
                        if "AUTO" in esic_val:
                            esic_r = "YES" if g <= 21000 else "NO"
                            g = solve_gross_from_annual_ctc(val, is_staff=(not is_h), is_helper=is_h, esic_opt=esic_r, pt_val=pt_v)
                    else:
                        g = val
                        esic_r = "YES" if ("YES" in esic_val or ("AUTO" in esic_val and g <= 21000)) else "NO"

                    brk_rec = compute_salary_breakdown(g, is_staff=(not is_h), is_helper=is_h, esic_opt=esic_r, pt_val=pt_v)
                    rec['gross'] = brk_rec['gross']
                    rec['salary_breakdown'] = brk_rec
                    rec['brk'] = brk_rec
                    rec['annual_ctc'] = brk_rec['annual_ctc']
                    rec['in_hand'] = brk_rec['in_hand']
                    processed_records.append(rec)

                # Show Preview Table
                preview_rows = []
                for r in processed_records:
                    preview_rows.append({
                        'Candidate ID': r.get('emp_id', '-'),
                        'Candidate Name': r.get('candidate_name', '-'),
                        'Designation': r.get('designation', '-'),
                        'DOJ': r.get('doj', '-'),
                        'Monthly Gross (₹)': f"₹ {r['gross']:,.2f}",
                        'Net In-Hand (₹)': f"₹ {r['in_hand']:,.2f}",
                        'Annual CTC (₹)': f"₹ {r['annual_ctc']:,.2f}",
                        'Status': 'Ready ✅'
                    })
                st.dataframe(pd.DataFrame(preview_rows), use_container_width=True)

                st.markdown("##### 3. Batch Generate & Download")
                co_data = {
                    'establishment_name': est_name,
                    'company_name': est_name,
                    'company_address': comp_addr,
                    'signatory_name': sig_name,
                    'signatory_title': sig_title,
                    'location': site_loc,
                    'site': site_loc
                }

                bulk_lh = st.radio(
                    "Paper Style for Bulk Letters:",
                    ["📄 Digital Letterhead (Includes company header artwork)", "🖨️ Pre-Printed Stationery (1.80\" Blank top margin)"],
                    key="bulk_offer_lh_choice"
                )
                with_lh_bool = "Digital" in bulk_lh

                bb1, bb2, bb3 = st.columns(3)

                # Bulk ZIP of PDFs
                with bb1:
                    if st.button("📦 Generate All Offer PDFs (ZIP)", key="btn_bulk_offer_pdf_zip", type="primary", use_container_width=True):
                        with st.spinner(f"Generating {len(processed_records)} offer letters via Word COM..."):
                            zip_pdf_buf = generate_joining_offer_bulk_zip(processed_records, co_data, with_letterhead=with_lh_bool, doc_type='pdf')
                            st.session_state['bulk_offer_pdf_zip'] = zip_pdf_buf.getvalue()
                            st.success(f"✅ Generated {len(processed_records)} Offer PDFs!")

                    if st.session_state.get('bulk_offer_pdf_zip'):
                        st.download_button(
                            "⬇️ Download Bulk PDFs (.zip)",
                            data=st.session_state['bulk_offer_pdf_zip'],
                            file_name=f"Bulk_Offer_Letters_PDF_{datetime.today().strftime('%Y%m%d')}.zip",
                            mime="application/zip",
                            use_container_width=True
                        )

                # Consolidated Single PDF
                with bb2:
                    if st.button("📄 Generate Consolidated Master PDF", key="btn_bulk_offer_master_pdf", use_container_width=True):
                        with st.spinner(f"Merging {len(processed_records)} letters into single Master PDF..."):
                            master_pdf_buf = generate_consolidated_joining_offer_pdf(processed_records, co_data, with_letterhead=with_lh_bool)
                            st.session_state['bulk_offer_master_pdf'] = master_pdf_buf.getvalue()
                            st.success(f"✅ Master PDF ({len(processed_records) * 3} pages) ready for 1-click batch printing!")

                    if st.session_state.get('bulk_offer_master_pdf'):
                        st.download_button(
                            "⬇️ Download Master PDF",
                            data=st.session_state['bulk_offer_master_pdf'],
                            file_name=f"Consolidated_Offer_Letters_{datetime.today().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

                # Bulk ZIP of Word docs
                with bb3:
                    if st.button("📝 Generate All Word Docs (ZIP)", key="btn_bulk_offer_docx_zip", use_container_width=True):
                        with st.spinner(f"Generating {len(processed_records)} Word documents..."):
                            zip_docx_buf = generate_joining_offer_bulk_zip(processed_records, co_data, with_letterhead=with_lh_bool, doc_type='docx')
                            st.session_state['bulk_offer_docx_zip'] = zip_docx_buf.getvalue()
                            st.success(f"✅ Generated {len(processed_records)} Word Docs!")

                    if st.session_state.get('bulk_offer_docx_zip'):
                        st.download_button(
                            "⬇️ Download Bulk Word Docs (.zip)",
                            data=st.session_state['bulk_offer_docx_zip'],
                            file_name=f"Bulk_Offer_Letters_DOCX_{datetime.today().strftime('%Y%m%d')}.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
