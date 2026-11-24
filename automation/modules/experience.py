import streamlit as st
import textwrap
from datetime import datetime
from automation.config import load_settings
from automation.utils.ui_components import render_entity_site_selector, render_employee_selector_widget
from automation.utils.employee_master import record_employee_relieving
from automation.utils.letter_generators import (
    generate_experience_docx, generate_experience_pdf
)

def render(selected_site):
    st.subheader(f"📜 Experience & Relieving Certificate Generator (Site: {selected_site})")

    # Unified Master Selector
    sel_config = render_entity_site_selector(key_prefix="exp", selected_site_default=selected_site)
    est_name = sel_config["company_name"]
    comp_addr = sel_config["company_address"]
    sig_name = sel_config["signatory_name"]
    sig_title = sel_config["signatory_title"]
    site_loc = sel_config["site_location"]

    st.markdown("---")
    st.markdown("### 📋 Fill Experience Certificate Details")

    # Fast-Fill Correlation from Employee Master
    picked_emp = render_employee_selector_widget(filter_status=["active", "confirmed", "exited"], key_prefix="exp")
    if picked_emp:
        st.info(f"⚡ Loaded employee for relieving: **{picked_emp.get('name')}** ({picked_emp.get('designation')} &bull; Joined: {picked_emp.get('doj')}). Generating certificate will mark status as 'Exited' and free up 1 CLRA license slot.")

    def_exp_name = picked_emp.get("name", "VIKRAM SINGH CHAUHAN") if picked_emp else "VIKRAM SINGH CHAUHAN"
    def_exp_desig = picked_emp.get("designation", "Senior Mechanical Engineer") if picked_emp else "Senior Mechanical Engineer"
    def_exp_dept = picked_emp.get("department", "Mechanical & Piping Execution") if picked_emp else "Mechanical & Piping Execution"
    def_exp_doj = picked_emp.get("doj", "01-05-2023") if picked_emp else "01-05-2023"
    emp_key_id = picked_emp.get("emp_id") if picked_emp else def_exp_name

    ec1, ec2 = st.columns(2)
    with ec1:
        exp_ref_no = st.text_input("Certificate Ref. No.", value=f"AIPL/HR/EXP/{datetime.today().year}/089", key="exp_ref_no")
        exp_date = st.text_input("Issue Date", value=datetime.today().strftime('%d %B %Y'), key="exp_date")
        exp_name = st.text_input("Employee Full Name", value=def_exp_name, key="exp_name")
        exp_desig = st.text_input("Designation", value=def_exp_desig, key="exp_desig")

    with ec2:
        exp_dept = st.text_input("Department / Discipline", value=def_exp_dept, key="exp_dept")
        exp_site = st.text_input("Operating Project Site", value=site_loc, key="exp_site")
        exp_doj = st.text_input("Date of Joining (DOJ)", value=def_exp_doj, key="exp_doj")
        exp_dor = st.text_input("Date of Relieving (DOR)", value=datetime.today().strftime('%d-%m-%Y'), key="exp_dor")

    exp_data = {
        'establishment_name': est_name,
        'company_address': comp_addr,
        'ref_no': exp_ref_no,
        'date': exp_date,
        'candidate_name': exp_name,
        'emp_name': exp_name,
        'designation': exp_desig,
        'department': exp_dept,
        'site': exp_site,
        'doj': exp_doj,
        'dor': exp_dor,
        'signatory_name': sig_name,
        'signatory_title': sig_title
    }

    # Live Formatted Preview
    with st.expander("👁️ View Live Certificate Preview", expanded=True):
        exp_preview_html = textwrap.dedent(f"""
<div class="letter-preview-box" style="background-color: #ffffff; padding: 25px; border-radius: 8px; border: 1px solid #CBD5E1; font-family: 'Aptos Narrow', Arial, sans-serif; color: #0F172A; box-shadow: 0 4px 12px rgba(0,0,0,0.06);">
<div style="text-align: center; border-bottom: 2px solid #2563EB; padding-bottom: 8px; margin-bottom: 12px;">
<h3 style="margin: 0; color: #1E3A8A;">{est_name}</h3>
<p style="margin: 2px 0; font-size: 11.5px; color: #64748B;">{comp_addr}</p>
</div>
<table style="width: 100%; margin-bottom: 15px; font-size: 13px;">
<tr>
<td><b>Ref. No.:</b> {exp_ref_no}</td>
<td style="text-align: right;"><b>Date:</b> {exp_date}</td>
</tr>
</table>
<div style="text-align: center; margin: 15px 0;">
<h3 style="margin: 0; color: #0F172A; text-decoration: underline; letter-spacing: 0.5px;">EXPERIENCE CERTIFICATE</h3>
<h4 style="margin: 4px 0 0 0; color: #64748B; font-weight: 600;">TO WHOMSOEVER IT MAY CONCERN</h4>
</div>

<p style="text-align: justify; line-height: 1.6; font-size: 13.5px; color: #334155;">
This is to certify that <b>{exp_name}</b> was associated with <b>{est_name}</b> in the capacity of <b>{exp_desig}</b> in <b>{exp_dept}</b> at our project site <b>{exp_site}</b>. He was associated with the Company from <b>{exp_doj}</b> to <b>{exp_dor}</b> and was responsible for managing and coordinating assigned project/site activities, ensuring effective execution of work, coordinating with the project team and supporting the achievement of organizational and project objectives.
</p>

<p style="text-align: justify; line-height: 1.6; font-size: 13.5px; color: #334155;">
During his tenure with the Company, he demonstrated professionalism, commitment and responsibility towards his assigned duties. He maintained a professional and responsible approach while coordinating with the project team and Management, contributing effectively to the smooth execution of assigned responsibilities.
</p>

<p style="text-align: justify; line-height: 1.6; font-size: 13.5px; color: #334155;">
His conduct and performance during his tenure with the Company were found to be satisfactory.
</p>

<p style="text-align: justify; line-height: 1.6; font-size: 13.5px; color: #334155;">
We appreciate his contribution and association with the organization and wish him success, growth and prosperity in all his future professional endeavours.
</p>

<p style="text-align: justify; line-height: 1.6; font-size: 13.5px; color: #334155;">
This certificate is being issued at his request for whatever purpose it may serve.
</p>

<div style="margin-top: 30px;">
<p style="margin: 0; font-weight: bold; color: #0F172A;">For {est_name}</p>
<br/><br/>
<p style="margin: 0; font-weight: bold; color: #0F172A;">Authorized Signatory</p>
</div>
</div>
""").strip()
        st.markdown(exp_preview_html, unsafe_allow_html=True)

    st.markdown("### 📥 Generate & Download Documents")
    col_lh, col_plain, col_docx = st.columns(3)

    # 1. PDF With Letterhead
    with col_lh:
        st.markdown("#### 🏢 Digital Letterhead PDF")
        st.caption("Complete letter with official header chevron banner & registered Mundra footer.")
        if st.button("⚙️ Generate PDF (With Letterhead)", key="btn_exp_pdf_lh", type="primary", use_container_width=True):
            with st.spinner("Rendering vector PDF with letterhead..."):
                record_employee_relieving(emp_key_id, {"dor": exp_dor, "ref_no": exp_ref_no})
                pdf_lh_buf = generate_experience_pdf(exp_data, with_letterhead=True)
                st.session_state['exp_pdf_lh_bytes'] = pdf_lh_buf.getvalue()
                st.session_state['exp_pdf_lh_name'] = f"Experience_Letterhead_{exp_name.replace(' ', '_')}.pdf"
                st.success("✅ Generated successfully! Worker marked as Exited in Central Master & 1 CLRA license slot freed up.")

        if st.session_state.get('exp_pdf_lh_bytes'):
            st.download_button(
                "⬇️ Download PDF (With Letterhead)",
                data=st.session_state['exp_pdf_lh_bytes'],
                file_name=st.session_state['exp_pdf_lh_name'],
                mime="application/pdf",
                use_container_width=True
            )

    # 2. PDF Without Letterhead (Pre-printed Paper)
    with col_plain:
        st.markdown("#### 📄 Pre-Printed Paper PDF")
        st.caption("Leaves exact 1.9\" top margin for feeding physical company letterhead stationery.")
        if st.button("⚙️ Generate PDF (Plain / Without LH)", key="btn_exp_pdf_plain", use_container_width=True):
            with st.spinner("Rendering vector PDF for pre-printed paper..."):
                pdf_plain_buf = generate_experience_pdf(exp_data, with_letterhead=False)
                st.session_state['exp_pdf_plain_bytes'] = pdf_plain_buf.getvalue()
                st.session_state['exp_pdf_plain_name'] = f"Experience_PlainPaper_{exp_name.replace(' ', '_')}.pdf"
                st.success("✅ Generated successfully!")

        if st.session_state.get('exp_pdf_plain_bytes'):
            st.download_button(
                "⬇️ Download PDF (Without Letterhead)",
                data=st.session_state['exp_pdf_plain_bytes'],
                file_name=st.session_state['exp_pdf_plain_name'],
                mime="application/pdf",
                use_container_width=True
            )

    # 3. Word Document (.docx)
    with col_docx:
        st.markdown("#### 📝 Editable Word (.docx)")
        st.caption("Native Aptos Narrow docx formatted to exact 1 A4 page specifications.")
        if st.button("⚙️ Generate Word (.docx)", key="btn_exp_docx", use_container_width=True):
            with st.spinner("Populating Word document..."):
                docx_buf = generate_experience_docx(exp_data, with_letterhead=True)
                st.session_state['exp_docx_bytes'] = docx_buf.getvalue()
                st.session_state['exp_docx_name'] = f"Experience_{exp_name.replace(' ', '_')}.docx"
                st.success("✅ Generated successfully!")

        if st.session_state.get('exp_docx_bytes'):
            st.download_button(
                "⬇️ Download Word Document (.docx)",
                data=st.session_state['exp_docx_bytes'],
                file_name=st.session_state['exp_docx_name'],
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
