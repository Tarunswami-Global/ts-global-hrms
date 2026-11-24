import streamlit as st
from datetime import datetime
from automation.config import load_settings, has_permission, render_permission_guard
from automation.utils.ui_components import render_entity_site_selector, render_employee_selector_widget
from automation.utils.employee_master import record_employee_warning
from automation.utils.letter_generators import (
    generate_warning_docx, generate_warning_pdf
)

def render(selected_site):
    st.subheader(f"⚠️ Disciplinary & Warning Notice Generator (Site: {selected_site})")

    # Unified Master Selector
    sel_config = render_entity_site_selector(key_prefix="warn", selected_site_default=selected_site)
    est_name = sel_config["company_name"]
    comp_addr = sel_config["company_address"]
    sig_name = sel_config["signatory_name"]
    sig_title = sel_config["signatory_title"]
    site_loc = sel_config["site_location"]

    st.markdown("---")
    st.markdown("### 📋 Fill Disciplinary / Warning Notice Details")
    
    # Fast-Fill Correlation from Employee Master
    picked_emp = render_employee_selector_widget(filter_status=["active", "confirmed"], key_prefix="warn")
    existing_warn_count = 0
    if picked_emp:
        existing_warns = picked_emp.get("warnings", [])
        existing_warn_count = len(existing_warns)
        if existing_warn_count >= 2:
            st.error(f"🚨 **CRITICAL NOTICE:** Worker **{picked_emp.get('name')}** already has **{existing_warn_count} prior warnings** on record! System recommends escalating to **FINAL SHOW-CAUSE NOTICE**.")
        elif existing_warn_count == 1:
            st.warning(f"⚠️ Worker **{picked_emp.get('name')}** has **1 previous warning** on record. Issuing a Second Written Warning.")
        else:
            st.info(f"⚡ Loaded worker: **{picked_emp.get('name')}** (Clean disciplinary record: 0 warnings).")

    def_warn_id = picked_emp.get("punch_id", picked_emp.get("emp_id", "EMP-1102")) if picked_emp else "EMP-1102"
    def_warn_name = picked_emp.get("name", "SANJAY M. PARMAR") if picked_emp else "SANJAY M. PARMAR"
    def_warn_desig = picked_emp.get("designation", "Site Welder / Fabricator") if picked_emp else "Site Welder / Fabricator"

    def_level_idx = 2 if existing_warn_count >= 2 else (1 if existing_warn_count == 1 else 0)

    c1, c2 = st.columns(2)
    with c1:
        ref_no = st.text_input("Notice Ref No.", value=f"AIPL/HR/WARN/{datetime.today().year}/019", key="warn_ref_no")
        letter_date = st.text_input("Notice Date", value=datetime.today().strftime('%d-%m-%Y'), key="warn_date")
        emp_name = st.text_input("Employee Full Name", value=def_warn_name, key="warn_name")
        emp_id = st.text_input("Employee ID / Code", value=def_warn_id, key="warn_id")
        designation = st.text_input("Designation", value=def_warn_desig, key="warn_desig")

    with c2:
        site_input = st.text_input("Operating Site", value=site_loc, key="warn_site")
        warning_level = st.selectbox(
            "Notice Severity Level",
            ["FIRST WRITTEN WARNING", "SECOND WRITTEN WARNING", "FINAL SHOW-CAUSE NOTICE", "SAFETY VIOLATION MEMO"],
            index=def_level_idx,
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
    if not has_permission("can_issue_disciplinary_notices"):
        render_permission_guard("can_issue_disciplinary_notices", "Issue Disciplinary & Show-Cause Notices")
        st.info("ℹ️ Your role has read-only preview access. Issuing formal disciplinary memos or show-cause notices is restricted to HR Managers and Super Admins.")
    else:
        b1, b2 = st.columns(2)
        with b1:
            if st.button("⚙️ Generate Word (.docx)", key="btn_warn_docx", type="primary", use_container_width=True):
                new_tot = record_employee_warning(emp_id, warn_data)
                docx_buf = generate_warning_docx(warn_data)
                st.session_state['warn_docx_bytes'] = docx_buf.getvalue()
                st.session_state['warn_docx_name'] = f"Warning_{emp_name.replace(' ', '_')}.docx"
                st.success(f"✅ Word notice generated & logged against employee record in Central Master (Total warnings on record: {new_tot})!")

            if st.session_state.get('warn_docx_bytes'):
                st.download_button(
                    "⬇️ Download Warning Notice (.docx)",
                    data=st.session_state['warn_docx_bytes'],
                    file_name=st.session_state['warn_docx_name'],
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )

        with b2:
            if st.button("⚙️ Generate A4 PDF (.pdf)", key="btn_warn_pdf", type="primary", use_container_width=True):
                new_tot = record_employee_warning(emp_id, warn_data)
                pdf_buf = generate_warning_pdf(warn_data)
                st.session_state['warn_pdf_bytes'] = pdf_buf.getvalue()
                st.session_state['warn_pdf_name'] = f"Warning_{emp_name.replace(' ', '_')}.pdf"
                st.success(f"✅ PDF notice generated & logged against employee record in Central Master (Total warnings on record: {new_tot})!")

            if st.session_state.get('warn_pdf_bytes'):
                st.download_button(
                    "⬇️ Download Warning Notice (.pdf)",
                    data=st.session_state['warn_pdf_bytes'],
                    file_name=st.session_state['warn_pdf_name'],
                    mime="application/pdf",
                    use_container_width=True
                )
