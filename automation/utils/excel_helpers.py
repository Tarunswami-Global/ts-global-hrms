import io
import re
from datetime import datetime
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from automation.config import MONTH_ORDER, MONTH_DISPLAY

def parse_sheet_month_year(sheet_name, cal_year=2026):
    """
    Intelligently extracts (year, month_num, month_label, sheet_name)
    from arbitrary sheet names like 'JAN 2026', 'MUNDRA JAN 26', 'Salary_Feb_2026', etc.
    """
    s = str(sheet_name).strip().upper()
    words = re.findall(r'[A-Z]+', s)
    m_num = 99
    for w in words:
        if w in MONTH_ORDER:
            m_num = MONTH_ORDER[w]
            break

    # Search for 4-digit year (e.g. 2025, 2026, 2027)
    y_match_4 = re.findall(r'\b(20\d\d)\b', s)
    if y_match_4:
        yr = int(y_match_4[0])
    else:
        # Search for 2-digit year like _26 or -26
        y_match_2 = re.findall(r'[\'_\s-](\d{2})\b', s)
        if y_match_2:
            yr = 2000 + int(y_match_2[0])
        else:
            yr = cal_year

    month_str = MONTH_DISPLAY.get(m_num, s)
    return (yr, m_num, f"{month_str}-{yr}", sheet_name)

def format_doj(val):
    """Formats various Date of Joining formats to DD-MM-YYYY."""
    if pd.isna(val) or str(val).strip() in ['', '0', '00:00:00', 'NaT', 'None', 'nan', 'NAN', '-']:
        return ""
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.strftime('%d-%m-%Y')

    # Check if value is Excel serial date number (e.g., 44927)
    try:
        val_float = float(val)
        if 30000 < val_float < 65000:
            dt = datetime.fromordinal(datetime(1899, 12, 30).toordinal() + int(val_float))
            return dt.strftime('%d-%m-%Y')
    except (ValueError, TypeError):
        pass

    s = str(val).strip().split(' ')[0]
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d', '%d.%m.%Y', '%d-%b-%Y', '%d-%b-%y'):
        try:
            return datetime.strptime(s, fmt).strftime('%d-%m-%Y')
        except ValueError:
            pass
    return s

def clean_num(val, is_float=False):
    """Safely cleans numbers with commas, currency symbols, and whitespace."""
    if val is None or pd.isna(val):
        return 0.0 if is_float else 0
    val_str = str(val).strip().replace(',', '').replace('₹', '').replace('Rs.', '').replace('Rs', '').replace('/-', '').strip()
    if val_str == '' or val_str.lower() in ['nan', 'none', 'null', '-', 'nil']:
        return 0.0 if is_float else 0
    try:
        num = float(val_str)
        return round(num, 2) if is_float else int(round(num))
    except Exception:
        return 0.0 if is_float else 0

def safe_get(row, idx, default=""):
    """Safely retrieves value from a pandas Series or list by index."""
    if idx < len(row):
        val = row.iloc[idx] if hasattr(row, 'iloc') else row[idx]
        if pd.notna(val) and str(val).strip().lower() not in ['nan', 'none', 'nat']:
            return str(val).strip()
    return default

def scan_and_validate_data(df, sheet_name):
    """Validates dataframe rows for basic data sanity."""
    errors = []
    warnings = []
    if df.empty:
        errors.append(f"Sheet '{sheet_name}' is empty.")
        return errors, warnings
    
    for idx, row in df.iterrows():
        row_num = idx + 2
        name = safe_get(row, 0)
        if not name:
            warnings.append(f"Row {row_num}: Missing Employee Name.")
            continue
        
        days_val = safe_get(row, 6, "0")
        try:
            days = clean_num(days_val)
            if days < 0 or days > 31:
                errors.append(f"Row {row_num} ({name}): Invalid Days Worked ({days}). Must be between 0 and 31.")
        except Exception:
            pass
            
    return errors, warnings

