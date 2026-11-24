import streamlit as st
import os
from automation.config import load_master_registry, load_settings, get_base64_image

def render_entity_site_selector(key_prefix="global", selected_site_default=None):
    """
    Unified reusable selector for Issuing Entity (AIPL, Ashapura, PMT, GBBS) 
    and Operating Project Site linked directly to the Master Registry.
    Automatically assigns correct Director/Signatory:
    - AAIKRUPA INFRATECH PVT. LTD. (AIPL) -> Karman Gadhvi (Director)
    - ASHAPURA / PMT / GBBS -> Tarun Swami (Authorized Signatory / MD)
    """
    reg = load_master_registry()
    entities = reg.get("entities", {})
    sites = reg.get("sites", {})
    clients = reg.get("clients", {})
    pos = reg.get("pos", {})
    
    st.markdown("""
        <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 12px; padding: 14px 18px; margin-bottom: 16px;">
            <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #64748B; font-weight: 700; margin-bottom: 6px;">
                🏢 Issuing Company Entity & Client Project Site
            </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    
    # 1. Entity Selection
    with c1:
        entity_keys = list(entities.keys()) if entities else ["AIPL"]
        # Format function
        def format_entity(k):
            ent = entities.get(k, {})
            sig = ent.get('signatory_name', 'Karman Gadhvi' if k == 'AIPL' else 'Tarun Swami')
            return f"{ent.get('name', k)} ({sig})"
            
        selected_ent_key = st.selectbox(
            "Issuing Company Entity",
            entity_keys,
            format_func=format_entity,
            key=f"{key_prefix}_entity_sel"
        )
        ent_obj = entities.get(selected_ent_key, {})
        
        # Explicit Director Mapping
        if selected_ent_key == "AIPL":
            sig_name = "Karman Gadhvi"
            sig_title = "Director"
        else:
            sig_name = ent_obj.get("signatory_name", "Tarun Swami")
            sig_title = ent_obj.get("signatory_title", "Authorized Signatory / Managing Director")
            
        st.caption(f"✍️ Signatory: **{sig_name}** ({sig_title}) &bull; CIN: <code>{ent_obj.get('cin', 'N/A')}</code>")

    # 2. Site Selection
    with c2:
        site_keys = list(sites.keys()) if sites else ["MPL-PIPE-01"]
        default_idx = 0
        if selected_site_default:
            for i, k in enumerate(site_keys):
                if selected_site_default in k or selected_site_default in sites[k].get("site_name", ""):
                    default_idx = i
                    break
                    
        def format_site(k):
            s = sites.get(k, {})
            c_name = clients.get(s.get("client_id", ""), {}).get("short_name", "")
            return f"{k} — {s.get('site_name', k)[:38]} ({c_name})"
            
        selected_site_code = st.selectbox(
            "Operating Project Site",
            site_keys,
            index=default_idx,
            format_func=format_site,
            key=f"{key_prefix}_site_sel"
        )
        site_obj = sites.get(selected_site_code, {})
        client_obj = clients.get(site_obj.get("client_id", ""), {})
        po_obj = pos.get(site_obj.get("po_no", ""), {})
        
        cap = site_obj.get("labour_cap", 250)
        active = site_obj.get("active_headcount", 210)
        headroom = cap - active
        
        cap_color = "#10B981" if headroom > 10 else ("#F59E0B" if headroom > 0 else "#EF4444")
        st.caption(f"🛡️ Client: **{client_obj.get('name', 'Adani MPL')}** &bull; CLRA Cap: **{active}/{cap}** (<span style='color:{cap_color}; font-weight:700;'>+{headroom} free slots</span>)", unsafe_allow_html=True)
        
    st.markdown("</div>", unsafe_allow_html=True)
    
    return {
        "entity_id": selected_ent_key,
        "company_name": ent_obj.get("name", "AAIKRUPA INFRATECH PVT. LTD."),
        "company_address": ent_obj.get("address", "Shop No. 18, Ashok Vatika, Dhrab Road, Mundra, Kutch, Gujarat - 370421"),
        "cin": ent_obj.get("cin", "U45201GJ2020PTC114920"),
        "gstin": ent_obj.get("gstin", ""),
        "pf_code": ent_obj.get("pf_code", ""),
        "esic_code": ent_obj.get("esic_code", ""),
        "signatory_name": sig_name,
        "signatory_title": sig_title,
        "site_code": selected_site_code,
        "site_name": site_obj.get("site_name", selected_site_code),
        "site_location": site_obj.get("site_location", "Mundra Petrochem Complex, Adani Port SEZ, Mundra, Kutch"),
        "nature_of_work": site_obj.get("nature_of_work", "Mechanical & Structural Execution"),
        "client_id": site_obj.get("client_id", "ADANI_MPL"),
        "client_name": client_obj.get("name", "M/S. MUNDRA PETROCHEM LIMITED"),
        "client_rc": client_obj.get("rc_no", ""),
        "po_no": site_obj.get("po_no", "PO-ADANI-MPL-2026-881"),
        "clra_license_no": site_obj.get("clra_license_no", "1199597230"),
        "headroom": headroom
    }

def render_employee_selector_widget(filter_status=None, filter_site=None, key_prefix="emp"):
    """
    Reusable dropdown widget to select an employee from Employee Master.
    Returns the selected employee object or None.
    """
    from automation.utils.employee_master import load_employees
    emps = load_employees()
    if not emps:
        return None
        
    filtered_emps = {}
    for k, v in emps.items():
        if filter_status and v.get("status") not in (filter_status if isinstance(filter_status, list) else [filter_status]):
            continue
        if filter_site and filter_site.upper() not in v.get("site_code", "").upper() and filter_site.upper() not in v.get("site_location", "").upper():
            continue
        filtered_emps[k] = v
        
    if not filtered_emps:
        filtered_emps = emps # fallback to all if filter produces empty
        
    options = ["-- Select from Employee Master / Candidate List --"] + list(filtered_emps.keys())
    
    def format_emp(k):
        if k == options[0]:
            return k
        e = filtered_emps[k]
        status_badge = "🟢" if e.get("status") == "active" else ("🟡" if e.get("status") == "offered" else ("🔵" if e.get("status") == "confirmed" else "⚪"))
        return f"{status_badge} {e.get('name', '')} ({e.get('designation', '')} &bull; Punch: {e.get('punch_id', k)} &bull; ₹{e.get('gross_salary', 0):,.0f})"
        
    sel_key = st.selectbox(
        "⚡ Fast-Fill from Central Employee Master",
        options,
        format_func=format_emp,
        key=f"{key_prefix}_master_dropdown"
    )
    
    if sel_key != options[0]:
        return filtered_emps[sel_key]
    return None
