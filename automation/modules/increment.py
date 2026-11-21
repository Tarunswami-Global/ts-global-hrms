import streamlit as st
import io
import os
import textwrap
import calendar
import pandas as pd
from datetime import datetime
from automation.config import load_settings
from automation.utils.letter_generators import (
    generate_increment_docx,
    generate_increment_pdf,
    generate_increment_bulk_zip,
    generate_consolidated_increment_pdf
)

def calculate_service_length(doj_str, letter_date_str):
    """
    Calculates exact duration between Date of Joining (DOJ) and Letter Issue Date.
    Formula: Total years and completed months from DOJ to Letter Date.
    """
    try:
        d1 = None
        d2 = None
        for fmt in ('%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%d.%m.%Y'):
            try:
                d1 = datetime.strptime(str(doj_str).strip(), fmt)
                break
            except ValueError:
                pass
        for fmt in ('%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%d.%m.%Y'):
            try:
                d2 = datetime.strptime(str(letter_date_str).strip(), fmt)
                break
            except ValueError:
                pass
                
        if d1 and d2 and d2 >= d1:
            years = d2.year - d1.year
            months = d2.month - d1.month
            days = d2.day - d1.day
            
            if days < 0:
                months -= 1
                prev_m = d2.month - 1 if d2.month > 1 else 12
                prev_y = d2.year if d2.month > 1 else d2.year - 1
                _, max_days = calendar.monthrange(prev_y, prev_m)
                days += max_days
                
            if months < 0:
                years -= 1
                months += 12
                
            parts = []
            if years > 0:
                parts.append(f"{years} Year{'s' if years > 1 else ''}")
            if months > 0:
                parts.append(f"{months} Month{'s' if months > 1 else ''}")
            if days > 0 and years == 0 and months == 0:
                parts.append(f"{days} Day{'s' if days > 1 else ''}")
                
            return " ".join(parts) if parts else "Less than 1 Month"
    except Exception:
        pass
    return "2 Years"

