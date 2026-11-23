import streamlit as st
import io
import textwrap
import pandas as pd
from datetime import datetime
from automation.config import load_settings, has_permission, render_permission_guard
from automation.utils.letter_generators import (
    generate_appointment_docx, 
    generate_appointment_pdf,
    generate_appointment_bulk_zip,
    generate_consolidated_appointment_pdf
)

def render(selected_site):
    settings = load_settings()
    default_est = settings.get('establishment_name', "AAIKRUPA INFRATECH PVT. LTD.")
    default_addr = settings.get('company_address', "Mundra-Kachchh Highway, Mundra, Gujarat - 370421")
    sig_name = settings.get('signatory_name', "Tarun Swami")
    sig_title = settings.get('signatory_title', "Authorized Signatory / Managing Director")

    st.subheader("📝 Official Appointment Letter Generator")

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
            key="appt_comp_choice"
        )
        if comp_choice == "➕ Custom Company Name":
            est_name = st.text_input("Enter Company Full Name", value="ASHAPURA INFRATECH", key="appt_custom_comp")
        else:
            est_name = comp_choice

        comp_addr = st.text_input("Company Address (For Header / Footer)", value=default_addr, key="appt_comp_addr")

    with cfg_c2:
        site_choice = st.selectbox(
            "Select Operating Project Site",
            [
                selected_site,
                "M/S. Mundra Petrochem Limited (MPL Piping 250)",
                "M/S. Mundra Petrochem Limited (MPL Struct 250)",
                "Adani New Industries Ltd. (ANIL Project Site)",
                "Tata Projects / Linde India Project Site",
                "Central Fabrication Yard (Mundra)",
                "➕ Custom Work Site / Location"
            ],
            index=0,
            key="appt_site_choice"
        )
        if site_choice == "➕ Custom Work Site / Location":
            site_loc = st.text_input("Enter Project Site Name", value=selected_site, key="appt_custom_site")
        else:
            site_loc = site_choice

    st.markdown("---")

    # =========================================================================
    # TABS: SINGLE CANDIDATE vs BULK EXCEL UPLOAD
    # =========================================================================
    tab_single, tab_bulk = st.tabs([
        "📝 Single Candidate Appointment",
        "📂 Bulk Upload from Excel"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: SINGLE CANDIDATE
    # -------------------------------------------------------------------------
    with tab_single:
        st.markdown("#### 📋 Fill Candidate Appointment Details")
        c1, c2 = st.columns(2)
        with c1:
            letter_date = st.text_input("Issue Date", value=datetime.today().strftime('%d/%m/%Y'), key="s_appt_date")
            candidate_name = st.text_input("Candidate Full Name", value="NAVEEN KUMAR MISHRA", key="s_appt_name")
            emp_code = st.text_input("Employee Code (Punch ID / Gate Pass No.)", value="8300013436", key="s_appt_code")
            designation = st.text_input("Designation / Role", value="FITTER", key="s_appt_desig")

        with c2:
            doj = st.text_input("Effective Date of Joining (DOJ)", value=datetime.today().strftime('%d/%m/%Y'), key="s_appt_doj")
            monthly_sal = st.number_input("Gross Monthly Salary (₹)", min_value=5000.0, value=30000.0, step=1000.0, key="s_appt_sal")
            notice_days = st.number_input("Termination Notice Period (Days)", min_value=15, max_value=90, value=60, step=15, key="s_appt_notice")

        single_data = {
            'company_name': est_name,
            'establishment_name': est_name,
            'company_address': comp_addr,
            'date': letter_date,
            'candidate_name': candidate_name,
            'emp_code': emp_code,
            'emp_id': emp_code,
            'designation': designation,
            'site': site_loc,
            'doj': doj,
            'monthly_salary': monthly_sal,
            'notice_days': notice_days,
            'signatory_name': sig_name,
            'signatory_title': sig_title
        }

        # Live Formatted Preview
        with st.expander("👁️ View Live Appointment Letter Preview (Exact Company Template)", expanded=True):
            appt_preview_html = textwrap.dedent(f"""
<div class="letter-preview-box" style="background-color: #ffffff; padding: 25px; border-radius: 8px; border: 1px solid #CBD5E1; font-family: 'Aptos Narrow', Arial, sans-serif; color: #0F172A; box-shadow: 0 4px 12px rgba(0,0,0,0.06);">
<div style="text-align: center; border-bottom: 2px solid #2563EB; padding-bottom: 8px; margin-bottom: 12px;">
<h3 style="margin: 0; color: #1E3A8A;">{est_name}</h3>
<p style="margin: 2px 0; font-size: 11.5px; color: #64748B;">{comp_addr}</p>
<h4 style="margin: 6px 0 0 0; text-decoration: underline; color: #0F172A;">APPOINTMENT LETTER</h4>
</div>
<table style="width: 100%; margin-bottom: 12px; font-size: 13px;">
<tr>
<td><b>Date:</b> {letter_date}</td>
<td style="text-align: right;"><b>Site:</b> {site_loc}</td>
</tr>
</table>
<p style="font-size: 13.5px; color: #0F172A; line-height: 1.5;">
<b>To,</b><br/>
<b>Mr. {candidate_name.upper()}</b><br/>
Employee Code: {emp_code}
</p>
<p style="font-size: 13.5px; color: #1E3A8A; font-weight: bold;"><b>Subject: Appointment Letter</b></p>
<p style="font-size: 13.5px; color: #0F172A;">Dear Sir,</p>

<p style="text-align: justify; line-height: 1.5; font-size: 13px; color: #334155;">
We are pleased to appoint you as <b>{designation.upper()}</b> with <b>{est_name}</b> with effect from <b>{doj}</b>.
</p>
<p style="text-align: justify; line-height: 1.5; font-size: 13px; color: #334155;">
Your employment is project-based and shall remain valid until the completion of the assigned project/site at <b>{site_loc}</b> or otherwise terminated by the Company as per its requirements and policies.
</p>
<p style="text-align: justify; line-height: 1.5; font-size: 13px; color: #334155;">
<b>Compensation:</b> Your Gross Monthly Salary shall be <b>₹ {monthly_sal:,.0f} per month</b>. Applicable statutory deductions such as PF, Professional Tax, Income Tax, or any other deductions as prescribed by law shall be made wherever applicable.
</p>

<p style="font-size: 13px; font-weight: bold; color: #1E3A8A; margin-top: 10px;">Terms & Conditions:</p>
<ul style="padding-left: 20px; font-size: 12.5px; color: #475569; line-height: 1.45;">
<li>You shall perform your duties diligently and comply with all Company Rules, Client Requirements, Site Regulations, Safety Standards, and Compliance Guidelines applicable at the workplace.</li>
<li>Salary, wages, benefits, business information, and other employment-related matters are strictly confidential and shall not be disclosed to any unauthorized person.</li>
<li>Any Company-issued Gate Pass, ID Card, Access Card, Uniform, Safety Equipment, Tools, Documents, or Assets shall remain the property of the Company.</li>
<li>Attendance shall be recorded only through the Company's approved attendance system.</li>
<li>Either party may terminate this employment by giving <b>{notice_days} days' prior written notice</b>.</li>
</ul>

<p style="font-size: 13px; color: #334155; margin-top: 10px;">
We welcome you to <b>{est_name}</b> and wish you a successful association with the Company.
</p>

<table style="width: 100%; margin-top: 20px; font-size: 13px;">
<tr>
<td style="vertical-align: top;">
<b>For {est_name}</b><br/><br/><br/>
<b>{sig_name}</b><br/>
Authorized Signatory
</td>
<td style="text-align: right; vertical-align: top;">
<b>EMPLOYEE ACCEPTANCE:</b><br/>
I, {candidate_name.upper()}, accept the terms.<br/><br/>
Signature: ______________________<br/>
Date: ______________
</td>
</tr>
</table>
</div>
""").strip()
            st.markdown(appt_preview_html, unsafe_allow_html=True)

        st.markdown("### 📥 Generate & Download Appointment Letter")
        if not has_permission("can_issue_appointment_letters"):
            render_permission_guard("can_issue_appointment_letters", "Generate & Issue Appointment Letters")
            st.info("ℹ️ Your role has read-only preview access. Issuing and generating official Appointment Contract Letters is restricted to HR Managers and Compliance Heads.")
        else:
            sc1, sc2, sc3 = st.columns(3)

            # 1. PDF With Letterhead
            with sc1:
                st.markdown("#### 🏢 Digital Letterhead PDF")
                st.caption("Complete letter with official header chevron banner & registered Mundra footer.")
                if st.button("⚙️ Generate PDF (With Letterhead)", key="btn_s_appt_pdf_lh", type="primary", use_container_width=True):
                    with st.spinner("Rendering vector PDF with letterhead..."):
                        pdf_lh_buf = generate_appointment_pdf(single_data, with_letterhead=True)
                        st.session_state['s_appt_pdf_lh_bytes'] = pdf_lh_buf.getvalue()
                        st.session_state['s_appt_pdf_lh_name'] = f"Appointment_{candidate_name.replace(' ', '_')}_WithLH.pdf"
                        st.success("✅ Generated successfully!")

                if st.session_state.get('s_appt_pdf_lh_bytes'):
                    st.download_button(
                        "⬇️ Download PDF (With Letterhead)",
                        data=st.session_state['s_appt_pdf_lh_bytes'],
                        file_name=st.session_state['s_appt_pdf_lh_name'],
                        mime="application/pdf",
                        use_container_width=True
                    )

            # 2. PDF Without Letterhead (Pre-printed Paper)
            with sc2:
                st.markdown("#### 📄 Pre-Printed Paper PDF")
                st.caption("Leaves exact 1.80\" top margin for feeding physical company letterhead stationery.")
                if st.button("⚙️ Generate PDF (Plain / Without LH)", key="btn_s_appt_pdf_plain", use_container_width=True):
                    with st.spinner("Rendering vector PDF for pre-printed paper..."):
                        pdf_plain_buf = generate_appointment_pdf(single_data, with_letterhead=False)
                        st.session_state['s_appt_pdf_plain_bytes'] = pdf_plain_buf.getvalue()
                        st.session_state['s_appt_pdf_plain_name'] = f"Appointment_{candidate_name.replace(' ', '_')}_Stationery.pdf"
                        st.success("✅ Generated successfully!")

                if st.session_state.get('s_appt_pdf_plain_bytes'):
                    st.download_button(
                        "⬇️ Download PDF (Without Letterhead)",
                        data=st.session_state['s_appt_pdf_plain_bytes'],
                        file_name=st.session_state['s_appt_pdf_plain_name'],
                        mime="application/pdf",
                        use_container_width=True
                    )

            # 3. Word Document (.docx)
            with sc3:
                st.markdown("#### 📝 Editable Word (.docx)")
                st.caption("Native Aptos Narrow docx formatted to exact 1 A4 page specifications.")
                if st.button("⚙️ Generate Word (.docx)", key="btn_s_appt_docx", use_container_width=True):
                    with st.spinner("Populating Word document..."):
                        docx_buf = generate_appointment_docx(single_data, with_letterhead=True)
                        st.session_state['s_appt_docx_bytes'] = docx_buf.getvalue()
                        st.session_state['s_appt_docx_name'] = f"Appointment_{candidate_name.replace(' ', '_')}.docx"
                        st.success("✅ Generated successfully!")

                if st.session_state.get('s_appt_docx_bytes'):
                    st.download_button(
                        "⬇️ Download Word Document (.docx)",
                        data=st.session_state['s_appt_docx_bytes'],
                        file_name=st.session_state['s_appt_docx_name'],
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )

    # -------------------------------------------------------------------------
    # TAB 2: BULK EXCEL UPLOAD
    # -------------------------------------------------------------------------
    with tab_bulk:
        st.markdown("#### 📂 Bulk Appointment Letter Generation")
        st.info("💡 Upload an Excel (.xlsx) or CSV file with employee records to issue appointments in bulk.")

        # Sample Template Generation
        sample_df = pd.DataFrame([
            {
                'Employee Code': 'EMP-83001',
                'Candidate Name': 'RAMESHWAR YADAV',
                'Designation': '6G WELDER',
                'Date of Joining (DOJ)': datetime.today().strftime('%d/%m/%Y'),
                'Gross Monthly Salary': 34000,
                'Operating Site': site_loc,
                'Notice Period Days': 60
            },
            {
                'Employee Code': 'EMP-83002',
                'Candidate Name': 'MOHAMMAD ALI KHAN',
                'Designation': 'PIPING FITTER',
                'Date of Joining (DOJ)': datetime.today().strftime('%d/%m/%Y'),
                'Gross Monthly Salary': 29500,
                'Operating Site': site_loc,
                'Notice Period Days': 60
            },
            {
                'Employee Code': 'EMP-83003',
                'Candidate Name': 'PANKAJ SOLANKI',
                'Designation': 'RIGGER FOREMAN',
                'Date of Joining (DOJ)': datetime.today().strftime('%d/%m/%Y'),
                'Gross Monthly Salary': 38000,
                'Operating Site': site_loc,
                'Notice Period Days': 60
            }
        ])
        sample_excel_buf = io.BytesIO()
        sample_df.to_excel(sample_excel_buf, index=False)
        sample_excel_buf.seek(0)

        st.download_button(
            "📥 Download Sample Excel Template (.xlsx)",
            data=sample_excel_buf,
            file_name="Appointment_Bulk_Template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.write("")
        uploaded_file = st.file_uploader("Upload Candidates Excel / CSV Sheet", type=["xlsx", "xls", "csv"], key="bulk_appt_file")

        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)

                # Clean column headers
                df.columns = [str(c).strip() for c in df.columns]
                st.success(f"✅ Successfully loaded {len(df)} candidate records!")
                st.dataframe(df, use_container_width=True)

                # Map rows to standard candidates list
                candidates_list = []
                for _, row in df.iterrows():
                    cand = {
                        'emp_code': str(row.get('Employee Code', row.get('emp_code', row.get('Emp Code', 'EMP-01')))).strip(),
                        'candidate_name': str(row.get('Candidate Name', row.get('candidate_name', row.get('Name', 'Candidate')))).strip(),
                        'designation': str(row.get('Designation', row.get('designation', row.get('Role', 'FITTER')))).strip(),
                        'doj': str(row.get('Date of Joining (DOJ)', row.get('doj', row.get('DOJ', datetime.today().strftime('%d/%m/%Y'))))).strip(),
                        'monthly_salary': row.get('Gross Monthly Salary', row.get('monthly_salary', row.get('Salary', 30000))),
                        'site': str(row.get('Operating Site', row.get('site', site_loc))).strip(),
                        'notice_days': str(row.get('Notice Period Days', row.get('notice_days', 60))).strip()
                    }
                    candidates_list.append(cand)

                company_base_data = {
                    'company_name': est_name,
                    'establishment_name': est_name,
                    'company_address': comp_addr,
                    'date': datetime.today().strftime('%d/%m/%Y'),
                    'signatory_name': sig_name,
                    'signatory_title': sig_title
                }

                st.markdown("### 📦 Bulk Generation & Download Actions")
                b_c1, b_c2 = st.columns(2)
                b_c3, b_c4 = st.columns(2)

                # 1. Bulk ZIP With Letterhead
                with b_c1:
                    if st.button("🏢 Generate Bulk ZIP (PDF With Letterhead)", key="btn_b_zip_lh", use_container_width=True):
                        with st.spinner(f"Generating {len(candidates_list)} letterhead PDFs..."):
                            zip_lh = generate_appointment_bulk_zip(candidates_list, company_base_data, with_letterhead=True, doc_type='pdf')
                            st.session_state['b_zip_lh_bytes'] = zip_lh.getvalue()
                            st.success("✅ Bulk Letterhead ZIP Ready!")

                    if st.session_state.get('b_zip_lh_bytes'):
                        st.download_button(
                            "⬇️ Download Bulk ZIP (With Letterhead)",
                            data=st.session_state['b_zip_lh_bytes'],
                            file_name=f"Appointments_Letterhead_{len(candidates_list)}_Workers.zip",
                            mime="application/zip",
                            use_container_width=True
                        )

                # 2. Bulk ZIP Without Letterhead (Pre-printed Stationery)
                with b_c2:
                    if st.button("📄 Generate Bulk ZIP (Plain PDFs for Stationery)", key="btn_b_zip_plain", use_container_width=True):
                        with st.spinner(f"Generating {len(candidates_list)} stationery PDFs..."):
                            zip_plain = generate_appointment_bulk_zip(candidates_list, company_base_data, with_letterhead=False, doc_type='pdf')
                            st.session_state['b_zip_plain_bytes'] = zip_plain.getvalue()
                            st.success("✅ Bulk Plain Stationery ZIP Ready!")

                    if st.session_state.get('b_zip_plain_bytes'):
                        st.download_button(
                            "⬇️ Download Bulk ZIP (Plain Stationery)",
                            data=st.session_state['b_zip_plain_bytes'],
                            file_name=f"Appointments_Stationery_{len(candidates_list)}_Workers.zip",
                            mime="application/zip",
                            use_container_width=True
                        )

                # 3. Bulk ZIP Word Documents
                with b_c3:
                    if st.button("📝 Generate Bulk ZIP (Word .docx files)", key="btn_b_zip_docx", use_container_width=True):
                        with st.spinner(f"Generating {len(candidates_list)} Word documents..."):
                            zip_docx = generate_appointment_bulk_zip(candidates_list, company_base_data, with_letterhead=True, doc_type='docx')
                            st.session_state['b_zip_docx_bytes'] = zip_docx.getvalue()
                            st.success("✅ Bulk Word (.docx) ZIP Ready!")

                    if st.session_state.get('b_zip_docx_bytes'):
                        st.download_button(
                            "⬇️ Download Bulk ZIP (Word .docx)",
                            data=st.session_state['b_zip_docx_bytes'],
                            file_name=f"Appointments_Word_{len(candidates_list)}_Workers.zip",
                            mime="application/zip",
                            use_container_width=True
                        )

                # 4. Consolidated Merged PDF (Batch Office Print)
                with b_c4:
                    if st.button("📚 Generate Consolidated PDF (1 File for Batch Print)", key="btn_b_merged_pdf", type="primary", use_container_width=True):
                        with st.spinner(f"Merging {len(candidates_list)} appointment letters into 1 PDF..."):
                            merged_pdf_buf = generate_consolidated_appointment_pdf(candidates_list, company_base_data, with_letterhead=False)
                            st.session_state['b_merged_pdf_bytes'] = merged_pdf_buf.getvalue()
                            st.success(f"✅ Consolidated {len(candidates_list)}-page PDF Ready for Printing!")

                    if st.session_state.get('b_merged_pdf_bytes'):
                        st.download_button(
                            "⬇️ Download Consolidated Batch Print PDF",
                            data=st.session_state['b_merged_pdf_bytes'],
                            file_name=f"Consolidated_Appointments_{len(candidates_list)}_Candidates.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

            except Exception as e:
                st.error(f"Error processing uploaded spreadsheet: {str(e)}")
