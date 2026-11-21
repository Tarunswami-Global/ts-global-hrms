import streamlit as st
from datetime import datetime
from automation.config import load_settings
from automation.utils.letter_generators import (
    generate_warning_docx, generate_warning_pdf
)

def render(selected_site):
    settings = load_settings()
    est_name = settings.get('establishment_name', "AAIKRUPA INFRATECH PVT. LTD.")
    comp_addr = settings.get('company_address', "Mundra-Kachchh Highway, Mundra, Gujarat - 370421")
    sig_name = settings.get('signatory_name', "Tarun Swami")
    sig_title = settings.get('signatory_title', "Authorized Signatory / Managing Director")

    st.subheader(f"⚠️ Disciplinary & Warning Notice Generator (Site: {selected_site})")

    st.markdown("### 📋 Fill Disciplinary / Warning Notice Details")
    
    c1, c2 = st.columns(2)
    with c1:
        ref_no = st.text_input("Notice Ref No.", value=f"AIPL/HR/WARN/{datetime.today().year}/019", key="warn_ref_no")
        letter_date = st.text_input("Notice Date", value=datetime.today().strftime('%d-%m-%Y'), key="warn_date")
        emp_name = st.text_input("Employee Full Name", value="SANJAY M. PARMAR", key="warn_name")
        emp_id = st.text_input("Employee ID / Code", value="EMP-1102", key="warn_id")
        designation = st.text_input("Designation", value="Site Welder / Fabricator", key="warn_desig")

    with c2:
        site_loc = st.text_input("Operating Site", value=selected_site, key="warn_site")
        warning_level = st.selectbox(
            "Notice Severity Level",
            ["FIRST WRITTEN WARNING", "SECOND WRITTEN WARNING", "FINAL SHOW-CAUSE NOTICE", "SAFETY VIOLATION MEMO"],
            index=0,
            key="warn_level"
        )
        violation_type = st.selectbox(
            "Category of Violation",
            [
                "Unapproved Absenteeism & Leaving Site Without Permission",
                "Non-Compliance with Mandatory Safety PPE on Project Site",
                "Negligence of Duty & Non-Adherence to Supervisor Instructions",
                "Insubordination / Misconduct with Co-Workers",
                "Damage or Negligent Handling of Company Equipment"
            ],
            index=0,
            key="warn_violation"
        )
        incident_date = st.text_input("Date of Incident / Absence", value=datetime.today().strftime('%d-%m-%Y'), key="warn_inc_date")
        reply_days = st.number_input("Response Deadline (Hours)", min_value=24, max_value=168, value=48, step=24, key="warn_reply_days")

    incident_details = st.text_area(
        "Incident Specifics & Factual Summary",
        value=f"Continuous absence from duty without prior leave approval or communication, causing operational disruption at {site_loc}.",
        height=80,
        key="warn_details"
    )

    warn_data = {
        'establishment_name': est_name,
        'company_address': comp_addr,
        'ref_no': ref_no,
        'date': letter_date,
        'emp_name': emp_name,
        'emp_id': emp_id,
        'designation': designation,
        'site': site_loc,
        'warn_type': warning_level,
        'warning_level': warning_level,
        'violation_type': violation_type,
        'incident_date': incident_date,
        'incident_details': incident_details,
        'reply_days': reply_days,
        'signatory_name': sig_name,
        'signatory_title': sig_title
    }

    # Live Preview
    with st.expander("👁️ View Live Disciplinary Notice Preview", expanded=True):
        st.markdown(f"""
        <div class="letter-preview-box" style="background-color: #0d1527; padding: 25px; border-radius: 8px; border: 1px solid #1E293B;">
            <div style="text-align: center; border-bottom: 2px solid #EF4444; padding-bottom: 8px;">
                <h3 style="margin: 0; color: #60A5FA;">{est_name.upper()}</h3>
                <p style="margin: 2px 0; font-size: 12px; color: #94A3B8;">{comp_addr}</p>
            </div>
            <table style="width: 100%; margin-top: 10px; font-size: 13px;">
                <tr>
                    <td><b>Ref No:</b> {ref_no}</td>
                    <td style="text-align: right;"><b>Date:</b> {letter_date}</td>
                </tr>
            </table>
            <div style="text-align: center; margin: 15px 0;">
                <h4 style="text-decoration: underline; margin: 0; color: #EF4444;">NOTICE: {warning_level.upper()}</h4>
            </div>
            <p><b>To,</b><br/>
            <b>{emp_name}</b> (Emp ID: {emp_id})<br/>
            Designation: {designation}<br/>
            Site: {site_loc}</p>
            
            <p><b>Subject: Formal Warning regarding '{violation_type}'</b></p>
            
            <p>Dear {emp_name},</p>
            <p>It has been officially brought to the notice of the management that on <b>{incident_date}</b>, you were involved in the following infraction:</p>
            <div style="background-color: #1e1b2e; border-left: 4px solid #EF4444; padding: 10px; font-style: italic; color: #FCA5A5;">
                "{incident_details}"
            </div>
            <p>Such actions constitute a serious breach of site discipline, industrial standing orders, and the company's code of conduct.</p>
            
            <p>You are hereby served this <b>{warning_level}</b>. You are instructed to submit your written explanation to the HR Department within <b>{reply_days} hours</b> of receipt of this notice, failing which it will be presumed that you have no defense and management may initiate formal disciplinary proceedings, including withholding of incentives or termination of service.</p>
            
            <br/>
            <p><b>For, {est_name}</b><br/><br/><br/>
            <b>{sig_name}</b><br/>
            {sig_title}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 📥 Download Notice")
    b1, b2 = st.columns(2)
    with b1:
        if st.button("⚙️ Generate Word (.docx)", key="btn_warn_docx", type="primary", use_container_width=True):
            docx_buf = generate_warning_docx(warn_data)
            st.session_state['warn_docx_bytes'] = docx_buf.getvalue()
            st.session_state['warn_docx_name'] = f"Warning_{emp_name.replace(' ', '_')}.docx"
            st.success("✅ Word document generated!")

        if st.session_state.get('warn_docx_bytes'):
            st.download_button(
                "⬇️ Download Warning Notice (.docx)",
                data=st.session_state['warn_docx_bytes'],
                file_name=st.session_state['warn_docx_name'],
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

    with b2:
        if st.button("⚙️ Generate A4 PDF (.pdf)", key="btn_warn_pdf", use_container_width=True):
            pdf_buf = generate_warning_pdf(warn_data)
            st.session_state['warn_pdf_bytes'] = pdf_buf.getvalue()
            st.session_state['warn_pdf_name'] = f"Warning_{emp_name.replace(' ', '_')}.pdf"
            st.success("✅ PDF document generated!")

        if st.session_state.get('warn_pdf_bytes'):
            st.download_button(
                "⬇️ Download Warning Notice (.pdf)",
                data=st.session_state['warn_pdf_bytes'],
                file_name=st.session_state['warn_pdf_name'],
                mime="application/pdf",
                use_container_width=True
            )
