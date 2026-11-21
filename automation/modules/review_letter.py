import streamlit as st
from datetime import datetime
from automation.config import load_settings
from automation.utils.letter_generators import (
    generate_review_docx, generate_review_pdf
)

def render(selected_site):
    settings = load_settings()
    st.subheader(f"⭐ Performance Review & Confirmation Letter Generator (Site: {selected_site})")
    
    est_name = settings.get('establishment_name', "AAIKRUPA INFRATECH PVT. LTD.")
    comp_addr = settings.get('company_address', "Mundra-Kachchh Highway, Mundra, Gujarat - 370421")
    sig_name = settings.get('signatory_name', "Tarun Swami")
    sig_title = settings.get('signatory_title', "Authorized Signatory / Managing Director")

    st.markdown("### 📋 Fill Performance Review & Service Confirmation Details")
    
    c1, c2 = st.columns(2)
    with c1:
        ref_no = st.text_input("Review Ref No.", value=f"AIPL/HR/CONF/{datetime.today().year}/008")
        letter_date = st.text_input("Issue Date", value=datetime.today().strftime('%d-%m-%Y'))
        emp_name = st.text_input("Employee Full Name", value="DINESH B. MEHTA")
        emp_id = st.text_input("Employee ID / Code", value="EMP-1045")
        designation = st.text_input("Designation", value="Site Electrical Supervisor")

    with c2:
        site_loc = st.text_input("Operating Site", value=selected_site)
        prob_end = st.text_input("Probation End Date", value="31-03-2026")
        eff_date = st.text_input("Confirmation Effective Date", value="01-04-2026")
        rating = st.selectbox(
            "Overall Performance Assessment",
            ["Exceeds Expectations (Grade A+)", "Meets Expectations (Grade A)", "Satisfactory Progress (Grade B)", "Needs Improvement (Grade C)"],
            index=0
        )
        remarks = st.text_area("Key Performance Remarks", value="Demonstrated exceptional technical troubleshooting, site safety leadership, and zero absenteeism during the probation tenure.", height=70)

    data = {
        'establishment_name': est_name,
        'company_address': comp_addr,
        'ref_no': ref_no,
        'date': letter_date,
        'emp_name': emp_name,
        'emp_id': emp_id,
        'designation': designation,
        'site': site_loc,
        'probation_end_date': prob_end,
        'effective_date': eff_date,
        'rating': rating,
        'remarks': remarks,
        'signatory_name': sig_name,
        'signatory_title': sig_title
    }

    # Live Preview
    with st.expander("👁️ View Live Confirmation Letter Preview", expanded=True):
        st.markdown(f"""
        <div class="letter-preview-box">
            <div style="text-align: center; border-bottom: 2px solid #1E3A8A; padding-bottom: 8px;">
                <h3 style="margin: 0; color: #1E3A8A;">{est_name.upper()}</h3>
                <p style="margin: 2px 0; font-size: 12px; color: #64748B;">{comp_addr}</p>
            </div>
            <table style="width: 100%; margin-top: 10px; font-size: 13px;">
                <tr>
                    <td><b>Ref No:</b> {ref_no}</td>
                    <td style="text-align: right;"><b>Date:</b> {letter_date}</td>
                </tr>
            </table>
            <div style="text-align: center; margin: 15px 0;">
                <h4 style="text-decoration: underline; margin: 0; color: #0F172A;">CONFIRMATION OF EMPLOYMENT LETTER</h4>
            </div>
            <p><b>To,</b><br/>
            <b>{emp_name}</b> (Emp ID: {emp_id})<br/>
            Designation: {designation}<br/>
            Site: {site_loc}</p>
            
            <p><b>Subject: Confirmation of Employment Services upon Probation Completion</b></p>
            
            <p>Dear {emp_name},</p>
            <p>Consequent to the review of your performance during your probation period ending on <b>{prob_end}</b>, we take great pleasure in confirming your regular employment with <b>{est_name}</b> as <b>'{designation}'</b> with effect from <b>{eff_date}</b>.</p>
            
            <p><b>• Performance Rating:</b> {rating}<br/>
            <b>• Appraisal Remarks:</b> {remarks}</p>
            
            <p>All other terms of your appointment agreement remain in force. We look forward to your continuing growth and dedication with our company.</p>
            <p>Congratulations on achieving regular confirmation status!</p>
            
            <br/>
            <p><b>For, {est_name}</b><br/><br/><br/>
            <b>{sig_name}</b><br/>
            {sig_title}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### 📥 Download Confirmation Letter")
    b1, b2 = st.columns(2)
    with b1:
        if st.button("⚙️ Generate Word (.docx)", key="btn_rev_docx", type="primary", use_container_width=True):
            docx_buf = generate_review_docx(data)
            st.session_state['rev_docx_bytes'] = docx_buf.getvalue()
            st.session_state['rev_docx_name'] = f"Confirmation_{emp_name.replace(' ', '_')}.docx"
            st.success("✅ Word document generated!")

        if st.session_state.get('rev_docx_bytes'):
            st.download_button(
                "⬇️ Download Confirmation Letter (.docx)",
                data=st.session_state['rev_docx_bytes'],
                file_name=st.session_state['rev_docx_name'],
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

    with b2:
        if st.button("⚙️ Generate A4 PDF (.pdf)", key="btn_rev_pdf", use_container_width=True):
            pdf_buf = generate_review_pdf(data)
            st.session_state['rev_pdf_bytes'] = pdf_buf.getvalue()
            st.session_state['rev_pdf_name'] = f"Confirmation_{emp_name.replace(' ', '_')}.pdf"
            st.success("✅ PDF document generated!")

        if st.session_state.get('rev_pdf_bytes'):
            st.download_button(
                "⬇️ Download Confirmation Letter (.pdf)",
                data=st.session_state['rev_pdf_bytes'],
                file_name=st.session_state['rev_pdf_name'],
                mime="application/pdf",
                use_container_width=True
            )
