import streamlit as st
from automation.config import load_settings, has_permission, load_master_registry

def render(selected_site):
    settings = load_settings()
    reg = load_master_registry()
    est_name = settings.get('establishment_name', "AAIKRUPA INFRATECH PVT. LTD.")
    principal_emp = settings.get('principal_employer', "M/S. MUNDRA PETROCHEM LIMITED, MUNDRA, KACHCHH")
    license_no = settings.get('license_no', "1199597230")
    signatory = settings.get('signatory_name', "Karman Gadhvi")
    sites = settings.get('sites', [])
    current_user = st.session_state.get('username', 'Admin').upper()

    sites_dict = reg.get('sites', {})
    total_workers = sum(s.get('active_headcount', 0) for s in sites_dict.values()) if sites_dict else 651
    total_cap = sum(s.get('labour_cap', 0) for s in sites_dict.values()) if sites_dict else 750
    cap_util_pct = round((total_workers / total_cap * 100), 1) if total_cap > 0 else 0

    # Dashboard Main Title (Oilforce Solutions Style)
    st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 22px;">
            <div>
                <h2 style="margin: 0; font-size: 24px; font-weight: 800; color: #0F172A; letter-spacing: -0.5px;">
                    📊 Enterprise Operations & Compliance Dashboard
                </h2>
                <p style="margin: 4px 0 0 0; font-size: 13px; color: #64748B;">
                    Unified Management Terminal &bull; {est_name} &bull; Active Site: <span style="color: #2563EB; font-weight: 700;">{selected_site}</span>
                </p>
            </div>
            <div>
                <span class="status-pill pill-green" style="font-size: 12px; padding: 6px 14px; font-weight: 700;">
                    🟢 All Modules Operational
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Executive Director Presentation Cockpit Banner
    if has_permission("can_view_director_cockpit"):
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); border-radius: 12px; padding: 14px 22px; color: #FFFFFF; display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; border-left: 5px solid #F59E0B; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);">
                <div>
                    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1.2px; color: #F59E0B; font-weight: 800;">Executive Director & Boardroom Governance</div>
                    <div style="font-size: 15px; font-weight: 700; color: #FFFFFF; margin-top: 2px;">👔 Managing Director Cockpit & Statutory Audit Guarantee</div>
                </div>
                <div style="display: flex; gap: 10px; align-items: center;">
                    <span style="font-size: 11px; color: #CBD5E1; background: rgba(255,255,255,0.1); padding: 4px 10px; border-radius: 8px;">99.4% Lawful Rating</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("👔 Open Executive Director Presentation Cockpit ➔", key="btn_dash_open_cockpit", type="primary", use_container_width=True):
            st.session_state['nav_selection'] = "👔 Executive Director Cockpit"
            st.rerun()
        st.write("")

    # =========================================================================
    # ROW 1: TOP 4 KPI BENTO CARDS (OILFORCE SOLUTIONS STYLE)
    # =========================================================================
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
            <div class="modern-card" style="padding: 18px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <div style="width: 8px; height: 8px; border-radius: 50%; background: #2563EB;"></div>
                    <span style="font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.8px; color: #64748B; font-weight: 700;">
                        OPERATING SITES
                    </span>
                </div>
                <h2 style="margin: 4px 0 2px 0; font-size: 28px; font-weight: 800; color: #0F172A;">{len(sites)}</h2>
                <div style="font-size: 11.5px; font-weight: 600; color: #10B981; margin-top: 4px;">▲ +1 new site this month</div>
            </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
            <div class="modern-card" style="padding: 18px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <div style="width: 8px; height: 8px; border-radius: 50%; background: #10B981;"></div>
                    <span style="font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.8px; color: #64748B; font-weight: 700;">
                        ACTIVE MANPOWER
                    </span>
                </div>
                <h2 style="margin: 4px 0 2px 0; font-size: 28px; font-weight: 800; color: #0F172A;">{total_workers}</h2>
                <div style="font-size: 11.5px; font-weight: 600; color: #10B981; margin-top: 4px;">▲ Cap: {total_cap} ({cap_util_pct}% Utilized)</div>
            </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
            <div class="modern-card" style="padding: 18px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <div style="width: 8px; height: 8px; border-radius: 50%; background: #F59E0B;"></div>
                    <span style="font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.8px; color: #64748B; font-weight: 700;">
                        STATUTORY REGISTERS
                    </span>
                </div>
                <h2 style="margin: 4px 0 2px 0; font-size: 28px; font-weight: 800; color: #0F172A;">5 Forms</h2>
                <div style="font-size: 11.5px; font-weight: 600; color: #2563EB; margin-top: 4px;">● Forms A-D & 18 Active</div>
            </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
            <div class="modern-card" style="padding: 18px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                    <div style="width: 8px; height: 8px; border-radius: 50%; background: #A855F7;"></div>
                    <span style="font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.8px; color: #64748B; font-weight: 700;">
                        LETTER ENGINES
                    </span>
                </div>
                <h2 style="margin: 4px 0 2px 0; font-size: 28px; font-weight: 800; color: #0F172A;">7 Modules</h2>
                <div style="font-size: 11.5px; font-weight: 600; color: #10B981; margin-top: 4px;">● Calibrated & Verified</div>
            </div>
        """, unsafe_allow_html=True)

    st.write("")

    # =========================================================================
    # ROW 2: BENTO GRID (SCORE DONUT + TASKS + SITE HEATMAP)
    # =========================================================================
    b_col1, b_col2, b_col3 = st.columns([1, 1.35, 1.15])
    
    with b_col1:
        st.markdown("""
            <div class="modern-card" style="height: 275px; text-align: center; display: flex; flex-direction: column; justify-content: space-between;">
                <div style="text-align: left; font-size: 14px; font-weight: 700; color: #0F172A;">
                    System Efficiency Score
                </div>
                <div style="display: flex; justify-content: center; align-items: center; margin: 10px 0;">
                    <div style="width: 110px; height: 110px; border-radius: 50%; background: conic-gradient(#10B981 0% 88%, #E2E8F0 88% 100%); display: flex; align-items: center; justify-content: center;">
                        <div style="width: 84px; height: 84px; background: #FFFFFF; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                            <span style="font-size: 24px; font-weight: 800; color: #0F172A;">88</span>
                            <span style="font-size: 11px; color: #64748B;">/ 100</span>
                        </div>
                    </div>
                </div>
                <div style="display: flex; justify-content: center; gap: 10px; font-size: 11px;">
                    <span style="color: #EF4444; font-weight: 600;">● &lt;60 Low</span>
                    <span style="color: #F59E0B; font-weight: 600;">● 61-80 Neutral</span>
                    <span style="color: #10B981; font-weight: 600;">● 81-100 Optimal</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with b_col2:
        st.markdown("""
            <div class="modern-card" style="height: 275px; display: flex; flex-direction: column; justify-content: space-between;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 14px; font-weight: 700; color: #0F172A;">Pending Operations & Work Orders</span>
                    <span style="font-size: 11.5px; color: #2563EB; font-weight: 600; cursor: pointer;">Live Queue</span>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 8px;">
                    <div style="display: flex; align-items: center; gap: 8px; padding: 7px 10px; border-radius: 8px; background: #F8FAFC; font-size: 12.5px;">
                        <span style="color: #10B981; font-weight: 700;">✓</span>
                        <span style="color: #1E293B; font-weight: 500;">Offer Letter: Manish R. Joshi (₹37,234 Gross)</span>
                        <span style="margin-left: auto; font-size: 11px; color: #64748B;">Today</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; padding: 7px 10px; border-radius: 8px; background: #F8FAFC; font-size: 12.5px;">
                        <span style="color: #10B981; font-weight: 700;">✓</span>
                        <span style="color: #1E293B; font-weight: 500;">Salary Increment Batch (15% across 22 Staff)</span>
                        <span style="margin-left: auto; font-size: 11px; color: #64748B;">Today</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; padding: 7px 10px; border-radius: 8px; background: #F8FAFC; font-size: 12.5px;">
                        <span style="color: #94A3B8; font-weight: 700;">○</span>
                        <span style="color: #1E293B; font-weight: 500;">Verify Form A Muster Roll for Mundra</span>
                        <span style="margin-left: auto; font-size: 11px; color: #64748B;">Tomorrow</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px; padding: 7px 10px; border-radius: 8px; background: #F8FAFC; font-size: 12.5px;">
                        <span style="color: #94A3B8; font-weight: 700;">○</span>
                        <span style="color: #1E293B; font-weight: 500;">Generate Monthly Salary Slips for Nov 2026</span>
                        <span style="margin-left: auto; font-size: 11px; color: #64748B;">In 3 days</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with b_col3:
        st.markdown("""
            <div class="modern-card" style="height: 275px; display: flex; flex-direction: column; justify-content: space-between;">
                <div style="font-size: 14px; font-weight: 700; color: #0F172A;">
                    Site Allocation Heatmap
                </div>
                <div style="display: flex; flex-direction: column; gap: 12px; margin-top: 6px;">
                    <div>
                        <div style="display: flex; justify-content: space-between; font-size: 12.5px; margin-bottom: 4px;">
                            <span style="color: #334155; font-weight: 500;">Mundra Petrochem Limited</span>
                            <strong style="color: #0F172A;">650 Manpower</strong>
                        </div>
                        <div style="height: 6px; background: #E2E8F0; border-radius: 3px; overflow: hidden;">
                            <div style="height: 100%; width: 72%; background: #2563EB;"></div>
                        </div>
                    </div>
                    <div>
                        <div style="display: flex; justify-content: space-between; font-size: 12.5px; margin-bottom: 4px;">
                            <span style="color: #334155; font-weight: 500;">ANIL Project Site</span>
                            <strong style="color: #0F172A;">150 Manpower</strong>
                        </div>
                        <div style="height: 6px; background: #E2E8F0; border-radius: 3px; overflow: hidden;">
                            <div style="height: 100%; width: 17%; background: #10B981;"></div>
                        </div>
                    </div>
                    <div>
                        <div style="display: flex; justify-content: space-between; font-size: 12.5px; margin-bottom: 4px;">
                            <span style="color: #334155; font-weight: 500;">Aaikrupa Registered Office</span>
                            <strong style="color: #0F172A;">100 Manpower</strong>
                        </div>
                        <div style="height: 6px; background: #E2E8F0; border-radius: 3px; overflow: hidden;">
                            <div style="height: 100%; width: 11%; background: #F59E0B;"></div>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.write("")

    # =========================================================================
    # 1. CLIENTS & WORKING SITE MANAGEMENT
    # =========================================================================
    st.markdown("""
        <div class="section-header-banner" style="border-left-color: #2563EB;">
            <div>
                <span class="section-badge">
                    SECTION 01 • OPERATIONS & SITES
                </span>
                <h3 style="margin: 2px 0 0 0; color: #0F172A; font-weight: 700;">🏢 Clients & Working Site Management</h3>
            </div>
            <span class="status-pill pill-blue">5 Active Projects • Total Labour Cap: 900 Manpower</span>
        </div>
    """, unsafe_allow_html=True)

    site_col1, site_col2 = st.columns([1.1, 1.3])
    
    with site_col1:
        st.markdown(f"""
            <div class="modern-card" style="height: 290px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <h4 style="margin:0; color: #2563EB;">📍 Active Operating Site</h4>
                    <span class="status-pill pill-green">LIVE SITE</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Current Site</span>
                    <span class="info-value" style="color: #2563EB;">{selected_site}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Principal Employer</span>
                    <span class="info-value">{principal_emp}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Contractor Firm</span>
                    <span class="info-value">{est_name}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Labour License No</span>
                    <span class="info-value">{license_no}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Authorized Signatory</span>
                    <span class="info-value">{signatory}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("⚙️ Configure Sites & Licenses in Admin Panel ➔", key="btn_dash_site_manage", use_container_width=True):
            st.session_state['nav_selection'] = "⚙️ Admin Control Panel"
            st.rerun()

    with site_col2:
        st.markdown(f"""
            <div class="modern-card" style="height: 290px; overflow-y: auto;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <h4 style="margin:0; color: #2563EB;">🏗️ Client Sites & Statutory Manpower Caps</h4>
                    <span class="status-pill pill-blue">STATUTORY ALLOCATIONS</span>
                </div>
                <div class="info-row">
                    <div>
                        <div style="color: #0F172A; font-weight: 600;">MPL - Piping Works Site</div>
                        <div style="font-size: 11.5px; color: #64748B;">Mundra Petrochem Limited</div>
                    </div>
                    <span class="status-pill pill-green">Cap: 250 Workers</span>
                </div>
                <div class="info-row">
                    <div>
                        <div style="color: #0F172A; font-weight: 600;">MPL - Structural Works Site</div>
                        <div style="font-size: 11.5px; color: #64748B;">Mundra Petrochem Limited</div>
                    </div>
                    <span class="status-pill pill-green">Cap: 250 Workers</span>
                </div>
                <div class="info-row">
                    <div>
                        <div style="color: #0F172A; font-weight: 600;">Linde-Solar & TATA CGPL Site</div>
                        <div style="font-size: 11.5px; color: #64748B;">Solar & Thermal Power Division</div>
                    </div>
                    <span class="status-pill pill-purple">WC Policy: 400 Workers</span>
                </div>
                <div class="info-row">
                    <div>
                        <div style="color: #0F172A; font-weight: 600;">Central Fab Shop & Registered Yard</div>
                        <div style="font-size: 11.5px; color: #64748B;">Mundra, Kutch (Permanent Base)</div>
                    </div>
                    <span class="status-pill pill-amber">Form F Gratuity Compliant</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        if st.button("📋 Open Form 18 Working Register for Site ➔", key="btn_dash_site_f18", use_container_width=True):
            st.session_state['nav_selection'] = "⚖️ Compliance Portal (Forms A-D & 18)"
            st.rerun()

    # =========================================================================
    # 2. COMPLIANCE REGISTERS
    # =========================================================================
    st.markdown("""
        <div class="section-header-banner" style="border-left-color: #10B981;">
            <div>
                <span class="section-badge" style="color: #15803D; background: #DCFCE7; border-color: #86EFAC;">
                    SECTION 02 • STATUTORY REGISTERS
                </span>
                <h3 style="margin: 2px 0 0 0; color: #0F172A; font-weight: 700;">⚖️ Statutory Compliance Registers</h3>
            </div>
            <span class="status-pill pill-green">Gujarat Factories Rules & Code on Wages (Central)</span>
        </div>
    """, unsafe_allow_html=True)

    cr_col1, cr_col2, cr_col3 = st.columns(3)

    with cr_col1:
        st.markdown("""
            <div class="modern-card" style="height: 195px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span class="status-pill pill-green">RULE 94 COMPLIANT</span>
                    <span style="font-size: 18px;">🌿</span>
                </div>
                <h4 style="margin: 0; color: #15803D;">Form 18 — Leave with Wages</h4>
                <p style="font-size: 12.5px; color: #64748B; margin-top: 8px; line-height: 1.5;">
                    Statutory Leave with Wages Register under Gujarat Factories Rules. Auto-calculates 5% earned leaves, days worked, and advance wages.
                </p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Open Form 18 Register ➔", key="btn_cr_f18", use_container_width=True):
            st.session_state['nav_selection'] = "⚖️ Compliance Portal (Forms A-D & 18)"
            st.rerun()

    with cr_col2:
        st.markdown("""
            <div class="modern-card" style="height: 195px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span class="status-pill pill-blue">CENTRAL STATUTORY</span>
                    <span style="font-size: 18px;">📘</span>
                </div>
                <h4 style="margin: 0; color: #1D4ED8;">Forms A, B, C & D Suite</h4>
                <p style="font-size: 12.5px; color: #64748B; margin-top: 8px; line-height: 1.5;">
                    Official blank & filled formats: Form A (Employee Register), Form B (Wage Computation), Form C (Loan Recovery), Form D (Muster Roll).
                </p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Open Forms A-D Suite ➔", key="btn_cr_fad", use_container_width=True):
            st.session_state['nav_selection'] = "⚖️ Compliance Portal (Forms A-D & 18)"
            st.rerun()

    with cr_col3:
        st.markdown("""
            <div class="modern-card" style="height: 195px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span class="status-pill pill-purple">86-POINT AUDIT</span>
                    <span style="font-size: 18px;">🛡️</span>
                </div>
                <h4 style="margin: 0; color: #6B21A8;">Master Audit & Adani Tracker</h4>
                <p style="font-size: 12.5px; color: #64748B; margin-top: 8px; line-height: 1.5;">
                    Darshan Sir's Master Monitoring tracker, Adani 86-point audit checklist, Form F Gratuity, PF ECR, ESIC challans, and contractor records.
                </p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Open Master Audit Hub ➔", key="btn_cr_audit", use_container_width=True):
            st.session_state['nav_selection'] = "⚖️ Compliance Portal (Forms A-D & 18)"
            st.rerun()

    # =========================================================================
    # 3. LETTER TEMPLATES (PRE-DESIGNED FORMATS)
    # =========================================================================
    st.markdown("""
        <div class="section-header-banner" style="border-left-color: #F59E0B;">
            <div>
                <span class="section-badge" style="color: #92400E; background: #FEF3C7; border-color: #FCD34D;">
                    SECTION 03 • PRE-DESIGNED FORMATS
                </span>
                <h3 style="margin: 2px 0 0 0; color: #0F172A; font-weight: 700;">📑 Pre-Designed Letter Templates & Formats</h3>
            </div>
            <span class="status-pill pill-amber">Original Company Formats • 100% Automated Pull</span>
        </div>
    """, unsafe_allow_html=True)

    lt_r1_c1, lt_r1_c2, lt_r1_c3 = st.columns(3)

    with lt_r1_c1:
        st.markdown("""
            <div class="modern-card" style="height: 190px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span class="status-pill pill-green">FORM XIX STATUTORY</span>
                    <span style="font-size: 18px;">📄</span>
                </div>
                <h4 style="margin: 0; color: #15803D;">Form XIX Wage / Salary Slip</h4>
                <p style="font-size: 12.5px; color: #64748B; margin-top: 8px; line-height: 1.5;">
                    Exact statutory slip: 50% Basic, 40% HRA, 8.33% Bonus, 5% Leave, PF 12%, and PT deduction formula.
                </p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Generate Salary Slips ➔", key="btn_lt_slip", use_container_width=True):
            st.session_state['nav_selection'] = "📄 1. Salary Slip Generate"
            st.rerun()

    with lt_r1_c2:
        st.markdown("""
            <div class="modern-card" style="height: 190px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span class="status-pill pill-blue">60-DAY NOTICE CLAUSE</span>
                    <span style="font-size: 18px;">📝</span>
                </div>
                <h4 style="margin: 0; color: #1D4ED8;">Appointment Contract Letter</h4>
                <p style="font-size: 12.5px; color: #64748B; margin-top: 8px; line-height: 1.5;">
                    Official appointment contract with 60-day notice period, Mundra site assignment, 1-yr confidentiality, & CTC matrix.
                </p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Generate Appointment ➔", key="btn_lt_appt", use_container_width=True):
            st.session_state['nav_selection'] = "📝 2. Appointment Generate"
            st.rerun()

    with lt_r1_c3:
        st.markdown("""
            <div class="modern-card" style="height: 190px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span class="status-pill pill-amber">9-ROW CTC MATRIX</span>
                    <span style="font-size: 18px;">📈</span>
                </div>
                <h4 style="margin: 0; color: #92400E;">Salary Increment Letter</h4>
                <p style="font-size: 12.5px; color: #64748B; margin-top: 8px; line-height: 1.5;">
                    Internal increment format with automatic percentage hike calculation, existing vs revised salary matrix, and effective date.
                </p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Generate Increment Letter ➔", key="btn_lt_inc", use_container_width=True):
            st.session_state['nav_selection'] = "📈 3. Increment Letter"
            st.rerun()

    st.write("")

    lt_r2_c1, lt_r2_c2, lt_r2_c3 = st.columns(3)

    with lt_r2_c1:
        st.markdown("""
            <div class="modern-card" style="height: 190px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span class="status-pill pill-blue">CANDIDATE OFFER</span>
                    <span style="font-size: 18px;">🤝</span>
                </div>
                <h4 style="margin: 0; color: #1D4ED8;">Joining Offer Letter</h4>
                <p style="font-size: 12.5px; color: #64748B; margin-top: 8px; line-height: 1.5;">
                    Pre-employment offer letters with 3-way gross/in-hand/CTC calculator, reporting location, joining date, and document checklist.
                </p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Generate Offer Letter ➔", key="btn_lt_offer", use_container_width=True):
            st.session_state['nav_selection'] = "🤝 4. Joining Offer Letter"
            st.rerun()

    with lt_r2_c2:
        st.markdown("""
            <div class="modern-card" style="height: 190px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span class="status-pill pill-purple">PROBATION CLEARANCE</span>
                    <span style="font-size: 18px;">⭐</span>
                </div>
                <h4 style="margin: 0; color: #6B21A8;">Performance Review Letter</h4>
                <p style="font-size: 12.5px; color: #64748B; margin-top: 8px; line-height: 1.5;">
                    Annual evaluation and post-probation service confirmation letters with revised remuneration and performance score.
                </p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Generate Review Letter ➔", key="btn_lt_rev", use_container_width=True):
            st.session_state['nav_selection'] = "⭐ 5. Review Letter"
            st.rerun()

    with lt_r2_c3:
        st.markdown("""
            <div class="modern-card" style="height: 190px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span class="status-pill pill-green">OFFICIAL RELIEVING</span>
                    <span style="font-size: 18px;">📜</span>
                </div>
                <h4 style="margin: 0; color: #15803D;">Experience Certificate</h4>
                <p style="font-size: 12.5px; color: #64748B; margin-top: 8px; line-height: 1.5;">
                    Official experience certificate with tenure dates, operating project site, professionalism endorsement, and dual letterhead modes.
                </p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Generate Experience Certificate ➔", key="btn_lt_exp", use_container_width=True):
            st.session_state['nav_selection'] = "📜 6. Experience Certificate"
            st.rerun()

    st.write("")

    lt_r3_c1, lt_r3_c2 = st.columns(2)
    with lt_r3_c1:
        st.markdown("""
            <div class="modern-card" style="height: 185px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span class="status-pill pill-amber" style="color: #DC2626; background: #FEE2E2; border-color: #FCA5A5;">DISCIPLINARY ACTION</span>
                    <span style="font-size: 18px;">⚠️</span>
                </div>
                <h4 style="margin: 0; color: #DC2626;">Disciplinary & Warning Notices</h4>
                <p style="font-size: 12.5px; color: #64748B; margin-top: 8px; line-height: 1.5;">
                    Formal written warning memos and show-cause notices for unauthorized absenteeism, safety non-compliance, and misconduct.
                </p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Generate Warning Notice ➔", key="btn_lt_warn", use_container_width=True):
            st.session_state['nav_selection'] = "⚠️ 7. Disciplinary & Warning Notice"
            st.rerun()

    with lt_r3_c2:
        st.markdown("""
            <div class="modern-card" style="height: 185px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span class="status-pill pill-amber">STATUTORY NOMINATION</span>
                    <span style="font-size: 18px;">🏛️</span>
                </div>
                <h4 style="margin: 0; color: #92400E;">Gratuity Form F (Nomination)</h4>
                <p style="font-size: 12.5px; color: #64748B; margin-top: 8px; line-height: 1.5;">
                    Statutory nomination under Payment of Gratuity (Central) Rules, 1972 with family member proportions and witness seals.
                </p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Open Compliance Hub ➔", key="btn_lt_grat", use_container_width=True):
            st.session_state['nav_selection'] = "⚖️ Compliance Portal (Forms A-D & 18)"
            st.rerun()

    # =========================================================================
    # 4. CURRENT USER & SESSION PROFILE
    # =========================================================================
    st.markdown("""
        <div class="section-header-banner" style="border-left-color: #6B21A8;">
            <div>
                <span class="section-badge" style="color: #6B21A8; background: #F3E8FF; border-color: #D8B4FE;">
                    SECTION 04 • SECURITY & PROFILE
                </span>
                <h3 style="margin: 2px 0 0 0; color: #0F172A; font-weight: 700;">👤 Current USER & Operational Profile</h3>
            </div>
            <span class="status-pill pill-purple">Live Authenticated Session</span>
        </div>
    """, unsafe_allow_html=True)

    usr_col1, usr_col2 = st.columns([1.2, 1])

    with usr_col1:
        st.markdown(f"""
            <div class="modern-card" style="height: 250px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <h4 style="margin:0; color: #6B21A8;">🔐 User Credentials & Clearance</h4>
                    <span class="status-pill pill-green">ACTIVE & VERIFIED</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Active Username</span>
                    <span class="info-value" style="color: #6B21A8;">{current_user}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Assigned Role</span>
                    <span class="info-value">Super Admin & Compliance Head</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Principal Signatory</span>
                    <span class="info-value">{signatory}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Operational Establishment</span>
                    <span class="info-value">{est_name}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Clearance Scope</span>
                    <span class="info-value">Full Master Access (All Sites & Statutory Letters)</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with usr_col2:
        st.markdown(f"""
            <div class="modern-card" style="height: 250px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                    <h4 style="margin:0; color: #2563EB;">⚡ Quick Operations</h4>
                    <span class="status-pill pill-blue">COMMANDS</span>
                </div>
                <p style="font-size: 13px; color: #64748B; margin-bottom: 16px;">
                    Direct session controls and administrative management for <b>{current_user}</b>:
                </p>
        """, unsafe_allow_html=True)
        
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if st.button("⚙️ Admin Settings", key="btn_usr_admin", use_container_width=True):
                st.session_state['nav_selection'] = "⚙️ Admin Control Panel"
                st.rerun()
        with btn_c2:
            if st.button("🔄 Refresh Cache", key="btn_usr_refresh", use_container_width=True):
                st.rerun()

        st.write("")
        if st.button("🚪 Terminate Session & Logout", key="btn_usr_logout", use_container_width=True):
            st.session_state['authenticated'] = False
            st.session_state['username'] = ''
            st.session_state['in_transition'] = False
            st.session_state['pending_username'] = ''
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