def create_blank_template(form_type):
    """Generates styled blank Excel templates for Form 18, Forms A-D, and Salary Sheets."""
    wb = Workbook()
    ws = wb.active
    ws.title = form_type[:30]
    
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    if form_type == "Form 18":
        headers = [
            "Employee Name", "Father Name", "Department", "Designation", "DOJ", 
            "Principal Employer", "Days Worked", "Layoff", "Maternity", "Leave Enjoyed", 
            "Total (9-12)", "Reg Earned", "Refused", "Regular Balance", "Leave Period", 
            "Normal Rate", "Cash Equiv"
        ]
        sample_row = [
            "RAMESH KUMAR SHARMA", "RAMLAL SHARMA", "Maintenance", "FITTER", "01-04-2023",
            "M/S. MUNDRA PETROCHEM LIMITED", 26, 0, 0, 0,
            26, 1, 0, 1, 0,
            650.00, 0.00
        ]
    elif form_type == "Salary Sheet":
        headers = [
            "Emp ID", "Employee Name", "Father Name", "Designation", "Department", "Site", 
            "DOJ", "Bank Name", "Bank Account", "IFSC", "UAN", "ESIC No", "Days Worked", 
            "Basic Salary", "DA", "HRA", "Site Allowance", "Overtime Amount", 
            "PF Deduction", "ESIC Deduction", "PT", "Advance / Loan", "TDS"
        ]
        sample_row = [
            "EMP001", "RAMESH KUMAR", "RAMLAL", "Fitter", "Mechanical", "Mundra Petrochem",
            "01-01-2024", "State Bank of India", "12345678901", "SBIN0001234", "100987654321", "3712345678", 26,
            15000, 3000, 2000, 1000, 1500,
            1800, 150, 200, 500, 0
        ]
    elif form_type == "Form A":
        headers = ["Employee Name", "Father Name", "Department", "Designation", "Date of Joining", "Principal Employer", "Days Worked", "Gender", "UAN", "Aadhaar", "Mobile", "Bank Name", "Account No", "IFSC", "Address"]
        sample_row = ["RAMESH KUMAR", "RAMLAL", "Plant", "Operator", "01-01-2024", "Mundra Petrochem", 26, "Male", "100987654321", "123456789012", "9876543210", "SBI", "123456789", "SBIN0001234", "Mundra, Kutch"]
    elif form_type == "Form B":
        headers = ["Employee Name", "Father Name", "Department", "Designation", "Date of Joining", "Principal Employer", "Days Worked", "Basic Salary", "DA", "HRA", "Overtime Hours", "Normal Rate", "Cash Equiv"]
        sample_row = ["RAMESH KUMAR", "RAMLAL", "Plant", "Operator", "01-01-2024", "Mundra Petrochem", 26, 12000, 2500, 1500, 10, 500, 0]
    elif form_type == "Form C":
        headers = ["Employee Name", "Recovery Type", "Particulars", "Date of Advance", "Amount", "Show Cause Issued", "Installments", "Recovery Date"]
        sample_row = ["RAMESH KUMAR", "Festival Advance", "Diwali Advance", "15-10-2025", 5000, "No", 2, "30-11-2025"]
    elif form_type == "Form D":
        headers = ["Employee Name", "Designation"] + [f"Day {i}" for i in range(1, 32)] + ["Total Days"]
        sample_row = ["RAMESH KUMAR", "Operator"] + ["P"] * 26 + ["WO"] * 5 + [26]
    else:
        headers = ["Field 1", "Field 2", "Field 3"]
        sample_row = ["Sample 1", "Sample 2", "Sample 3"]

    ws.append(headers)
    ws.append(sample_row)

    # Style header row
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
        # auto-fit width approx
        ws.column_dimensions[cell.column_letter].width = max(len(headers[col_num - 1]) + 4, 14)
        
        sample_cell = ws.cell(row=2, column=col_num)
        sample_cell.border = thin_border
        sample_cell.alignment = Alignment(vertical="center")

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
