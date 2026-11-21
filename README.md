# 🚀 TS Global HR Automation & Compliance Suite

**Enterprise HRMS & Statutory Compliance Terminal**  
Developed for: **Aaikrupa Infratech Pvt. Ltd.** (Mundra / Kutch, Gujarat)  
Owner: **Tarun Swami**

---

## 📌 Overview

**TS Global HRMS** is a specialized, production-ready Streamlit web application designed for industrial contract workforce management and statutory compliance under Indian labor laws (Gujarat Factories Rules, 1963, and the Code on Wages frameworks).

### 🛠️ Key Modules & Capabilities

1. **⚖️ Statutory Compliance Hub (Forms A-D & 18)**:
   - **Form 18 (Register of Leave with Wages)**: Automatically processes consolidated multi-month Excel sheets under Rule 94 of Gujarat Factories Rules, 1963.
   - Dual exports in **editable Word (.docx)** and **ready-to-print A4 PDF (.pdf)**.
   - Ready-to-use **Blank Excel Templates** for Form 18, Form A (Employee Register), Form B (Wage Register), Form C (Loans/Advances), and Form D (Muster Roll / Attendance).

2. **📄 Salary Slip Generator & Payroll Terminal**:
   - **Single Payslip Generator**: Instant calculation of Gross Earnings, Deductions (PF, ESIC, PT, Advance, TDS), Net Take-Home Pay, and Indian Currency in words.
   - **Bulk Payslip Upload**: Upload monthly Excel sheets to generate and download individual payslips in Word & PDF.

3. **📝 Appointment Letter Generator**:
   - Generates official appointment contracts with CTC structure, probation clauses, notice periods, and site postings in Word & PDF.

4. **📈 Annual Salary Increment & Appraisal Letter**:
   - Auto-calculates hike percentages, new annual CTC, and revised monthly breakdown with live preview and Word/PDF export.

5. **🤝 Joining & Offer Letter Generator**:
   - Generates candidate job offers with date of reporting, offered CTC, and joining documentation checklists in Word & PDF.

6. **⭐ Performance Review & Confirmation Letter**:
   - Official probation completion and service confirmation letters with performance grades (A+, A, B) and appraisal remarks.

7. **⚠️ Disciplinary Notices & Warning Templates**:
   - Multi-tier formal warnings (First Warning, Second Warning, Final Show-Cause Notice) for unapproved absenteeism, safety PPE non-compliance, and misconduct.

8. **⚙️ Super Administrator Master Control**:
   - Universal Logo Manager (instant site-wide reflection).
   - Persistent settings storage in `data/settings.json` (Contractor name, Principal Employer, Signatory name, Registered address).
   - Operating Sites Manager (add/manage dynamic client locations).

---

## 🚀 How to Run Locally

```bash
# 1. Activate your Python environment
# 2. Run the Streamlit application
streamlit run app.py
```

### 🔐 Default Login Credentials

* **Super Admin**:  
  Username: `Admin` (or `admin`)  
  Password: `Administrator@2027`

* **HR Associate**:  
  Username: `darshan`  
  Password: `AIPL@2027`

---

## 📂 Project Architecture

```
ts-global-hrms/
│
├── app.py                     # Main application entry point & router
├── requirements.txt           # Project dependencies
├── README.md                  # System documentation
│
├── data/
│   └── settings.json          # Persistent enterprise settings
│
├── assets/                    # Company logos (logo1.png, logo2.png)
│
├── automation/
│   ├── config.py              # Persistent settings manager & custom SaaS theme CSS
│   ├── auth.py                # Session authentication & login interface
│   │
│   ├── modules/
│   │   ├── dashboard.py         # Visual KPI launchpad
│   │   ├── compliance_hub.py    # Form 18 & statutory compliance registers
│   │   ├── salary_slip.py       # Single & bulk salary slip generator
│   │   ├── appointment.py       # Appointment letter generator
│   │   ├── increment.py         # Salary increment / appraisal letter generator
│   │   ├── joining_offer.py     # Job offer & joining letter generator
│   │   ├── review_letter.py     # Probation confirmation & review letter generator
│   │   ├── warning_templates.py # Disciplinary & warning notice generator
│   │   └── admin_panel.py       # Admin settings, logo manager & sites manager
│   │
│   └── utils/
│       ├── excel_helpers.py     # Sheet parsing, number cleaning, and blank template generator
│       ├── letter_generators.py # Unified Word & PDF engine for letters & payslips
│       ├── pdf_generators.py    # Form 18 ReportLab PDF generator
│       └── word_generators.py   # Form 18 python-docx Word generator
```

---

## 💡 How to Add New Modules in the Future

Adding a new module is simple:
1. Create a new file in `automation/modules/your_module.py` with a `def render(selected_site):` function.
2. In `app.py`:
   - Import `your_module` from `automation.modules`.
   - Add a navigation button in the sidebar.
   - Add an `elif portal_section == "Your Section": your_module.render(selected_site)`.
3. If your module needs Word or PDF export, use the reusable functions in `automation/utils/letter_generators.py`!
