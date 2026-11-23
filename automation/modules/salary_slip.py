import streamlit as st
import pandas as pd
import calendar
import textwrap
from datetime import datetime
from automation.config import load_settings, has_permission, render_permission_guard
from automation.utils.excel_helpers import clean_num, safe_get, format_doj, create_blank_template
from automation.utils.letter_generators import (
    generate_salary_slip_docx, generate_salary_slip_pdf, num_to_words_inr
)

def render(selected_site):
    settings = load_settings()
    st.subheader(f"📄 Form XIX Salary Slip & Wage Terminal (Site: {selected_site})")
    
    est_name = settings.get('establishment_name', "AAIKRUPA INFRATECH PVT. LTD.")
    comp_addr = settings.get('company_address', "Shop No. 18, Ashok Vatika, Dhrab, Mundra, Kutch, Gujarat - 370421")

    tab1, tab2 = st.tabs(["📝 Single Employee Payslip (Form XIX)", "📂 Bulk Upload from Excel"])

    with tab1:
        st.markdown("### 👤 Generate Form XIX Statutory Wage Slip")
        
        c_m1, c_m2, c_m3, c_m4 = st.columns([1.2, 1, 1, 1])
        months_list = [
            "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", 
            "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"
        ]
        years_list = [2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030]

        with c_m1:
            selected_month = st.selectbox(
                "🗓️ Select Month", 
                months_list,
                index=months_list.index("OCTOBER") if "OCTOBER" in months_list else 9
            )
        with c_m2:
            selected_year = st.selectbox(
                "📅 Select Year",
                years_list,
                index=years_list.index(2026) if 2026 in years_list else 3
            )

        # Automatically calculate days in the selected month & year
        month_idx = months_list.index(selected_month) + 1
        default_days_count = calendar.monthrange(selected_year, month_idx)[1]

        with c_m3:
            days_in_month = st.number_input(
                "Total Days in Month", 
                min_value=28, 
                max_value=31, 
                value=int(default_days_count)
            )
        with c_m4:
            days_worked = st.number_input(
                "Paid Days", 
                min_value=0, 
                max_value=int(days_in_month), 
                value=min(26, int(days_in_month))
            )

        pay_month = f"{selected_month} {selected_year}"

        st.markdown("#### 1. Employee Identification Details")
        c1, c2, c3 = st.columns(3)
        with c1:
            emp_id = st.text_input("Employee Code (e.g. AMPCW / 83000...)", value="AMPCW2366595")
            emp_name = st.text_input("Employee Full Name", value="RAMESH KUMAR SHARMA")
            designation = st.text_input("Designation / Trade", value="SENIOR FITTER")
        with c2:
            department = st.text_input("Department", value="Piping & Fabrication")
            doj = st.text_input("Date of Joining", value="01-04-2023")
            bank_acc = st.text_input("Bank A/c No. & Bank", value="SBI - 918020034567891")
        with c3:
            uan = st.text_input("UAN (PF Number)", value="100987654321")
            esic = st.text_input("ESIC IP Number", value="3712345678")
            target_site = st.text_input("Site Location", value=selected_site)

        st.markdown("#### 2. Salary Calculation (Aaikrupa Statutory Formula)")
        auto_calc = st.checkbox("⚡ Auto-Calculate Components using Aaikrupa Statutory Rules (50% Basic, 40% HRA, 8.33% Bonus, 5% Leave, 12% PF, ESIC 0.75%)", value=True)
        
        target_gross = 32000.0
        if auto_calc:
            target_gross = st.number_input("Enter Target Monthly Gross Salary (₹)", min_value=10000.0, value=26000.0, step=1000.0)
            calc_basic = max(round(target_gross * 0.50), 13897.0)
            calc_hra = round(calc_basic * 0.40)
            calc_bonus = round(calc_basic * 0.0833)
            calc_leave = round(calc_basic * 0.05)
            calc_allowance = max(0.0, target_gross - (calc_basic + calc_hra + calc_bonus + calc_leave))
            calc_pf = round(calc_basic * 0.12)
            calc_pt = 200.0
            # ESIC applies if Gross <= 21,000 (or optional statutory coverage)
            calc_esic_emp = round(target_gross * 0.0075, 2) if target_gross <= 21000 else 0.0
            calc_esic_employer = round(target_gross * 0.0325, 2) if target_gross <= 21000 else 0.0
        else:
            calc_basic, calc_hra, calc_bonus, calc_leave, calc_allowance = 15000.0, 6000.0, 1250.0, 750.0, 2000.0
            calc_pf, calc_pt, calc_esic_emp, calc_esic_employer = 1800.0, 200.0, 195.0, 845.0

        col_earn, col_ded = st.columns(2)
        with col_earn:
            st.markdown("##### 💵 Earnings Breakdown (₹)")
            basic = st.number_input("Basic Salary (₹)", min_value=0.0, value=float(calc_basic), step=500.0)
            hra = st.number_input("House Rent Allowance - HRA (40%) (₹)", min_value=0.0, value=float(calc_hra), step=250.0)
            bonus = st.number_input("Statutory Bonus (8.33%) (₹)", min_value=0.0, value=float(calc_bonus), step=100.0)
            leave = st.number_input("Leave with Wages (5%) (₹)", min_value=0.0, value=float(calc_leave), step=100.0)
            allowance = st.number_input("Site / Other Allowance (₹)", min_value=0.0, value=float(calc_allowance), step=250.0)
            ot = st.number_input("Incentive / Overtime (₹)", min_value=0.0, value=1000.0, step=250.0)

        with col_ded:
            st.markdown("##### 🔻 Statutory Deductions (₹)")
            pf = st.number_input("Provident Fund - PF (12%) (₹)", min_value=0.0, value=float(calc_pf), step=100.0)
            pt = st.number_input("Professional Tax - PT (₹)", min_value=0.0, value=float(calc_pt), step=50.0)
            esic_emp = st.number_input("ESIC Employee Contribution (0.75%) (₹)", min_value=0.0, value=float(calc_esic_emp), step=25.0)
            advance = st.number_input("Advance / Loan Recovery (₹)", min_value=0.0, value=0.0, step=500.0)
            tds = st.number_input("Other Deductions / TDS (₹)", min_value=0.0, value=0.0, step=100.0)

        gross_salary = basic + hra + bonus + leave + allowance + ot
        total_ded = pf + pt + esic_emp + advance + tds
        net_pay = gross_salary - total_ded

        # Employer statutory calculations
        pf_employer = round(basic * 0.13, 2)
        esic_employer = round(gross_salary * 0.0325, 2) if esic_emp > 0 else 0.0

        # Summary Display
        st.markdown("---")
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            st.metric("Total Gross Earnings", f"₹ {gross_salary:,.2f}")
        with sc2:
            st.metric("Total Deductions", f"₹ {total_ded:,.2f}")
        with sc3:
            st.metric("Net Take-Home Pay", f"₹ {net_pay:,.2f}")
        with sc4:
            st.metric("Employer Statutory Share", f"₹ {(pf_employer + esic_employer):,.2f}")

        slip_data = {
            'establishment_name': est_name,
            'company_address': comp_addr,
            'pay_month': pay_month,
            'emp_id': emp_id,
            'emp_name': emp_name,
            'designation': designation,
            'department': department,
            'site': target_site,
            'doj': doj,
            'bank_acc': bank_acc,
            'uan': uan,
            'esic': esic,
            'days_in_month': days_in_month,
            'days_worked': days_worked,
            'basic': basic,
            'hra': hra,
            'bonus': bonus,
            'leave': leave,
            'allowance': allowance,
            'ot': ot,
            'pf': pf,
            'pt': pt,
            'esic_emp': esic_emp,
            'esic_employer': esic_employer,
            'pf_employer': pf_employer,
            'advance': advance,
            'tds': tds
        }

        # Live Formatted Preview
        with st.expander("👁️ View Live Form XIX Wage Slip Preview (1-Page A4 Geometry)", expanded=True):
            slip_preview_html = textwrap.dedent(f"""
<div class="letter-preview-box">
    <div style="text-align: center; border-bottom: 2px solid #1E3A8A; padding-bottom: 8px;">
        <h4 style="margin: 0; color: #1E3A8A;">SALARY SLIP</h4>
        <p style="margin: 0; font-size: 11px; font-weight: bold; color: #475569;">WAGE SLIP [SEE RULE 78 (2) (b)] FORM NO. XIX</p>
        <h3 style="margin: 2px 0; color: #0F172A;">{est_name.upper()}</h3>
        <p style="margin: 0; font-size: 11px; color: #64748B;">{comp_addr}</p>
        <p style="margin: 3px 0 0 0; font-weight: bold; font-size: 12px; color: #1E3A8A;">SALARY SLIP FOR THE MONTH OF: {pay_month.upper()}</p>
    </div>
    <table style="width: 100%; font-size: 12px; margin-top: 8px; border-collapse: collapse;">
        <tr>
            <td style="width: 25%;"><b>Employee Name:</b></td>
            <td style="width: 25%; font-weight: 600;">{emp_name}</td>
            <td style="width: 25%;"><b>UAN No.:</b></td>
            <td style="width: 25%;">{uan}</td>
        </tr>
        <tr>
            <td><b>Employee Code:</b></td>
            <td style="font-weight: 600;">{emp_id}</td>
            <td><b>ESIC No.:</b></td>
            <td>{esic}</td>
        </tr>
        <tr>
            <td><b>Designation:</b></td>
            <td>{designation}</td>
            <td><b>Bank Details:</b></td>
            <td>{bank_acc}</td>
        </tr>
        <tr>
            <td><b>Department / Site:</b></td>
            <td>{department} ({target_site})</td>
            <td><b>Month:</b></td>
            <td>{pay_month}</td>
        </tr>
        <tr>
            <td><b>Working Days:</b></td>
            <td>{days_in_month}</td>
            <td><b>Paid Days:</b></td>
            <td>{days_worked}</td>
        </tr>
    </table>
    <br/>
    <table style="width: 100%; font-size: 12px; border: 1px solid #CBD5E1; border-collapse: collapse;">
        <tr style="background-color: #83CCEB; color: #0F172A; font-weight: bold;">
            <th style="padding: 5px; border: 1px solid #CBD5E1; text-align: left;">Earnings</th>
            <th style="padding: 5px; border: 1px solid #CBD5E1; text-align: right;">Amount (₹)</th>
            <th style="padding: 5px; border: 1px solid #CBD5E1; text-align: left;">Deductions</th>
            <th style="padding: 5px; border: 1px solid #CBD5E1; text-align: right;">Amount (₹)</th>
        </tr>
        <tr>
            <td style="padding: 4px; border: 1px solid #CBD5E1;">Basic Salary</td>
            <td style="padding: 4px; border: 1px solid #CBD5E1; text-align: right;">₹ {basic:,.2f}</td>
            <td style="padding: 4px; border: 1px solid #CBD5E1;">Provident Fund (PF 12%)</td>
            <td style="padding: 4px; border: 1px solid #CBD5E1; text-align: right;">₹ {pf:,.2f}</td>
        </tr>
        <tr>
            <td style="padding: 4px; border: 1px solid #CBD5E1;">House Rent Allowance (HRA 40%)</td>
            <td style="padding: 4px; border: 1px solid #CBD5E1; text-align: right;">₹ {hra:,.2f}</td>
            <td style="padding: 4px; border: 1px solid #CBD5E1;">Professional Tax (PT)</td>
            <td style="padding: 4px; border: 1px solid #CBD5E1; text-align: right;">₹ {pt:,.2f}</td>
        </tr>
        <tr>
            <td style="padding: 4px; border: 1px solid #CBD5E1;">Statutory Bonus (8.33%)</td>
            <td style="padding: 4px; border: 1px solid #CBD5E1; text-align: right;">₹ {bonus:,.2f}</td>
            <td style="padding: 4px; border: 1px solid #CBD5E1;">Advance Recovery</td>
            <td style="padding: 4px; border: 1px solid #CBD5E1; text-align: right;">₹ {advance:,.2f}</td>
        </tr>
        <tr>
            <td style="padding: 4px; border: 1px solid #CBD5E1;">Leave with Wages (5%)</td>
            <td style="padding: 4px; border: 1px solid #CBD5E1; text-align: right;">₹ {leave:,.2f}</td>
            <td style="padding: 4px; border: 1px solid #CBD5E1;">Other Deductions</td>
            <td style="padding: 4px; border: 1px solid #CBD5E1; text-align: right;">₹ {tds:,.2f}</td>
        </tr>
        <tr>
            <td style="padding: 4px; border: 1px solid #CBD5E1;">Site / Other Allowance</td>
            <td style="padding: 4px; border: 1px solid #CBD5E1; text-align: right;">₹ {allowance:,.2f}</td>
            <td style="padding: 4px; border: 1px solid #CBD5E1; color: #1E40AF; font-weight: 600;">ESIC (Employee - 0.75%)</td>
            <td style="padding: 4px; border: 1px solid #CBD5E1; text-align: right; color: #1E40AF; font-weight: 600;">₹ {esic_emp:,.2f}</td>
        </tr>
        <tr>
            <td style="padding: 4px; border: 1px solid #CBD5E1;">Incentive / Overtime</td>
            <td style="padding: 4px; border: 1px solid #CBD5E1; text-align: right;">₹ {ot:,.2f}</td>
            <td style="padding: 4px; border: 1px solid #CBD5E1; color: #6D28D9;">ESIC (Employer - 3.25%)*</td>
            <td style="padding: 4px; border: 1px solid #CBD5E1; text-align: right; color: #6D28D9;">₹ {esic_employer:,.2f}</td>
        </tr>
        <tr style="background-color: #F8FAFC; font-weight: bold;">
            <td style="padding: 5px; border: 1px solid #CBD5E1; color: #15803D;">Gross Earnings</td>
            <td style="padding: 5px; border: 1px solid #CBD5E1; text-align: right; color: #15803D;">₹ {gross_salary:,.2f}</td>
            <td style="padding: 5px; border: 1px solid #CBD5E1; color: #DC2626;">Total Deductions</td>
            <td style="padding: 5px; border: 1px solid #CBD5E1; text-align: right; color: #DC2626;">₹ {total_ded:,.2f}</td>
        </tr>
    </table>
    <div style="background-color: #92D050; border: 1px solid #65A30D; padding: 10px; margin-top: 10px; border-radius: 6px; color: #0F172A;">
        <b style="font-size: 13px;">NET PAYABLE SALARY: ₹ {net_pay:,.2f}</b><br/>
        <i>({num_to_words_inr(net_pay)})</i>
    </div>
    <p style="font-size: 11px; color: #64748B; margin-top: 8px; text-align: center;">
        Note: This is a computer-generated salary slip and does not require a signature. *Employer statutory share (PF ₹{pf_employer:,.2f} + ESIC ₹{esic_employer:,.2f} = ₹{(pf_employer + esic_employer):,.2f}) is paid directly by the company. | For Aaikrupa Infratech Pvt. Ltd. (Authorized Signatory)
    </p>
</div>
""").strip()
            st.markdown(slip_preview_html, unsafe_allow_html=True)

        st.markdown("### 📥 Download Form XIX Salary Slip (Official 1-Page)")
        if not has_permission("can_generate_salary_slips"):
            render_permission_guard("can_generate_salary_slips", "Generate & Issue Form XIX Salary Slips")
            st.info("ℹ️ Your role is authorized to view wage computations in Read-Only mode. Generating signed PDF/Word salary slips is restricted to HR Managers and Super Admins.")
        else:
            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("🏢 PDF with Letterhead", key="btn_slip_pdf_lh", type="primary", use_container_width=True):
                    with st.spinner("Generating 1-Page PDF with Official Letterhead..."):
                        buf_pdf_lh = generate_salary_slip_pdf(slip_data, with_letterhead=True)
                        st.session_state['slip_pdf_lh'] = buf_pdf_lh.getvalue()
                        st.session_state['slip_pdf_lh_name'] = f"FormXIX_SalarySlip_WithLetterhead_{emp_id}_{pay_month.replace(' ', '_')}.pdf"
                        st.success("✅ PDF with Letterhead ready!")
                
                if st.session_state.get('slip_pdf_lh'):
                    st.download_button(
                        "⬇️ Download PDF (With Letterhead)",
                        data=st.session_state['slip_pdf_lh'],
                        file_name=st.session_state['slip_pdf_lh_name'],
                        mime="application/pdf",
                        use_container_width=True
                    )

            with b2:
                if st.button("📄 PDF without Letterhead", key="btn_slip_pdf_plain", use_container_width=True):
                    with st.spinner("Generating 1-Page PDF for Pre-printed Stationery..."):
                        buf_pdf_plain = generate_salary_slip_pdf(slip_data, with_letterhead=False)
                        st.session_state['slip_pdf_plain'] = buf_pdf_plain.getvalue()
                        st.session_state['slip_pdf_plain_name'] = f"FormXIX_SalarySlip_PlainStationery_{emp_id}_{pay_month.replace(' ', '_')}.pdf"
                        st.success("✅ PDF for Pre-printed Stationery ready!")
                
                if st.session_state.get('slip_pdf_plain'):
                    st.download_button(
                        "⬇️ Download PDF (Plain / Stationery)",
                        data=st.session_state['slip_pdf_plain'],
                        file_name=st.session_state['slip_pdf_plain_name'],
                        mime="application/pdf",
                        use_container_width=True
                    )

            with b3:
                if st.button("📝 Word Document (.docx)", key="btn_slip_docx", use_container_width=True):
                    with st.spinner("Generating Word (.docx) Format..."):
                        buf_docx = generate_salary_slip_docx(slip_data, with_letterhead=True)
                        st.session_state['single_slip_docx'] = buf_docx.getvalue()
                        st.session_state['single_slip_docx_name'] = f"FormXIX_SalarySlip_{emp_id}_{pay_month.replace(' ', '_')}.docx"
                        st.success("✅ Official Word Wage Slip ready!")
                
                if st.session_state.get('single_slip_docx'):
                    st.download_button(
                        "⬇️ Download Form XIX (.docx)",
                        data=st.session_state['single_slip_docx'],
                        file_name=st.session_state['single_slip_docx_name'],
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )

    with tab2:
        st.markdown("### 📂 Bulk Salary Slip Generation from Master Sheet")
        st.write("Upload your monthly payroll Excel sheet (e.g. `FORM-A,B,C,D for internal payroll sample format.xlsx`) to generate slips.")
        
        with st.expander("📥 Need Template? Download Blank Salary Sheet Excel"):
            st.download_button(
                "⬇️ Download Blank Salary Sheet Template (.xlsx)",
                data=create_blank_template("Salary Sheet"),
                file_name="Template_Salary_Sheet.xlsx"
            )

        bulk_file = st.file_uploader("Upload Salary Sheet (.xlsx)", type=["xlsx"], key="bulk_salary_file")
        if bulk_file:
            try:
                xls = pd.ExcelFile(bulk_file)
                target_sheet = "FORM-A,B,C" if "FORM-A,B,C" in xls.sheet_names else xls.sheet_names[0]
                df_salary = pd.read_excel(bulk_file, sheet_name=target_sheet)
                st.success(f"✅ Loaded Sheet [{target_sheet}] with {len(df_salary)} rows.")
                st.dataframe(df_salary.head(), use_container_width=True)

                selected_row = st.selectbox(
                    "Select Employee to Generate Official Slip",
                    options=range(min(len(df_salary), 200)),
                    format_func=lambda idx: f"{safe_get(df_salary.iloc[idx], 1, 'EMP')} - {safe_get(df_salary.iloc[idx], 10, safe_get(df_salary.iloc[idx], 2, 'Employee'))} ({safe_get(df_salary.iloc[idx], 11, 'Worker')})"
                )

                if selected_row is not None:
                    r = df_salary.iloc[selected_row]
                    emp_bulk_data = {
                        'establishment_name': est_name,
                        'company_address': comp_addr,
                        'pay_month': "CURRENT MONTH",
                        'emp_id': safe_get(r, 1, safe_get(r, 0, "EMP001")),
                        'emp_name': safe_get(r, 10, safe_get(r, 2, "Staff Name")),
                        'designation': safe_get(r, 11, safe_get(r, 3, "Worker")),
                        'department': safe_get(r, 9, selected_site),
                        'site': selected_site,
                        'doj': format_doj(safe_get(r, 5, "")),
                        'bank_acc': safe_get(r, 7, ''),
                        'uan': safe_get(r, 4, "N/A"),
                        'esic': safe_get(r, 5, "N/A"),
                        'days_in_month': 31,
                        'days_worked': clean_num(safe_get(r, 12, 26)),
                        'basic': clean_num(safe_get(r, 17, safe_get(r, 13, 0)), is_float=True),
                        'hra': clean_num(safe_get(r, 18, safe_get(r, 14, 0)), is_float=True),
                        'bonus': clean_num(safe_get(r, 19, 0), is_float=True),
                        'leave': clean_num(safe_get(r, 20, 0), is_float=True),
                        'allowance': clean_num(safe_get(r, 21, safe_get(r, 16, 0)), is_float=True),
                        'ot': clean_num(safe_get(r, 22, 0), is_float=True),
                        'pf': clean_num(safe_get(r, 26, safe_get(r, 18, 0)), is_float=True),
                        'pt': clean_num(safe_get(r, 27, 200), is_float=True),
                        'advance': clean_num(safe_get(r, 28, 0), is_float=True),
                        'tds': clean_num(safe_get(r, 29, 0), is_float=True)
                    }

                    b_c1, b_c2, b_c3 = st.columns(3)
                    with b_c1:
                        pdf_bulk_lh = generate_salary_slip_pdf(emp_bulk_data, with_letterhead=True)
                        st.download_button(
                            f"⬇️ {emp_bulk_data['emp_id']} PDF (With Letterhead)",
                            data=pdf_bulk_lh,
                            file_name=f"WageSlip_WithLetterhead_{emp_bulk_data['emp_id']}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    with b_c2:
                        pdf_bulk_plain = generate_salary_slip_pdf(emp_bulk_data, with_letterhead=False)
                        st.download_button(
                            f"⬇️ {emp_bulk_data['emp_id']} PDF (Plain / Stationery)",
                            data=pdf_bulk_plain,
                            file_name=f"WageSlip_PlainStationery_{emp_bulk_data['emp_id']}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    with b_c3:
                        docx_bulk = generate_salary_slip_docx(emp_bulk_data, with_letterhead=True)
                        st.download_button(
                            f"⬇️ {emp_bulk_data['emp_id']} Word Slip (.docx)",
                            data=docx_bulk,
                            file_name=f"WageSlip_{emp_bulk_data['emp_id']}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True
                        )
            except Exception as e:
                st.error(f"❌ Error reading Excel file: {e}")
