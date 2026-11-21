import streamlit as st
import pandas as pd
import io
from automation.config import load_settings
from automation.utils.excel_helpers import (
    parse_sheet_month_year, scan_and_validate_data, clean_num, format_doj, create_blank_template, safe_get
)
from automation.utils.word_generators import generate_form18_docx
from automation.utils.pdf_generators import generate_form18_pdf

def render(selected_site, cal_year=2026):
    settings = load_settings()
    st.subheader(f"📑 Statutory Compliance Hub & Registers (Site: {selected_site})")
    
    # 1. Establishment Details
    default_est = settings.get('establishment_name', "AAIKRUPA INFRATECH PVT. LTD.")
    default_pe_base = "M/S. MUNDRA PETROCHEM LIMITED, MUNDRA, KACHCHH" if "MUNDRA" in selected_site.upper() else f"{selected_site}, KUTCH"
    default_pe = settings.get('principal_employer', default_pe_base)
    default_lic = settings.get('license_no', "1199597230")

    tabs = st.tabs([
        "📄 Form 18 (Leave with Wages)", 
        "📥 Download Blank Compliance Templates", 
        "ℹ️ Statutory Rules & Guidelines"
    ])

    with tabs[0]:
        st.markdown("#### Form 18 — Register of Leave with Wages (Rule 94, Gujarat Factories Rules, 1963)")
        
        col1, col2 = st.columns(2)
        with col1:
            contractor_name = st.text_input("Contractor / Establishment Name", value=default_est, key="form18_est")
            license_no = st.text_input("License No.", value=default_lic, key="form18_lic")
        with col2:
            principal_employer = st.text_input("Principal Employer Name & Address", value=default_pe, key="form18_pe")

        st.markdown("---")
        uploaded_excel = st.file_uploader(
            f"📂 Upload Consolidated Leave Register Excel File (.xlsx)", 
            type=["xlsx"], 
            key="form18_excel"
        )
        
        master_df = None
        sheet_info = []
        if uploaded_excel:
            try:
                xls = pd.ExcelFile(uploaded_excel)
                # Parse valid sheets using the improved regex parser
                valid_sheets = [s for s in xls.sheet_names if parse_sheet_month_year(s, cal_year)[1] != 99]
                sheet_info = sorted([parse_sheet_month_year(s, cal_year) for s in valid_sheets], key=lambda x: (x[0], x[1]))
                
                if not sheet_info:
                    st.warning("⚠️ No valid monthly sheets recognized. Please ensure sheet names include a month (e.g. 'JAN', 'FEB', 'MARCH 2026').")

                all_records = []
                for yr, m_num, period_label, s_name in sheet_info:
                    df = pd.read_excel(uploaded_excel, sheet_name=s_name).dropna(how='all')
                    
                    errs, warns = scan_and_validate_data(df, s_name)
                    if errs:
                        st.markdown(f'<div class="error-box"><b>⚠️ Error Scan in Sheet [{s_name}]:</b><br/>' + "<br/>".join(errs) + '</div>', unsafe_allow_html=True)
                    if warns:
                        st.markdown(f'<div class="error-box" style="background-color: #FEF3C7; border-color: #F59E0B; color: #92400E;"><b>⚠️ Warning Scan in Sheet [{s_name}]:</b><br/>' + "<br/>".join(warns) + '</div>', unsafe_allow_html=True)
                    if not errs and not warns:
                        st.markdown(f'<div class="success-box">✅ Sheet [{s_name}] successfully scanned and synced!</div>', unsafe_allow_html=True)

                    # Safe column inspection: Form 18 template has 17 columns (indices 0 to 16)
                    if df.shape[1] >= 7:
                        for _, row in df.iterrows():
                            name = safe_get(row, 0).upper()
                            if not name or name == 'NAN': 
                                continue
                            father = safe_get(row, 1).upper()
                            if father in ['0', 'NAN', 'NONE', 'FATHER']: 
                                father = ""
                            emp_key = f"{name} (S/O {father})" if father else name
                            
                            days_worked = clean_num(safe_get(row, 6, 0))
                            normal_rate = clean_num(safe_get(row, 15, 0), is_float=True)
                            cash_equiv = clean_num(safe_get(row, 16, 0), is_float=True)
                            rate_leave = round(normal_rate + cash_equiv, 2)
                            
                            dept = safe_get(row, 2, selected_site)
                            desig = safe_get(row, 3, "").upper()
                            doj = format_doj(safe_get(row, 4, ""))
                            
                            layoff = clean_num(safe_get(row, 7, 0))
                            maternity = clean_num(safe_get(row, 8, 0))
                            leave_enjoyed = clean_num(safe_get(row, 9, 0))
                            total_9to12 = days_worked + layoff
                            reg_earned = clean_num(safe_get(row, 11, 0))
                            refused = clean_num(safe_get(row, 12, 0))
                            regular_bal = clean_num(safe_get(row, 13, 0))
                            leave_period = clean_num(safe_get(row, 14, 0))

                            all_records.append({
                                'EmpKey': emp_key, 'Year': yr, 'MonthNum': m_num, 'MonthLabel': period_label,
                                'SheetName': s_name, 'Name': name, 'Fathername': father,
                                'Department': dept,
                                'Designation': desig,
                                'DOJ': doj,
                                'PrincipalEmployer': principal_employer,
                                'DaysWorked': days_worked,
                                'Layoff': layoff,
                                'Maternity': maternity,
                                'LeaveEnjoyed': leave_enjoyed,
                                'Total9to12': total_9to12,
                                'RegLeaveEarned': reg_earned,
                                'Refused': refused,
                                'RegularCol': regular_bal,
                                'LeavePeriod': leave_period,
                                'NormalRate': normal_rate, 'CashEquiv': cash_equiv, 'RateLeaveWages': rate_leave,
                                'TotalLeaveWages': int(round(rate_leave * days_worked * 0.0833))
                            })
                if all_records:
                    master_df = pd.DataFrame(all_records)
            except Exception as e:
                st.error(f"❌ Error reading Excel file: {e}")

        # Form 18 Export Controls
        st.markdown("---")
        if master_df is not None and not master_df.empty:
            st.success(f"📊 Loaded {len(master_df['EmpKey'].unique())} unique employees across {len(sheet_info)} monthly sheets.")
            c1, c2 = st.columns(2)
            with c1:
                page_orient = st.selectbox("Page Layout", ["Landscape", "Portrait"], index=0, key="form18_orient")
            with c2:
                font_choice = st.selectbox("Font Style", ["Times New Roman", "Calibri", "Arial"], index=0, key="form18_font")
                
            avail_months = [(m[1], m[2], m[3]) for m in sheet_info]
            sel_m = st.selectbox("Select Target Month", options=avail_months, format_func=lambda x: f"{x[1]} (Sheet: {x[2]})", index=len(avail_months)-1, key="form18_sel_m")
            
            emp_list = master_df[master_df['MonthNum'] <= sel_m[0]]['EmpKey'].unique().tolist()
            sel_emps = st.multiselect("Select Employees for Form 18", options=emp_list, default=emp_list, key="form18_sel_emps")
            
            st.markdown("### 📥 Document Generation & Download")
            
            # Persistent generation caching to prevent download button disappearance
            b1, b2 = st.columns(2)
            with b1:
                if st.button("⚙️ Generate Word Document (.docx)", type="primary", use_container_width=True):
                    with st.spinner("Generating Word (.docx) document..."):
                        docx_buf = generate_form18_docx(master_df, sel_emps, contractor_name, sel_m[0], font_choice, page_orient, True)
                        st.session_state['form18_docx_bytes'] = docx_buf.getvalue()
                        st.session_state['form18_docx_name'] = f"Form18_{sel_m[1]}_{selected_site[:10]}.docx"
                
                if st.session_state.get('form18_docx_bytes'):
                    st.download_button(
                        "⬇️ Download Form 18 (.docx)", 
                        data=st.session_state['form18_docx_bytes'], 
                        file_name=st.session_state.get('form18_docx_name', 'Form18.docx'),
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
            
            with b2:
                if st.button("⚙️ Generate A4 PDF Document (.pdf)", use_container_width=True):
                    with st.spinner("Generating A4 PDF document..."):
                        pdf_buf = generate_form18_pdf(master_df, sel_emps, contractor_name, sel_m[0], page_orient, True)
                        st.session_state['form18_pdf_bytes'] = pdf_buf.getvalue()
                        st.session_state['form18_pdf_name'] = f"Form18_{sel_m[1]}_{selected_site[:10]}.pdf"

                if st.session_state.get('form18_pdf_bytes'):
                    st.download_button(
                        "⬇️ Download Form 18 (.pdf)", 
                        data=st.session_state['form18_pdf_bytes'], 
                        file_name=st.session_state.get('form18_pdf_name', 'Form18.pdf'),
                        mime="application/pdf",
                        use_container_width=True
                    )
        else:
            st.info("📂 Please upload your consolidated Excel file above to scan records and generate Form 18.")

    with tabs[1]:
        st.markdown("### 📥 Download Pre-Formatted Blank Excel Templates")
        st.write("Download ready-to-use statutory templates with pre-configured headers for your site:")
        
        c_t1, c_t2, c_t3 = st.columns(3)
        with c_t1:
            st.markdown("#### Form 18 (Leave with Wages)")
            st.download_button("⬇️ Download Form 18 Template", data=create_blank_template("Form 18"), file_name="Template_Form_18.xlsx", use_container_width=True)
            st.markdown("#### Form C (Loan & Advances)")
            st.download_button("⬇️ Download Form C Template", data=create_blank_template("Form C"), file_name="Template_Form_C.xlsx", use_container_width=True)

        with c_t2:
            st.markdown("#### Form A (Employee Register)")
            st.download_button("⬇️ Download Form A Template", data=create_blank_template("Form A"), file_name="Template_Form_A.xlsx", use_container_width=True)
            st.markdown("#### Form D (Attendance Register)")
            st.download_button("⬇️ Download Form D Template", data=create_blank_template("Form D"), file_name="Template_Form_D.xlsx", use_container_width=True)

        with c_t3:
            st.markdown("#### Form B (Wage Register)")
            st.download_button("⬇️ Download Form B Template", data=create_blank_template("Form B"), file_name="Template_Form_B.xlsx", use_container_width=True)
            st.markdown("#### Salary Slip Consolidated Sheet")
            st.download_button("⬇️ Download Salary Sheet Template", data=create_blank_template("Salary Sheet"), file_name="Template_Salary_Sheet.xlsx", use_container_width=True)

    with tabs[2]:
        st.markdown("### 📜 Statutory Compliance Reference Guide")
        st.markdown("""
        * **Form 18 — Gujarat Factories Rules, 1963 (Rule 94):**
          * Required to be maintained for every adult worker employed in the factory/contract site.
          * Calculates leave with wages earned (1 day for every 20 days worked).
        * **Form A — Employee Register (Code on Wages, 2019):**
          * Captures KYC details, Date of Joining, Father's Name, Aadhaar, Bank Details, and UAN.
        * **Form B — Wage Register:**
          * Mandatory record of Basic wages, DA, Overtime, Gross earnings, Deductions (PF, ESIC, PT), and Net wages paid.
        * **Form D — Muster Roll / Attendance Register:**
          * Daily 31-day presence register showing Present (P), Absent (A), Weekly Off (WO), and Paid Holidays (PH).
        """)
