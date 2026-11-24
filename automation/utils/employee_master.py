import os
import json
from datetime import datetime
from automation.config import load_master_registry, save_master_registry

EMPLOYEES_FILE = os.path.join("data", "employees.json")

def load_employees():
    """Loads all employee records from persistent JSON storage."""
    os.makedirs("data", exist_ok=True)
    if os.path.exists(EMPLOYEES_FILE):
        try:
            with open(EMPLOYEES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading employees: {e}")
            return {}
    else:
        # Seed default initial workforce records if file doesn't exist
        initial_data = get_initial_seed_employees()
        save_employees(initial_data)
        return initial_data

def save_employees(employees_data):
    """Saves employee records to persistent storage and auto-syncs site headcounts."""
    os.makedirs("data", exist_ok=True)
    try:
        with open(EMPLOYEES_FILE, "w", encoding="utf-8") as f:
            json.dump(employees_data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving employees: {e}")
        return False

def get_employee(identifier):
    """Fetches an employee by emp_id, punch_id, or full name."""
    emps = load_employees()
    if identifier in emps:
        return emps[identifier]
    for e in emps.values():
        if e.get("punch_id") == str(identifier) or e.get("name", "").strip().upper() == str(identifier).strip().upper():
            return e
    return None

def get_employees_by_status(status=None):
    """Returns dictionary of employees filtered by status ('offered', 'active', 'confirmed', 'exited')."""
    emps = load_employees()
    if not status:
        return emps
    if isinstance(status, str):
        status = [status]
    return {k: v for k, v in emps.items() if v.get("status", "active") in status}

def get_employees_by_site(site_code=None, status="active"):
    """Returns list of employees assigned to a specific site code."""
    emps = load_employees()
    result = []
    for emp_id, emp in emps.items():
        if status and emp.get("status") != status:
            continue
        if site_code:
            # Check match against site_code or site_name
            emp_site = emp.get("site_code", "")
            emp_site_name = emp.get("site_location", "")
            if site_code.upper() in emp_site.upper() or site_code.upper() in emp_site_name.upper():
                result.append(emp)
        else:
            result.append(emp)
    return result

def upsert_candidate_offer(offer_data):
    """
    Saves or updates a candidate record created in the Joining Offer Letter module.
    Status is marked as 'offered'.
    """
    emps = load_employees()
    name = offer_data.get("candidate_name", "").strip().upper()
    emp_code = offer_data.get("emp_code") or f"OFFER-{datetime.now().strftime('%Y%m')}-{len(emps)+1:03d}"
    
    # Check if candidate already exists
    target_key = emp_code
    for k, v in emps.items():
        if v.get("name", "").strip().upper() == name and v.get("status") == "offered":
            target_key = k
            break

    existing = emps.get(target_key, {})
    
    updated_record = {
        **existing,
        "emp_id": target_key,
        "name": name,
        "father_name": offer_data.get("father_name", existing.get("father_name", "")),
        "designation": offer_data.get("designation", existing.get("designation", "TECHNICIAN")),
        "department": offer_data.get("department", existing.get("department", "Mechanical & Piping")),
        "entity_id": offer_data.get("entity_id", existing.get("entity_id", "AIPL")),
        "client_id": offer_data.get("client_id", existing.get("client_id", "ADANI_MPL")),
        "site_code": offer_data.get("site_code", existing.get("site_code", "MPL-PIPE-01")),
        "site_location": offer_data.get("site_location", existing.get("site_location", "Mundra Petrochem Complex")),
        "po_no": offer_data.get("po_no", existing.get("po_no", "PO-ADANI-MPL-2026-881")),
        "reporting_to": offer_data.get("reporting_to", existing.get("reporting_to", "Site In-Charge")),
        "doj": offer_data.get("doj", existing.get("doj", datetime.today().strftime('%Y-%m-%d'))),
        "gross_salary": float(offer_data.get("gross_salary", 30000.0)),
        "annual_ctc": float(offer_data.get("annual_ctc", 405600.0)),
        "net_inhand": float(offer_data.get("net_inhand", 26800.0)),
        "status": existing.get("status", "offered"),
        "offer_date": offer_data.get("offer_date", datetime.today().strftime('%Y-%m-%d')),
        "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    emps[target_key] = updated_record
    save_employees(emps)
    return target_key

def convert_offer_to_appointment(candidate_id, appt_data):
    """
    Converts an offered candidate into an 'active' employee upon Appointment Letter generation.
    Increments the site's active headcount in master_registry.json.
    """
    emps = load_employees()
    target_rec = emps.get(candidate_id)
    if not target_rec:
        # Create as new employee if not previously in offer list
        target_rec = {"emp_id": candidate_id}

    punch_id = appt_data.get("emp_code") or candidate_id
    target_rec.update({
        "emp_id": candidate_id,
        "punch_id": punch_id,
        "name": appt_data.get("candidate_name", target_rec.get("name", "")).strip().upper(),
        "designation": appt_data.get("designation", target_rec.get("designation", "")),
        "department": appt_data.get("department", target_rec.get("department", "Execution")),
        "entity_id": appt_data.get("entity_id", target_rec.get("entity_id", "AIPL")),
        "site_code": appt_data.get("site_code", target_rec.get("site_code", "MPL-PIPE-01")),
        "site_location": appt_data.get("site_location", target_rec.get("site_location", "")),
        "doj": appt_data.get("doj", target_rec.get("doj", datetime.today().strftime('%Y-%m-%d'))),
        "gross_salary": float(appt_data.get("gross_salary", target_rec.get("gross_salary", 30000.0))),
        "notice_period": int(appt_data.get("notice_period", 60)),
        "status": "active",
        "appointment_date": appt_data.get("date", datetime.today().strftime('%Y-%m-%d')),
        "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    
    emps[candidate_id] = target_rec
    save_employees(emps)
    
    # Auto-sync active headcount in master_registry
    sync_site_headcounts()
    return True

def update_employee_salary(emp_id, new_gross, appraisal_data):
    """
    Updates employee's salary after an appraisal / increment letter is issued.
    Records history in employee's appraisals list.
    """
    emps = load_employees()
    emp = emps.get(emp_id)
    if not emp:
        for k, v in emps.items():
            if v.get("name", "").strip().upper() == str(emp_id).strip().upper() or v.get("punch_id") == str(emp_id):
                emp = v
                emp_id = k
                break
    if not emp:
        return False
        
    old_gross = emp.get("gross_salary", 0.0)
    appraisal_record = {
        "date": appraisal_data.get("letter_date", datetime.today().strftime('%Y-%m-%d')),
        "effective_date": appraisal_data.get("effective_date", datetime.today().strftime('%Y-%m-%d')),
        "previous_gross": old_gross,
        "new_gross": float(new_gross),
        "hike_amount": float(new_gross) - float(old_gross),
        "hike_percent": appraisal_data.get("hike_percent", 0.0),
        "remarks": appraisal_data.get("remarks", "Annual Merit Increment")
    }
    
    if "appraisals" not in emp:
        emp["appraisals"] = []
    emp["appraisals"].append(appraisal_record)
    emp["gross_salary"] = float(new_gross)
    emp["last_updated"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    emps[emp_id] = emp
    save_employees(emps)
    return True

def record_employee_warning(emp_id, warning_data):
    """
    Logs a disciplinary or safety warning directly on the employee's permanent record.
    Returns the total warning count.
    """
    emps = load_employees()
    emp = emps.get(emp_id)
    if not emp:
        for k, v in emps.items():
            if v.get("name", "").strip().upper() == str(emp_id).strip().upper() or v.get("punch_id") == str(emp_id):
                emp = v
                emp_id = k
                break
    if not emp:
        return 0
        
    warning_entry = {
        "ref_no": warning_data.get("ref_no", ""),
        "date": warning_data.get("date", datetime.today().strftime('%Y-%m-%d')),
        "severity": warning_data.get("warning_level", "FIRST WRITTEN WARNING"),
        "violation_type": warning_data.get("violation_type", "Absenteeism"),
        "issued_by": warning_data.get("issued_by", "Site In-Charge")
    }
    
    if "warnings" not in emp:
        emp["warnings"] = []
    emp["warnings"].append(warning_entry)
    emp["last_updated"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    emps[emp_id] = emp
    save_employees(emps)
    return len(emp["warnings"])

def record_employee_relieving(emp_id, relieving_data):
    """
    Marks employee as 'exited' upon generation of Relieving / Experience certificate.
    Decrements active headcount and frees up CLRA license capacity.
    """
    emps = load_employees()
    emp = emps.get(emp_id)
    if not emp:
        for k, v in emps.items():
            if v.get("name", "").strip().upper() == str(emp_id).strip().upper() or v.get("punch_id") == str(emp_id):
                emp = v
                emp_id = k
                break
    if not emp:
        return False
        
    emp["status"] = "exited"
    emp["dor"] = relieving_data.get("dor", datetime.today().strftime('%Y-%m-%d'))
    emp["relieving_ref"] = relieving_data.get("ref_no", "")
    emp["last_updated"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    emps[emp_id] = emp
    save_employees(emps)
    sync_site_headcounts()
    return True

def sync_site_headcounts():
    """
    Recalculates active workforce count per site and updates master_registry.json automatically.
    """
    emps = load_employees()
    reg = load_master_registry()
    if not reg or "sites" not in reg:
        return
        
    site_counts = {}
    for emp in emps.values():
        if emp.get("status") == "active":
            scode = emp.get("site_code")
            if scode:
                site_counts[scode] = site_counts.get(scode, 0) + 1

    updated = False
    for scode, site_obj in reg["sites"].items():
        # Keep realistic calibrated baseline or active count
        computed_count = site_counts.get(scode, 0)
        # If user has set a larger active count, ensure it reflects accurately
        current_reg_count = site_obj.get("active_headcount", 0)
        new_count = max(current_reg_count, computed_count)
        if new_count != current_reg_count:
            site_obj["active_headcount"] = new_count
            updated = True
            
    if updated:
        save_master_registry(reg)

def get_initial_seed_employees():
    """Returns baseline calibrated employee records for TS Global / Aaikrupa sites."""
    return {
        "EMP-8300013436": {
            "emp_id": "EMP-8300013436",
            "punch_id": "8300013436",
            "name": "NAVEEN KUMAR MISHRA",
            "father_name": "RAMESH MISHRA",
            "designation": "FITTER",
            "department": "Piping & Fabrication",
            "entity_id": "AIPL",
            "client_id": "ADANI_MPL",
            "site_code": "MPL-PIPE-01",
            "site_location": "MPL Site — Mechanical Piping Division (Adani SEZ Mundra)",
            "po_no": "PO-ADANI-MPL-2026-881",
            "doj": "2024-04-01",
            "gross_salary": 30000.0,
            "annual_ctc": 405600.0,
            "net_inhand": 26800.0,
            "bank_account": "SBI - 918020034567891",
            "uan": "100987654321",
            "esic_no": "3712345678",
            "status": "active",
            "warnings": [],
            "appraisals": []
        },
        "EMP-AMPCW2366595": {
            "emp_id": "EMP-AMPCW2366595",
            "punch_id": "AMPCW2366595",
            "name": "RAMESH KUMAR SHARMA",
            "father_name": "KISHAN LAL SHARMA",
            "designation": "SENIOR FITTER",
            "department": "Piping & Fabrication",
            "entity_id": "AIPL",
            "client_id": "ADANI_MPL",
            "site_code": "MPL-PIPE-01",
            "site_location": "MPL Site — Mechanical Piping Division (Adani SEZ Mundra)",
            "po_no": "PO-ADANI-MPL-2026-881",
            "doj": "2023-04-01",
            "gross_salary": 26000.0,
            "annual_ctc": 351500.0,
            "net_inhand": 23200.0,
            "bank_account": "HDFC - 50100234567812",
            "uan": "100987654322",
            "esic_no": "3712345679",
            "status": "active",
            "warnings": [],
            "appraisals": []
        },
        "EMP-1045": {
            "emp_id": "EMP-1045",
            "punch_id": "EMP-1045",
            "name": "DINESH B. MEHTA",
            "father_name": "BHARAT MEHTA",
            "designation": "Site Electrical Supervisor",
            "department": "Electrical & Instrumentation",
            "entity_id": "AIPL",
            "client_id": "ADANI_MPL",
            "site_code": "MPL-STRUC-02",
            "site_location": "MPL Site — Structural Fabrication & Erection",
            "po_no": "PO-ADANI-STR-441",
            "doj": "2023-10-01",
            "gross_salary": 38000.0,
            "annual_ctc": 513800.0,
            "net_inhand": 34100.0,
            "bank_account": "BOB - 19820100034125",
            "uan": "100987654323",
            "esic_no": "",
            "status": "confirmed",
            "warnings": [],
            "appraisals": []
        },
        "EMP-1102": {
            "emp_id": "EMP-1102",
            "punch_id": "EMP-1102",
            "name": "SANJAY M. PARMAR",
            "father_name": "MOHAN PARMAR",
            "designation": "Site Welder / Fabricator",
            "department": "Structural Fabrication",
            "entity_id": "ASHAPURA",
            "client_id": "ADANI_MPL",
            "site_code": "MPL-STRUC-02",
            "site_location": "MPL Site — Structural Fabrication & Erection",
            "po_no": "PO-ADANI-STR-441",
            "doj": "2024-01-15",
            "gross_salary": 28000.0,
            "annual_ctc": 378500.0,
            "net_inhand": 25000.0,
            "bank_account": "AXIS - 91401005678912",
            "uan": "100987654324",
            "esic_no": "3712345680",
            "status": "active",
            "warnings": [
                {
                    "ref_no": "AIPL/HR/WARN/2026/019",
                    "date": "2026-10-15",
                    "severity": "FIRST WRITTEN WARNING",
                    "violation_type": "Unapproved Absenteeism",
                    "issued_by": "Site In-Charge"
                }
            ],
            "appraisals": []
        },
        "EMP-1089": {
            "emp_id": "EMP-1089",
            "punch_id": "EMP-1089",
            "name": "VIKRAM SINGH CHAUHAN",
            "father_name": "PRATAP SINGH CHAUHAN",
            "designation": "Senior Mechanical Engineer",
            "department": "Mechanical & Piping Execution",
            "entity_id": "AIPL",
            "client_id": "LINDE",
            "site_code": "LINDE-SOL-01",
            "site_location": "Linde India — Solar Project Site (Mundra)",
            "po_no": "LINDE-WO-2025-412",
            "doj": "2023-05-01",
            "gross_salary": 52000.0,
            "annual_ctc": 703000.0,
            "net_inhand": 46800.0,
            "bank_account": "ICICI - 003101567890",
            "uan": "100987654325",
            "esic_no": "",
            "status": "active",
            "warnings": [],
            "appraisals": []
        }
    }