def render(selected_site):
    settings = load_settings()
    default_est = settings.get('establishment_name', "AAIKRUPA INFRATECH PVT. LTD.")
    default_addr = settings.get('company_address', "Shop No. 18, Ashok Vatika, Dhrab, Mundra, Kutch, Gujarat - 370421")
    sig_name = settings.get('signatory_name', "Tarun Swami")
    sig_title = settings.get('signatory_title', "Authorized Signatory / Managing Director")

    st.subheader("📈 Official Salary Increment & Appraisal Letter Generator")

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
            key="inc_comp_choice"
        )
        if comp_choice == "➕ Custom Company Name":
            est_name = st.text_input("Enter Company Full Name", value="ASHAPURA INFRATECH", key="inc_custom_comp")
        else:
            est_name = comp_choice

        comp_addr = st.text_input("Company Address (For Header / Footer)", value=default_addr, key="inc_comp_addr")

    with cfg_c2:
        site_choice = st.selectbox(
            "Select Operating Project Site",
            [
                "M/S. MUNDRA PETROCHEM LIMITED (MPL Piping 250)",
                "M/S. MUNDRA PETROCHEM LIMITED (MPL Struct 250)",
                "ADANI NEW INDUSTRIES LTD. (ANIL Project Site)",
                "TATA PROJECTS / LINDE INDIA SITE",
                "CENTRAL FABRICATION YARD (Mundra)",
                "➕ Custom Site / Work Location"
            ],
            index=0 if "MUNDRA" in selected_site.upper() else 2,
            key="inc_site_choice"
        )
        if site_choice == "➕ Custom Site / Work Location":
            site_loc = st.text_input("Enter Work Site / Location", value=selected_site, key="inc_custom_site")
        else:
            site_loc = site_choice

    st.markdown("---")

    # =========================================================================
    # DUAL OPERATION MODE TABS
    # =========================================================================
    tab1, tab2 = st.tabs([
        "👤 Mode 1: Single Employee Increment Letter",
        "📂 Mode 2: Bulk Increment Letters (Mail Merge Excel)"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: SINGLE EMPLOYEE INCREMENT LETTER
    # -------------------------------------------------------------------------
    with tab1:
        st.markdown("#### 📋 Fill Employee Appraisal & Revision Details")
        c1, c2 = st.columns(2)

        with c1:
            ref_no = st.text_input("Reference No.", value=f"AIPL/HR/INC/{datetime.today().year}/012", key="inc_ref")
            letter_date = st.text_input("Letter Issue Date (DD-MM-YYYY)", value=datetime.today().strftime('%d-%m-%Y'), key="inc_date")
            emp_name = st.text_input("Employee Full Name", value="AVDHESH KUMAR SHUKLA", key="inc_name")
            emp_id = st.text_input("Employee Code / ID", value="EMP-1088", key="inc_id")
            designation = st.text_input("Designation", value="Senior Plant Operator", key="inc_desig")
            department = st.text_input("Department", value="Operations / Mechanical", key="inc_dept")

        with c2:
            doj = st.text_input("Date of Joining (DOJ: DD-MM-YYYY)", value="15-03-2024", key="inc_doj")
            effective_date = st.text_input("Increment Effective Date", value="01-11-2026", key="inc_eff_date")
            
            # Auto-calculate service length: formula from DOJ to Letter Issue Date
            auto_length = calculate_service_length(doj, letter_date)
            
            # Reactive sync: when DOJ or Letter Date changes, update Length of Service automatically
            date_pair_tracker = f"{doj.strip()}_{letter_date.strip()}"
            if st.session_state.get('inc_last_dates_pair') != date_pair_tracker:
                st.session_state['inc_len_service'] = auto_length
                st.session_state['inc_last_dates_pair'] = date_pair_tracker
            elif 'inc_len_service' not in st.session_state:
                st.session_state['inc_len_service'] = auto_length

            length_service = st.text_input(
                "Length of Service (⚡ Auto-Formula: DOJ to Letter Date)", 
                key="inc_len_service"
            )

            curr_sal = st.number_input("Current Monthly Gross Salary (₹)", min_value=0.0, value=22000.0, step=500.0, key="inc_curr_sal")
            default_rev = max(float(curr_sal), 25500.0)
            rev_sal = st.number_input("Revised Monthly Gross Salary (₹)", min_value=0.0, value=default_rev, step=500.0, key="inc_rev_sal")

        inc_amt = rev_sal - curr_sal
        inc_pct = round((inc_amt / curr_sal) * 100, 2) if curr_sal > 0 else 0.0

        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Increment Hike", f"₹ {inc_amt:,.2f} / mo")
        with m2:
            st.metric("Hike Percentage", f"+{inc_pct} %")
        with m3:
            st.metric("Revised Gross", f"₹ {rev_sal:,.2f} / mo")
        with m4:
            st.metric("Revised Annual CTC", f"₹ {rev_sal * 12:,.2f} / yr")

        data = {
            'company_name': est_name,
            'establishment_name': est_name,
            'company_address': comp_addr,
            'ref_no': ref_no,
            'date': letter_date,
            'emp_name': emp_name,
            'candidate_name': emp_name,
            'emp_id': emp_id,
            'emp_code': emp_id,
            'designation': designation,
            'department': department,
            'site': site_loc,
            'doj': doj,
            'length_of_service': length_service,
            'length_service': length_service,
            'curr_salary': curr_sal,
            'rev_salary': rev_sal,
            'effective_date': effective_date,
            'effective_from': effective_date,
            'signatory_name': sig_name,
            'signatory_title': sig_title
        }

        # Live Preview (Zero-indenting to guarantee NO markdown code block triggers)
        with st.expander("👁️ View Live Increment Letter Preview (Exact 9-Row Table)", expanded=True):
            preview_card_html = textwrap.dedent(f"""
<div class="letter-preview-box" style="background:#ffffff; border:1px solid #CBD5E1; border-radius:8px; padding:28px; font-family:'Aptos Narrow', Arial, sans-serif; color:#0F172A; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);">
<div style="text-align: right; font-size: 13px; font-weight: bold; color: #334155;">
Date: {letter_date}
</div>
<div style="margin-top: 10px; font-size: 13px; line-height: 1.5;">
<b>To,</b><br/>
<b>Mr. {emp_name}</b><br/>
Employee Code: <b>{emp_id}</b><br/>
Designation: <b>{designation}</b><br/>
Department: <b>{department}</b><br/>
Project/Site: <b>{site_loc}</b>
</div>

<div style="margin: 16px 0 12px 0; font-size: 14.5px; font-weight: bold; color: #1E3A8A; text-decoration: underline;">
Subject: Salary Increment Letter
</div>

<p style="font-size: 13px; margin: 4px 0;">Dear <b>{emp_name}</b>,</p>
<p style="font-size: 13px; line-height: 1.5; margin: 6px 0;">
We are pleased to inform you that, after reviewing your performance, commitment, discipline, and valuable contribution towards the growth of <b>{est_name}</b>, the Management has approved a revision in your salary.
</p>
<p style="font-size: 13px; margin: 6px 0;">The revised salary details are as follows:</p>

<table style="width: 100%; border-collapse: collapse; font-size: 13px; margin: 12px 0; border: 1px solid #94A3B8;">
<thead>
<tr style="background: #F1F5F9; font-weight: bold;">
<th style="border: 1px solid #94A3B8; padding: 7px 12px; text-align: left; width: 45%;">Particulars</th>
<th style="border: 1px solid #94A3B8; padding: 7px 12px; text-align: left;">Details</th>
</tr>
</thead>
<tbody>
<tr><td style="border: 1px solid #94A3B8; padding: 5px 12px;">Employee Code</td><td style="border: 1px solid #94A3B8; padding: 5px 12px;"><b>{emp_id}</b></td></tr>
<tr><td style="border: 1px solid #94A3B8; padding: 5px 12px;">Designation</td><td style="border: 1px solid #94A3B8; padding: 5px 12px;"><b>{designation}</b></td></tr>
<tr><td style="border: 1px solid #94A3B8; padding: 5px 12px;">Date of Joining</td><td style="border: 1px solid #94A3B8; padding: 5px 12px;">{doj}</td></tr>
<tr style="background: #FFFBEB;"><td style="border: 1px solid #94A3B8; padding: 5px 12px; font-weight: bold; color: #B45309;">Length of Service</td><td style="border: 1px solid #94A3B8; padding: 5px 12px; font-weight: bold; color: #B45309;">{length_service}</td></tr>
<tr><td style="border: 1px solid #94A3B8; padding: 5px 12px;">Current Gross Salary</td><td style="border: 1px solid #94A3B8; padding: 5px 12px;">₹ {curr_sal:,.2f} /- per month</td></tr>
<tr style="background: #ECFDF5; font-weight: bold;"><td style="border: 1px solid #94A3B8; padding: 5px 12px; color: #065F46;">Revised Gross Salary</td><td style="border: 1px solid #94A3B8; padding: 5px 12px; color: #065F46;">₹ {rev_sal:,.2f} /- per month</td></tr>
<tr style="background: #EFF6FF; font-weight: bold;"><td style="border: 1px solid #94A3B8; padding: 5px 12px; color: #1D4ED8;">Increment Amount</td><td style="border: 1px solid #94A3B8; padding: 5px 12px; color: #1D4ED8;">₹ {inc_amt:,.2f} /- per month (+{inc_pct}%)</td></tr>
<tr><td style="border: 1px solid #94A3B8; padding: 5px 12px;">Effective From</td><td style="border: 1px solid #94A3B8; padding: 5px 12px;"><b>{effective_date}</b></td></tr>
</tbody>
</table>

<p style="font-size: 13px; line-height: 1.45; margin: 6px 0;">This salary revision has been granted in recognition of your consistent performance, dedication, professional attitude, and contribution towards the Company's objectives.</p>
<p style="font-size: 13px; line-height: 1.45; margin: 6px 0;">We appreciate your continued commitment and expect the same level of excellence and responsibility in the future.</p>
<p style="font-size: 13px; line-height: 1.45; margin: 6px 0;">All other terms and conditions of your employment shall remain unchanged.</p>
<p style="font-size: 13px; line-height: 1.45; margin: 6px 0;">We congratulate you on your well-deserved salary increment and wish you continued success with <b>{est_name}</b>.</p>
<p style="font-size: 13px; margin: 10px 0 4px 0;">With Best Wishes,</p>

<div style="margin-top: 18px; font-size: 13px; line-height: 1.5;">
<b>For {est_name}</b><br/>
<b>HR Department</b><br/><br/>
Authorized Signatory<br/>
<b>{est_name}</b>
</div>
<div style="margin-top: 18px; font-size: 11.5px; color: #64748B; font-style: italic;">
This is a system-generated salary revision letter and does not require a physical signature.
</div>
</div>
""").strip()
            st.markdown(preview_card_html, unsafe_allow_html=True)

        st.markdown("### 📥 Generate & Download Increment Letter")
        dl_c1, dl_c2, dl_c3 = st.columns(3)

        # 1. With Letterhead PDF
        with dl_c1:
            st.markdown("#### 🏢 Digital Letterhead PDF")
            st.caption("Includes official company artwork & top header banner.")
            if st.button("⚙️ Generate PDF (With Letterhead)", key="btn_s_inc_pdf_lh", type="primary", use_container_width=True):
                with st.spinner("Generating 1-page Letterhead PDF..."):
                    pdf_buf = generate_increment_pdf(data, with_letterhead=True)
                    st.session_state['s_inc_pdf_lh_bytes'] = pdf_buf.getvalue()
                    st.session_state['s_inc_pdf_lh_name'] = f"Increment_{emp_id}_{emp_name.replace(' ', '_')}_With_LH.pdf"
                    
                    # Generate live page preview of the PDF
                    try:
                        import pypdfium2 as pdfium
                        pdf_doc = pdfium.PdfDocument(pdf_buf.getvalue())
                        st.session_state['s_inc_pdf_lh_preview_img'] = pdf_doc[0].render(scale=1.5).to_pil()
                        pdf_doc.close()
                    except Exception:
                        pass
                    st.success("✅ Letterhead PDF ready!")

            if st.session_state.get('s_inc_pdf_lh_bytes'):
                st.download_button(
                    "⬇️ Download PDF (With Letterhead)",
                    data=st.session_state['s_inc_pdf_lh_bytes'],
                    file_name=st.session_state['s_inc_pdf_lh_name'],
                    mime="application/pdf",
                    use_container_width=True
                )
            if st.session_state.get('s_inc_pdf_lh_preview_img'):
                with st.expander("📄 View Letterhead PDF Snapshot", expanded=False):
                    st.image(st.session_state['s_inc_pdf_lh_preview_img'], caption="Exact 1-Page Letterhead PDF Preview", use_container_width=True)

        # 2. Plain Paper PDF (Without Letterhead)
        with dl_c2:
            st.markdown("#### 📄 Pre-Printed Paper PDF")
            st.caption("1.80\" top margin for feeding directly into physical letterhead printer.")
            if st.button("⚙️ Generate PDF (Plain / Without LH)", key="btn_s_inc_pdf_plain", use_container_width=True):
                with st.spinner("Generating 1-page Plain PDF..."):
                    pdf_plain_buf = generate_increment_pdf(data, with_letterhead=False)
                    st.session_state['s_inc_pdf_plain_bytes'] = pdf_plain_buf.getvalue()
                    st.session_state['s_inc_pdf_plain_name'] = f"Increment_{emp_id}_{emp_name.replace(' ', '_')}_Plain_Stationery.pdf"
                    
                    # Generate live page preview of the plain PDF
                    try:
                        import pypdfium2 as pdfium
                        pdf_doc2 = pdfium.PdfDocument(pdf_plain_buf.getvalue())
                        st.session_state['s_inc_pdf_plain_preview_img'] = pdf_doc2[0].render(scale=1.5).to_pil()
                        pdf_doc2.close()
                    except Exception:
                        pass
                    st.success("✅ Plain Stationery PDF ready!")

            if st.session_state.get('s_inc_pdf_plain_bytes'):
                st.download_button(
                    "⬇️ Download PDF (Without Letterhead)",
                    data=st.session_state['s_inc_pdf_plain_bytes'],
                    file_name=st.session_state['s_inc_pdf_plain_name'],
                    mime="application/pdf",
                    use_container_width=True
                )
            if st.session_state.get('s_inc_pdf_plain_preview_img'):
                with st.expander("📄 View Plain Stationery PDF Snapshot", expanded=False):
                    st.image(st.session_state['s_inc_pdf_plain_preview_img'], caption="Pre-Printed Stationery PDF Preview (1.80\" Top Margin)", use_container_width=True)

        # 3. Word Document (.docx)
        with dl_c3:
            st.markdown("#### 📝 Editable Word (.docx)")
            st.caption("Native Aptos Narrow format matching master template.")
            if st.button("⚙️ Generate Word (.docx)", key="btn_s_inc_docx", use_container_width=True):
                with st.spinner("Generating Word document..."):
                    docx_buf = generate_increment_docx(data, with_letterhead=True)
                    st.session_state['s_inc_docx_bytes'] = docx_buf.getvalue()
                    st.session_state['s_inc_docx_name'] = f"Increment_{emp_id}_{emp_name.replace(' ', '_')}.docx"
                    st.success("✅ Word document ready!")

            if st.session_state.get('s_inc_docx_bytes'):
                st.download_button(
                    "⬇️ Download Word (.docx)",
                    data=st.session_state['s_inc_docx_bytes'],
                    file_name=st.session_state['s_inc_docx_name'],
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )

    # -------------------------------------------------------------------------
    # TAB 2: BULK INCREMENT LETTERS (MAIL MERGE)
    # -------------------------------------------------------------------------
    with tab2:
        st.markdown("#### 📂 Bulk Increment Letter Generation (Excel Mail Merge)")
        st.info("💡 Upload an Excel or CSV file containing employee salary revision details to generate dozens of increment letters simultaneously in ZIP archives or 1 single batch PDF.")

        # Sample Template Generation
        sample_df = pd.DataFrame([
            {
                'Employee Code': 'EMP-1088',
                'Employee Name': 'AVDHESH KUMAR SHUKLA',
                'Designation': 'Senior Plant Operator',
                'Department': 'Operations / Mechanical',
                'Date of Joining (DOJ)': '15/03/2024',
                'Length of Service': '2 Years 8 Months',
                'Current Gross Salary': 22000,
                'Revised Gross Salary': 25500,
                'Effective From Date': '01/11/2026',
                'Operating Site': site_loc
            },
            {
                'Employee Code': 'EMP-1089',
                'Employee Name': 'VIKRAM SINGH CHAUHAN',
                'Designation': 'Mechanical Fitter',
                'Department': 'Mechanical',
                'Date of Joining (DOJ)': '01/06/2023',
                'Length of Service': '3 Years 5 Months',
                'Current Gross Salary': 28000,
                'Revised Gross Salary': 32000,
                'Effective From Date': '01/11/2026',
                'Operating Site': site_loc
            },
            {
                'Employee Code': 'EMP-1090',
                'Employee Name': 'MANISH SHARMA',
                'Designation': 'Rigger Foreman',
                'Department': 'Erection / Rigging',
                'Date of Joining (DOJ)': '10/01/2025',
                'Length of Service': '1 Year 10 Months',
                'Current Gross Salary': 32000,
                'Revised Gross Salary': 36500,
                'Effective From Date': '01/11/2026',
                'Operating Site': site_loc
            }
        ])
        sample_excel_buf = io.BytesIO()
        sample_df.to_excel(sample_excel_buf, index=False)
        sample_excel_buf.seek(0)

        st.download_button(
            "📥 Download Sample Excel Template (.xlsx)",
            data=sample_excel_buf,
            file_name="Salary_Increment_Bulk_Template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.write("")
        uploaded_file = st.file_uploader("Upload Employees Increment Excel / CSV Sheet", type=["xlsx", "xls", "csv"], key="bulk_inc_file")

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

                df.columns = [str(c).strip() for c in df.columns]
                st.success(f"✅ Successfully loaded {len(df)} employee increment records!")
                st.dataframe(df, use_container_width=True)

                records_list = []
                today_issue_date = datetime.today().strftime('%d-%m-%Y')
                for _, row in df.iterrows():
                    emp_code = str(row.get('Employee Code', row.get('emp_code', row.get('Emp Code', 'EMP-01')))).strip()
                    emp_name = str(row.get('Employee Name', row.get('Candidate Name', row.get('Name', 'Employee')))).strip()
                    desig = str(row.get('Designation', row.get('designation', 'Staff'))).strip()
                    dept = str(row.get('Department', row.get('department', 'Operations'))).strip()
                    doj_val = str(row.get('Date of Joining (DOJ)', row.get('Date of Joining', row.get('doj', '01/01/2024')))).strip()
                    eff_val = str(row.get('Effective From Date', row.get('Effective From', row.get('effective_date', '01/11/2026')))).strip()
                    
                    # Auto-formula fallback if Length of Service is empty or nan in Excel
                    len_raw = str(row.get('Length of Service', row.get('length_of_service', ''))).strip()
                    if not len_raw or len_raw.lower() in ('nan', 'none', ''):
                        len_val = calculate_service_length(doj_val, today_issue_date)
                    else:
                        len_val = len_raw
                    
                    try:
                        c_sal = float(row.get('Current Gross Salary', row.get('Current Salary', row.get('curr_salary', 22000))))
                    except Exception:
                        c_sal = 22000.0
                    try:
                        r_sal = float(row.get('Revised Gross Salary', row.get('Revised Salary', row.get('rev_salary', 25500))))
                    except Exception:
                        r_sal = 25500.0
                    
                    site_val = str(row.get('Operating Site', row.get('site', site_loc))).strip()

                    rec = {
                        'emp_code': emp_code,
                        'emp_id': emp_code,
                        'emp_name': emp_name,
                        'candidate_name': emp_name,
                        'designation': desig,
                        'department': dept,
                        'doj': doj_val,
                        'length_of_service': len_val,
                        'curr_salary': c_sal,
                        'rev_salary': r_sal,
                        'effective_date': eff_val,
                        'effective_from': eff_val,
                        'site': site_val
                    }
                    records_list.append(rec)

                company_base_data = {
                    'company_name': est_name,
                    'establishment_name': est_name,
                    'company_address': comp_addr,
                    'date': today_issue_date,
                    'signatory_name': sig_name,
                    'signatory_title': sig_title
                }

                st.markdown("### 📦 Bulk Generation & Download Actions")
                b_c1, b_c2 = st.columns(2)
                b_c3, b_c4 = st.columns(2)

                # 1. Bulk ZIP With Letterhead
                with b_c1:
                    if st.button("🏢 Generate Bulk ZIP (PDF With Letterhead)", key="btn_b_inc_zip_lh", use_container_width=True):
                        with st.spinner(f"Generating {len(records_list)} letterhead PDFs..."):
                            zip_lh = generate_increment_bulk_zip(records_list, company_base_data, with_letterhead=True, doc_type='pdf')
                            st.session_state['b_inc_zip_lh_bytes'] = zip_lh.getvalue()
                            st.success("✅ Bulk Letterhead ZIP Ready!")

                    if st.session_state.get('b_inc_zip_lh_bytes'):
                        st.download_button(
                            "⬇️ Download Bulk ZIP (With Letterhead)",
                            data=st.session_state['b_inc_zip_lh_bytes'],
                            file_name=f"Increments_Letterhead_{len(records_list)}_Staff.zip",
                            mime="application/zip",
                            use_container_width=True
                        )

                # 2. Bulk ZIP Without Letterhead (Pre-printed Stationery)
                with b_c2:
                    if st.button("📄 Generate Bulk ZIP (Plain PDFs for Stationery)", key="btn_b_inc_zip_plain", use_container_width=True):
                        with st.spinner(f"Generating {len(records_list)} plain stationery PDFs..."):
                            zip_plain = generate_increment_bulk_zip(records_list, company_base_data, with_letterhead=False, doc_type='pdf')
                            st.session_state['b_inc_zip_plain_bytes'] = zip_plain.getvalue()
                            st.success("✅ Bulk Plain Stationery ZIP Ready!")

                    if st.session_state.get('b_inc_zip_plain_bytes'):
                        st.download_button(
                            "⬇️ Download Bulk ZIP (Plain Stationery)",
                            data=st.session_state['b_inc_zip_plain_bytes'],
                            file_name=f"Increments_Plain_Stationery_{len(records_list)}_Staff.zip",
                            mime="application/zip",
                            use_container_width=True
                        )

                # 3. Bulk ZIP Word Documents (.docx)
                with b_c3:
                    if st.button("📝 Generate Bulk ZIP (Word .docx files)", key="btn_b_inc_zip_docx", use_container_width=True):
                        with st.spinner(f"Generating {len(records_list)} editable Word documents..."):
                            zip_docx = generate_increment_bulk_zip(records_list, company_base_data, with_letterhead=True, doc_type='docx')
                            st.session_state['b_inc_zip_docx_bytes'] = zip_docx.getvalue()
                            st.success("✅ Bulk Word (.docx) ZIP Ready!")

                    if st.session_state.get('b_inc_zip_docx_bytes'):
                        st.download_button(
                            "⬇️ Download Bulk ZIP (.docx)",
                            data=st.session_state['b_inc_zip_docx_bytes'],
                            file_name=f"Increments_Word_Docs_{len(records_list)}_Staff.zip",
                            mime="application/zip",
                            use_container_width=True
                        )

                # 4. Consolidated Continuous Batch PDF (1 File for Printing All)
                with b_c4:
                    if st.button("📚 Generate Consolidated PDF (1 File for Batch Print)", key="btn_b_inc_merged_pdf", type="primary", use_container_width=True):
                        with st.spinner(f"Merging {len(records_list)} increment letters into 1 single batch PDF..."):
                            merged_pdf = generate_consolidated_increment_pdf(records_list, company_base_data, with_letterhead=True)
                            st.session_state['b_inc_merged_pdf_bytes'] = merged_pdf.getvalue()
                            st.success("✅ Consolidated Batch Print PDF Ready!")

                    if st.session_state.get('b_inc_merged_pdf_bytes'):
                        st.download_button(
                            "⬇️ Download Consolidated Batch PDF (All in 1)",
                            data=st.session_state['b_inc_merged_pdf_bytes'],
                            file_name=f"All_Increments_Batch_Print_{len(records_list)}_Employees.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

            except Exception as e:
                st.error(f"❌ Error processing Excel file: {str(e)}")
