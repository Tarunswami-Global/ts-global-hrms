import streamlit as st
import os
import json
import base64
import hashlib

SETTINGS_FILE = os.path.join("data", "settings.json")
MASTER_REGISTRY_FILE = os.path.join("data", "master_registry.json")
MONTHLY_COMPLIANCE_FILE = os.path.join("data", "monthly_compliance.json")
USERS_FILE = os.path.join("data", "users.json")

ROLE_DEFINITIONS = {
    "super_admin": {
        "title": "Super Administrator & MD",
        "badge_color": "#DC2626",
        "allowed_nav": [
            "🏠 Dashboard Overview",
            "🛡️ Master License & Site Hub",
            "📊 Monthly Site Compliance",
            "⚖️ Statutory Registers (Forms A-D)",
            "📄 1. Salary Slip Generator",
            "📝 2. Appointment Letter",
            "📈 3. Salary Increment Letter",
            "🤝 4. Joining Offer Letter",
            "⭐ 5. Performance Review Letter",
            "📜 6. Experience Certificate",
            "⚠️ 7. Disciplinary Notice",
            "⚙️ Admin Control Panel"
        ]
    },
    "compliance_head": {
        "title": "Site Compliance Head & In-Charge",
        "badge_color": "#2563EB",
        "allowed_nav": [
            "🏠 Dashboard Overview",
            "🛡️ Master License & Site Hub",
            "📊 Monthly Site Compliance",
            "⚖️ Statutory Registers (Forms A-D)",
            "📄 1. Salary Slip Generator",
            "📝 2. Appointment Letter",
            "📜 6. Experience Certificate"
        ]
    },
    "hr_manager": {
        "title": "HR Operations Executive",
        "badge_color": "#059669",
        "allowed_nav": [
            "🏠 Dashboard Overview",
            "📄 1. Salary Slip Generator",
            "📝 2. Appointment Letter",
            "📈 3. Salary Increment Letter",
            "🤝 4. Joining Offer Letter",
            "⭐ 5. Performance Review Letter",
            "📜 6. Experience Certificate",
            "⚠️ 7. Disciplinary Notice"
        ]
    },
    "site_supervisor": {
        "title": "Site Supervisor & Timekeeper",
        "badge_color": "#D97706",
        "allowed_nav": [
            "🏠 Dashboard Overview",
            "📊 Monthly Site Compliance",
            "⚖️ Statutory Registers (Forms A-D)"
        ]
    },
    "auditor_readonly": {
        "title": "Client Compliance Auditor (Read-Only)",
        "badge_color": "#6B7280",
        "allowed_nav": [
            "🏠 Dashboard Overview",
            "📊 Monthly Site Compliance",
            "⚖️ Statutory Registers (Forms A-D)"
        ]
    }
}

def hash_password(password: str) -> str:
    """Computes salted SHA-256 hash of a password."""
    return hashlib.sha256(f"ts_salt_{password}".encode("utf-8")).hexdigest()

def load_users():
    """Loads all system users from persistent storage."""
    os.makedirs("data", exist_ok=True)
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading users: {e}")
    return {}

def save_users(users_data):
    """Saves system users to persistent storage."""
    os.makedirs("data", exist_ok=True)
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving users: {e}")
        return False


DEFAULT_SETTINGS = {
    "establishment_name": "AAIKRUPA INFRATECH PVT. LTD.",
    "principal_employer": "M/S. MUNDRA PETROCHEM LIMITED, MUNDRA, KACHCHH",
    "license_no": "1199597230",
    "signatory_name": "Tarun Swami",
    "signatory_title": "Authorized Signatory / Managing Director",
    "company_address": "Shop No. 18, Ashok Vatika, Dhrab, Mundra, Kutch, Gujarat - 370421",
    "company_phone": "+91 98250 12345",
    "company_email": "hr@aaikrupainfra.com",
    "sites": [
        "M/S. MUNDRA PETROCHEM LIMITED (Mundra)",
        "ANIL Project Site",
        "Aaikrupa Registered Office (Mundra)",
        "Other Client Site"
    ]
}

def load_master_registry():
    """Loads master registry data containing entities, clients, POs, and sites."""
    os.makedirs("data", exist_ok=True)
    if os.path.exists(MASTER_REGISTRY_FILE):
        try:
            with open(MASTER_REGISTRY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading master registry: {e}")
            return {}
    return {}

def save_master_registry(data):
    """Saves master registry data."""
    os.makedirs("data", exist_ok=True)
    try:
        with open(MASTER_REGISTRY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving master registry: {e}")
        return False

def load_monthly_compliance():
    """Loads monthly compliance tracking records."""
    os.makedirs("data", exist_ok=True)
    if os.path.exists(MONTHLY_COMPLIANCE_FILE):
        try:
            with open(MONTHLY_COMPLIANCE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_monthly_compliance(data):
    """Saves monthly compliance tracking records."""
    os.makedirs("data", exist_ok=True)
    try:
        with open(MONTHLY_COMPLIANCE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving monthly compliance: {e}")
        return False

def load_settings():
    """Loads configuration from persistent JSON file or returns defaults."""
    os.makedirs("data", exist_ok=True)
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                merged = {**DEFAULT_SETTINGS, **saved}
                return merged
        except Exception:
            return DEFAULT_SETTINGS.copy()
    else:
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

def save_settings(new_settings):
    """Saves configuration to persistent JSON file."""
    os.makedirs("data", exist_ok=True)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(new_settings, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

def get_base64_image(image_path):
    """Returns base64 encoded string of an image file."""
    if os.path.exists(image_path):
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""

def load_page_config():
    st.set_page_config(
        page_title="TS Global Trading & HRMS Terminal",
        page_icon="⚡",
        layout="wide"
    )

    logo_path = os.path.join("assets", "ts_global_logo.webp")
    logo_b64 = get_base64_image(logo_path)

    bg_watermark_css = ""
    if logo_b64:
        bg_watermark_css = f"""
        .fixed-bg-watermark {{
            position: fixed;
            top: 52%;
            left: 55%;
            transform: translate(-50%, -50%);
            width: 580px;
            height: 520px;
            background-image: url('data:image/webp;base64,{logo_b64}');
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
            opacity: 0.048;
            pointer-events: none;
            z-index: 0;
        }}
        """

    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@500;700&display=swap');

        html, body, [class*="css"], .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], section.main {{
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            background-color: #F8FAFC !important;
            color: #0F172A !important;
        }}

        [data-testid="stHeader"] {{
            background-color: transparent !important;
        }}

        /* Oilforce Solutions Sidebar Style */
        [data-testid="stSidebar"] {{
            background-color: #1E293B !important;
            border-right: 1px solid #334155 !important;
        }}

        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
        [data-testid="stSidebar"] h4, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {{
            color: #F8FAFC !important;
        }}

        [data-testid="stSidebar"] .stSelectbox label {{
            color: #94A3B8 !important;
            font-weight: 600 !important;
        }}

        /* Sidebar Navigation Buttons */
        [data-testid="stSidebar"] .stButton > button {{
            transition: all 0.18s ease !important;
            text-align: left !important;
            justify-content: flex-start !important;
            font-size: 13.5px !important;
            padding: 10px 14px !important;
        }}

        /* ACTIVE NAV ITEM: Oilforce Vibrant Amber / Gold Pill */
        [data-testid="stSidebar"] .stButton > button[kind="primary"],
        [data-testid="stSidebar"] button[data-testid="baseButton-primary"] {{
            background: #F59E0B !important;
            color: #0F172A !important;
            font-weight: 700 !important;
            border-radius: 12px !important;
            border: none !important;
            box-shadow: 0 4px 14px rgba(245, 158, 11, 0.35) !important;
        }}
        [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover,
        [data-testid="stSidebar"] button[data-testid="baseButton-primary"]:hover {{
            background: #FBBF24 !important;
            color: #0F172A !important;
            transform: translateY(-1px) !important;
        }}

        /* INACTIVE NAV ITEMS */
        [data-testid="stSidebar"] .stButton > button[kind="secondary"],
        [data-testid="stSidebar"] button[data-testid="baseButton-secondary"] {{
            background: transparent !important;
            color: #94A3B8 !important;
            font-weight: 500 !important;
            border-radius: 10px !important;
            border: 1px solid transparent !important;
        }}
        [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover,
        [data-testid="stSidebar"] button[data-testid="baseButton-secondary"]:hover {{
            background: rgba(255, 255, 255, 0.08) !important;
            color: #FFFFFF !important;
        }}

        h1, h2, h3, h4, h5, h6 {{
            color: #0F172A !important;
            font-weight: 700;
        }}
        p, label {{
            color: #334155;
        }}

        /* Streamlit elements overrides */
        .stSelectbox label, .stTextInput label, .stNumberInput label, .stDateInput label {{
            color: #1E293B !important;
            font-weight: 600 !important;
            font-size: 13px !important;
        }}

        .stTextInput input, .stSelectbox [data-baseweb="select"], .stNumberInput input, .stDateInput input {{
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            border: 1.5px solid #CBD5E1 !important;
            border-radius: 10px !important;
            font-size: 13.5px !important;
        }}
        .stTextInput input:focus, .stSelectbox [data-baseweb="select"]:focus {{
            border-color: #2563EB !important;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
        }}

        {bg_watermark_css}

        /* Modern Enterprise Top Header */
        .main-header {{
            background: #FFFFFF;
            padding: 16px 24px;
            border-radius: 14px;
            color: #0F172A;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
            border: 1px solid #E2E8F0;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        /* Modern Bento Surface Card */
        .modern-card {{
            background: #FFFFFF;
            border-radius: 14px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
            padding: 22px;
            transition: all 0.2s ease;
            position: relative;
            color: #0F172A;
        }}
        .modern-card:hover {{
            transform: translateY(-2px);
            border-color: #CBD5E1;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.07);
        }}

        /* Section Classification Badge */
        .section-badge {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            padding: 5px 14px;
            border-radius: 30px;
            background: #EFF6FF;
            color: #2563EB;
            border: 1px solid #BFDBFE;
            margin-bottom: 12px;
        }}

        /* Status Pills (Crisp Enterprise Theme) */
        .status-pill {{
            font-size: 11.5px;
            font-weight: 600;
            padding: 4px 12px;
            border-radius: 20px;
            display: inline-block;
        }}
        .pill-green {{
            background: #DCFCE7;
            color: #15803D;
            border: 1px solid #86EFAC;
        }}
        .pill-blue {{
            background: #DBEAFE;
            color: #1D4ED8;
            border: 1px solid #93C5FD;
        }}
        .pill-purple {{
            background: #F3E8FF;
            color: #6B21A8;
            border: 1px solid #D8B4FE;
        }}
        .pill-amber {{
            background: #FEF3C7;
            color: #92400E;
            border: 1px solid #FCD34D;
        }}

        /* Unified Section Header Banner */
        .section-header-banner {{
            background: #FFFFFF;
            border-left: 4px solid #2563EB;
            border-radius: 0 12px 12px 0;
            padding: 14px 20px;
            margin-top: 24px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-top: 1px solid #E2E8F0;
            border-bottom: 1px solid #E2E8F0;
            border-right: 1px solid #E2E8F0;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        }}

        /* Subtle Inner List / Info Row */
        .info-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 9px 0;
            border-bottom: 1px solid #F1F5F9;
            font-size: 13px;
        }}
        .info-row:last-child {{
            border-bottom: none;
        }}
        .info-label {{
            color: #64748B;
            font-weight: 500;
        }}
        .info-value {{
            color: #0F172A;
            font-weight: 600;
        }}

        /* Unified Streamlit Primary Buttons */
        .stButton>button[kind="primary"], button[data-testid="baseButton-primary"] {{
            background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
            color: #FFFFFF !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            font-size: 13.5px !important;
            border: none !important;
            padding: 10px 18px !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25) !important;
        }}
        .stButton>button[kind="primary"]:hover, button[data-testid="baseButton-primary"]:hover {{
            background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 16px rgba(37, 99, 235, 0.35) !important;
        }}

        /* Unified Streamlit Secondary Buttons */
        .stButton>button[kind="secondary"], button[data-testid="baseButton-secondary"] {{
            background: #FFFFFF !important;
            color: #1E293B !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 10px !important;
            font-weight: 600 !important;
            font-size: 13.5px !important;
            padding: 10px 18px !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04) !important;
        }}
        .stButton>button[kind="secondary"]:hover, button[data-testid="baseButton-secondary"]:hover {{
            background: #F8FAFC !important;
            border-color: #94A3B8 !important;
            color: #0F172A !important;
        }}

        /* Amber Action Button Utility */
        .btn-amber-action {{
            background: #F59E0B !important;
            color: #0F172A !important;
            font-weight: 700 !important;
            border-radius: 10px !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(245, 158, 11, 0.28) !important;
        }}

        /* Document Preview Box */
        .letter-preview-box {{
            background-color: #FFFFFF;
            color: #1E293B;
            padding: 28px;
            border-radius: 12px;
            font-family: 'Aptos Narrow', 'Calibri', serif;
            line-height: 1.6;
            border: 1px solid #CBD5E1;
            box-shadow: 0 4px 20px rgba(15, 23, 42, 0.06);
            margin-top: 15px;
            margin-bottom: 15px;
        }}

        /* Video Transition Modal */
        .transition-box {{
            background: #FFFFFF;
            border: 2px solid #2563EB;
            box-shadow: 0 10px 30px rgba(37, 99, 235, 0.15);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            margin-top: 15px;
        }}
        </style>
    """, unsafe_allow_html=True)

MONTH_ORDER = {
    'JAN': 1, 'FEB': 2, 'FAB': 2, 'MAR': 3, 'MARCH': 3, 
    'APR': 4, 'APRIL': 4, 'MAY': 5, 'JUN': 6, 'JUNE': 6, 
    'JUL': 7, 'JULY': 7, 'AUG': 8, 'SEP': 9, 'SEPT': 9, 
    'OCT': 10, 'NOV': 11, 'DEC': 12
}

MONTH_DISPLAY = {
    1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 
    7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
}
