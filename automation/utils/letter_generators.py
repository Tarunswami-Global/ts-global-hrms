import io
import os
import math
import uuid
import zipfile
from datetime import datetime
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, portrait
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

TEMPLATES_DIR = "templates"
ASSETS_DIR = "assets"

def num_to_words_inr(n):
    """Converts integer or float to Indian Rupees in words."""
    units = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten',
             'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
    
    def two_digits(num):
        if num < 20: return units[num]
        return tens[num // 10] + (' ' + units[num % 10] if num % 10 else '')
        
    def three_digits(num):
        h = num // 100
        rem = num % 100
        res = ''
        if h: res += units[h] + ' Hundred'
        if rem: res += (' and ' if res else '') + two_digits(rem)
        return res

    try:
        n = int(round(float(n)))
    except Exception:
        return 'Rupees Zero Only'
        
    if n <= 0: return 'Rupees Zero Only'
    
    parts = []
    crore = n // 10000000
    n %= 10000000
    lakh = n // 100000
    n %= 100000
    thousand = n // 1000
    n %= 1000
    rem = n
    
    if crore: parts.append(two_digits(crore) + ' Crore')
    if lakh: parts.append(two_digits(lakh) + ' Lakh')
    if thousand: parts.append(two_digits(thousand) + ' Thousand')
    if rem: parts.append(three_digits(rem))
        
    return 'Rupees ' + ' '.join(parts) + ' Only'

def docx_to_pdf_word_com(docx_bytes):
    """Converts a docx BytesIO to PDF BytesIO using Microsoft Word COM, with PowerShell bridge and ReportLab fallback."""
    import tempfile
    import subprocess
    temp_dir = os.path.join("scratch", "temp_pdf")
    os.makedirs(temp_dir, exist_ok=True)
    unique_id = uuid.uuid4().hex[:8]
    temp_docx = os.path.abspath(os.path.join(temp_dir, f"temp_{unique_id}.docx"))
    temp_pdf = os.path.abspath(os.path.join(temp_dir, f"temp_{unique_id}.pdf"))
    
    with open(temp_docx, "wb") as f:
        f.write(docx_bytes.getvalue() if hasattr(docx_bytes, 'getvalue') else docx_bytes)
        
    try:
        import pythoncom
        pythoncom.CoInitialize()
        import win32com.client
        word = win32com.client.Dispatch('Word.Application')
        word.Visible = False
        doc = word.Documents.Open(temp_docx)
        doc.SaveAs(temp_pdf, FileFormat=17) # 17 = wdFormatPDF
        doc.Close()
        word.Quit()
        pythoncom.CoUninitialize()
        
        with open(temp_pdf, "rb") as f:
            pdf_bytes = io.BytesIO(f.read())
            
        try:
            if os.path.exists(temp_docx): os.remove(temp_docx)
            if os.path.exists(temp_pdf): os.remove(temp_pdf)
        except Exception:
            pass
            
        return pdf_bytes
    except Exception as e:
        # Fallback 1: Direct PowerShell Word COM bridge
        try:
            ps_cmd = f"$w = New-Object -ComObject Word.Application; $w.Visible = $false; $d = $w.Documents.Open('{temp_docx}'); $d.SaveAs('{temp_pdf}', 17); $d.Close(); $w.Quit()"
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, timeout=15)
            if os.path.exists(temp_pdf):
                with open(temp_pdf, "rb") as f:
                    pdf_bytes = io.BytesIO(f.read())
                try:
                    if os.path.exists(temp_docx): os.remove(temp_docx)
                    if os.path.exists(temp_pdf): os.remove(temp_pdf)
                except Exception:
                    pass
                return pdf_bytes
        except Exception as ps_e:
            print(f"PowerShell Word COM fallback failed: {ps_e}")
            
        try:
            if os.path.exists(temp_docx): os.remove(temp_docx)
            if os.path.exists(temp_pdf): os.remove(temp_pdf)
        except Exception:
            pass
        return None

# ==============================================================
# 1. SALARY SLIP (FORM XIX WAGE SLIP - EXACT TEMPLATE ENGINE)
# ==============================================================

def generate_salary_slip_docx(data, with_letterhead=True):
    """Populates the official Form XIX Salary Slip template with Aptos Narrow, ESIC Employee & Employer,
    and exact 1-page A4 geometry (with or without letterhead)."""
    template_path = os.path.join(TEMPLATES_DIR, "7. Format- Salary Slip.docx")
    if not os.path.exists(template_path):
        return _generate_fallback_salary_docx(data)

    doc = Document(template_path)
    sec = doc.sections[0]
    
    # Exact A4 dimensions
    sec.page_width = Inches(8.27)
    sec.page_height = Inches(11.69)
    
    if with_letterhead:
        sec.top_margin = Inches(1.30)
        sec.bottom_margin = Inches(0.25)
        sec.left_margin = Inches(0.40)
        sec.right_margin = Inches(0.40)
        
        # Inject Letterhead Background
        lh_img = os.path.abspath(os.path.join(ASSETS_DIR, "letterhead_header_image.png"))
        if os.path.exists(lh_img):
            header = sec.header
            for p in header.paragraphs: p.text = ''
            hp = header.paragraphs[0]
            hrun = hp.add_run()
            hrun.add_picture(lh_img, width=Inches(8.27), height=Inches(11.69))
            
            drawing = hrun._r.find('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing')
            if drawing is not None:
                inline = drawing.find('{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}inline')
                if inline is not None:
                    anchor_xml = f'''
                    <wp:anchor xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
                               distT="0" distB="0" distL="0" distR="0" simplePos="0" relativeHeight="251658240"
                               behindDoc="1" locked="1" layoutInCell="1" allowOverlap="1">
                        <wp:simplePos x="0" y="0"/>
                        <wp:positionH relativeFrom="page"><wp:posOffset>0</wp:posOffset></wp:positionH>
                        <wp:positionV relativeFrom="page"><wp:posOffset>0</wp:posOffset></wp:positionV>
                        <wp:extent cx="7562088" cy="10689336"/>
                        <wp:effectExtent l="0" t="0" r="0" b="0"/>
                        <wp:wrapNone/>
                        <wp:docPr id="1" name="Letterhead Background"/>
                        <wp:cNvGraphicFramePr/>
                        {inline.find("{http://schemas.openxmlformats.org/drawingml/2006/main}graphic").xml}
                    </wp:anchor>
                    '''
                    drawing.remove(inline)
                    drawing.append(parse_xml(anchor_xml))
    else:
        # Without Letterhead: 1.8 inch margin for feeding office pre-printed stationery
        sec.top_margin = Inches(1.80)
        sec.bottom_margin = Inches(0.25)
        sec.left_margin = Inches(0.40)
        sec.right_margin = Inches(0.40)
        for p in sec.header.paragraphs: p.text = ''

    if not doc.tables:
        return _generate_fallback_salary_docx(data)

    table = doc.tables[0]

    # 1. REMOVE THE LOGO (rId5) FROM TABLE COMPLETELY
    for d in table._tbl.xpath('.//w:drawing'):
        if 'rId5' in d.xml:
            d.getparent().remove(d)

    # 2. Make Row 1 text clean and centered
    cell_r1 = table.rows[1].cells[0]
    for p in cell_r1.paragraphs:
        p.text = 'WAGE SLIP [SEE RULE 78 (2) (b)] FORM NO.XIX'
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if p.runs:
            p.runs[0].font.name = 'Aptos Narrow'
            p.runs[0].font.size = Pt(9.5)
            p.runs[0].font.bold = False

    # 3. Delete redundant spacer rows
    for r_i in [31, 29, 27, 26, 22, 11]:
        table._tbl.remove(table.rows[r_i]._tr)

    # 4. Delete duplicate company name & address rows (rows 3, 2)
    table._tbl.remove(table.rows[3]._tr)
    table._tbl.remove(table.rows[2]._tr)

    def populate(cell, text, bold=False, font_size=9, align=WD_ALIGN_PARAGRAPH.LEFT):
        if not cell.paragraphs: 
            cell.add_paragraph()
        p = cell.paragraphs[0]
        p.text = str(text)
        p.alignment = align
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        if p.runs:
            p.runs[0].font.name = 'Aptos Narrow'
            p.runs[0].font.bold = bold
            p.runs[0].font.size = Pt(font_size)

    pay_month = str(data.get('pay_month', 'OCTOBER 2026')).upper()
    emp_name = str(data.get('emp_name', ''))
    emp_id = str(data.get('emp_id', ''))
    designation = str(data.get('designation', ''))
    department = str(data.get('department', ''))
    uan = str(data.get('uan', 'N/A'))
    esic = str(data.get('esic', 'N/A'))
    bank_acc = str(data.get('bank_acc', ''))
    days_in_month = str(data.get('days_in_month', '26'))
    days_worked = str(data.get('days_worked', '26'))

    basic = float(data.get('basic', 0))
    hra = float(data.get('hra', 0))
    bonus = float(data.get('bonus', 0))
    leave = float(data.get('leave', 0))
    other_all = float(data.get('allowance', 0))
    incentive = float(data.get('ot', 0))

    pf = float(data.get('pf', 0))
    pt = float(data.get('pt', 0))
    advance = float(data.get('advance', 0))
    other_ded = float(data.get('tds', 0))
    esic_emp = float(data.get('esic_emp', 0))
    esic_employer = float(data.get('esic_employer', 0))
    pf_employer = float(data.get('pf_employer', round(basic * 0.13, 2)))

    gross = basic + hra + bonus + leave + other_all + incentive
    tot_ded = pf + pt + advance + other_ded + esic_emp
    net_pay = gross - tot_ded

    # Row 2: Month
    populate(table.rows[2].cells[0], f"SALARY SLIP FOR THE MONTH OF {pay_month}", bold=True, font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)

    # Employee details
    populate(table.rows[4].cells[1], emp_name, bold=True)
    populate(table.rows[4].cells[3], uan)
    populate(table.rows[5].cells[1], emp_id, bold=True)
    populate(table.rows[5].cells[3], esic)
    populate(table.rows[6].cells[1], designation)
    populate(table.rows[6].cells[3], bank_acc)
    populate(table.rows[7].cells[1], department)
    populate(table.rows[7].cells[3], pay_month)
    populate(table.rows[8].cells[1], f"{days_in_month} Days")
    populate(table.rows[8].cells[3], f"{days_worked} Days")

    # Earnings & Deductions
    populate(table.rows[12].cells[1], f"₹ {basic:,.2f}", align=WD_ALIGN_PARAGRAPH.RIGHT)
    populate(table.rows[12].cells[3], f"₹ {pf:,.2f}", align=WD_ALIGN_PARAGRAPH.RIGHT)

    populate(table.rows[13].cells[1], f"₹ {hra:,.2f}", align=WD_ALIGN_PARAGRAPH.RIGHT)
    populate(table.rows[13].cells[3], f"₹ {pt:,.2f}", align=WD_ALIGN_PARAGRAPH.RIGHT)

    populate(table.rows[14].cells[1], f"₹ {bonus:,.2f}" if bonus > 0 else "-", align=WD_ALIGN_PARAGRAPH.RIGHT)
    populate(table.rows[14].cells[3], f"₹ {advance:,.2f}" if advance > 0 else "-", align=WD_ALIGN_PARAGRAPH.RIGHT)

    populate(table.rows[15].cells[1], f"₹ {leave:,.2f}" if leave > 0 else "-", align=WD_ALIGN_PARAGRAPH.RIGHT)
    populate(table.rows[15].cells[3], f"₹ {other_ded:,.2f}" if other_ded > 0 else "-", align=WD_ALIGN_PARAGRAPH.RIGHT)

    populate(table.rows[16].cells[1], f"₹ {other_all:,.2f}" if other_all > 0 else "-", align=WD_ALIGN_PARAGRAPH.RIGHT)
    populate(table.rows[16].cells[2], "ESIC (Employee - 0.75%)")
    populate(table.rows[16].cells[3], f"₹ {esic_emp:,.2f}" if esic_emp > 0 else "-", align=WD_ALIGN_PARAGRAPH.RIGHT)

    populate(table.rows[17].cells[1], f"₹ {incentive:,.2f}" if incentive > 0 else "-", align=WD_ALIGN_PARAGRAPH.RIGHT)
    populate(table.rows[17].cells[2], "ESIC (Employer - 3.25%)*")
    populate(table.rows[17].cells[3], f"₹ {esic_employer:,.2f}" if esic_employer > 0 else "-", align=WD_ALIGN_PARAGRAPH.RIGHT)

    # Gross & Total Deductions
    populate(table.rows[18].cells[1], f"₹ {gross:,.2f}", bold=True, align=WD_ALIGN_PARAGRAPH.RIGHT)
    populate(table.rows[18].cells[3], f"₹ {tot_ded:,.2f}", bold=True, align=WD_ALIGN_PARAGRAPH.RIGHT)

    # Net Salary Summary
    populate(table.rows[20].cells[1], f"₹ {gross:,.2f}", bold=True, align=WD_ALIGN_PARAGRAPH.RIGHT)
    populate(table.rows[20].cells[3], f"₹ {tot_ded:,.2f}", bold=True, align=WD_ALIGN_PARAGRAPH.RIGHT)

    # Net Payable
    populate(table.rows[21].cells[1], f"₹ {net_pay:,.2f}", bold=True, font_size=11, align=WD_ALIGN_PARAGRAPH.RIGHT)
    populate(table.rows[21].cells[2], num_to_words_inr(net_pay), bold=True, font_size=9.5)

    # Note
    tot_employer = pf_employer + esic_employer
    populate(table.rows[22].cells[0], f"Note: This is a computer-generated salary slip and does not require a signature. *Employer statutory contribution (PF ₹{pf_employer:,.2f} + ESIC ₹{esic_employer:,.2f} = ₹{tot_employer:,.2f}) is paid directly by the company.", font_size=8)

    # Set line spacing tight
    for r in table.rows:
        for c in r.cells:
            for p in c.paragraphs:
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.0

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def _generate_fallback_salary_docx(data):
    doc = Document()
    p = doc.add_paragraph(f"{data.get('establishment_name', 'AAIKRUPA INFRATECH PVT. LTD.')}\nSALARY SLIP")
    p.runs[0].font.bold = True
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def generate_salary_slip_pdf(data, with_letterhead=True):
    """Generates official 1-page A4 PDF salary slip using native Word vector export,
    with automatic fallback to ReportLab if needed."""
    docx_buf = generate_salary_slip_docx(data, with_letterhead=with_letterhead)
    pdf_buf = docx_to_pdf_word_com(docx_buf)
    if pdf_buf:
        return pdf_buf
    return _generate_reportlab_salary_pdf(data)

def _generate_reportlab_salary_pdf(data):
    """Generates fallback A4 PDF salary slip using ReportLab."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=portrait(A4), leftMargin=12*mm, rightMargin=12*mm, topMargin=10*mm, bottomMargin=10*mm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('CompTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13, leading=15, alignment=1, textColor=colors.HexColor('#1E3A8A'))
    sub_style = ParagraphStyle('SubTitle', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10, alignment=1, textColor=colors.HexColor('#64748B'))
    hdr_style = ParagraphStyle('MonthHdr', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.5, leading=12, alignment=1, textColor=colors.black)
    cell_style = ParagraphStyle('CellNorm', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=9.5)
    cell_bold = ParagraphStyle('CellBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=9.5)

    elements = []
    est_name = data.get('establishment_name', 'AAIKRUPA INFRATECH PVT. LTD.').upper()
    elements.append(Paragraph(est_name, title_style))
    elements.append(Paragraph(data.get('company_address', 'Shop No. 18, Ashok Vatika, Dhrab, Mundra, Kutch, Gujarat'), sub_style))
    elements.append(Paragraph(f"<b>WAGE SLIP [SEE RULE 78 (2) (b)] FORM NO. XIX — {data.get('pay_month', 'MAY 2026').upper()}</b>", hdr_style))
    elements.append(Spacer(1, 2.5*mm))

    # Meta Table
    meta_data = [
        [Paragraph(f"<b>Employee Name:</b> {data.get('emp_name', '')}", cell_style),
         Paragraph(f"<b>Employee Code:</b> {data.get('emp_id', '')}", cell_style),
         Paragraph(f"<b>UAN No.:</b> {data.get('uan', 'N/A')}", cell_style)],
        [Paragraph(f"<b>Designation:</b> {data.get('designation', '')}", cell_style),
         Paragraph(f"<b>Department / Site:</b> {data.get('department', '')} ({data.get('site', '')})", cell_style),
         Paragraph(f"<b>ESIC No.:</b> {data.get('esic', 'N/A')}", cell_style)],
        [Paragraph(f"<b>Bank A/c:</b> {data.get('bank_acc', '')}", cell_style),
         Paragraph(f"<b>Working Days:</b> {data.get('days_in_month', 31)}", cell_style),
         Paragraph(f"<b>Paid Days:</b> {data.get('days_worked', 26)}", cell_style)]
    ]
    meta_table = Table(meta_data, colWidths=[65*mm, 65*mm, 55*mm])
    meta_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 3*mm))

    basic = float(data.get('basic', 0))
    hra = float(data.get('hra', 0))
    bonus = float(data.get('bonus', 0))
    leave = float(data.get('leave', 0))
    allowance = float(data.get('allowance', 0))
    ot = float(data.get('ot', 0))
    
    pf = float(data.get('pf', 0))
    pt = float(data.get('pt', 0))
    advance = float(data.get('advance', 0))
    tds = float(data.get('tds', 0))
    
    gross = basic + hra + bonus + leave + allowance + ot
    total_ded = pf + pt + advance + tds
    net_pay = gross - total_ded

    tbl_rows = [
        [Paragraph("<b>EARNINGS</b>", cell_bold), Paragraph("<b>AMOUNT (₹)</b>", cell_bold),
         Paragraph("<b>DEDUCTIONS</b>", cell_bold), Paragraph("<b>AMOUNT (₹)</b>", cell_bold)],
        [Paragraph("Basic Salary", cell_style), Paragraph(f"{basic:,.2f}", cell_style),
         Paragraph("Provident Fund (PF)", cell_style), Paragraph(f"{pf:,.2f}", cell_style)],
        [Paragraph("House Rent Allowance (HRA)", cell_style), Paragraph(f"{hra:,.2f}", cell_style),
         Paragraph("Professional Tax (PT)", cell_style), Paragraph(f"{pt:,.2f}", cell_style)],
        [Paragraph("Statutory Bonus (8.33%)", cell_style), Paragraph(f"{bonus:,.2f}" if bonus > 0 else "-", cell_style),
         Paragraph("Advance Recovery", cell_style), Paragraph(f"{advance:,.2f}" if advance > 0 else "-", cell_style)],
        [Paragraph("Leave Encashment (5%)", cell_style), Paragraph(f"{leave:,.2f}" if leave > 0 else "-", cell_style),
         Paragraph("Other Deductions / TDS", cell_style), Paragraph(f"{tds:,.2f}" if tds > 0 else "-", cell_style)],
        [Paragraph("Site / Other Allowance", cell_style), Paragraph(f"{allowance:,.2f}" if allowance > 0 else "-", cell_style),
         Paragraph("", cell_style), Paragraph("", cell_style)],
        [Paragraph("Incentive / Overtime", cell_style), Paragraph(f"{ot:,.2f}" if ot > 0 else "-", cell_style),
         Paragraph("", cell_style), Paragraph("", cell_style)],
        [Paragraph("<b>TOTAL GROSS EARNINGS</b>", cell_bold), Paragraph(f"<b>₹ {gross:,.2f}</b>", cell_bold),
         Paragraph("<b>TOTAL DEDUCTIONS</b>", cell_bold), Paragraph(f"<b>₹ {total_ded:,.2f}</b>", cell_bold)]
    ]

    main_tbl = Table(tbl_rows, colWidths=[55*mm, 35*mm, 60*mm, 35*mm])
    main_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F1F5F9')),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    elements.append(main_tbl)
    elements.append(Spacer(1, 3.5*mm))

    net_text = f"<b>NET PAYABLE SALARY: ₹ {net_pay:,.2f}</b> &nbsp;&nbsp;<i>({num_to_words_inr(net_pay)})</i>"
    net_para = Paragraph(net_text, ParagraphStyle('NetBox', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=colors.HexColor('#065F46')))
    net_banner = Table([[net_para]], colWidths=[185*mm])
    net_banner.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#D1FAE5')),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#10B981')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(net_banner)
    elements.append(Spacer(1, 8*mm))

    sig_data = [
        [Paragraph("<b>Employee Signature</b><br/><i>(Verified & Received)</i>", cell_style),
         Paragraph(f"<para align='right'><b>For, {est_name}</b><br/><br/><br/><b>Authorized Signatory</b></para>", cell_style)]
    ]
    sig_tbl = Table(sig_data, colWidths=[92*mm, 93*mm])
    sig_tbl.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
    elements.append(sig_tbl)

    doc.build(elements)
    buf.seek(0)
    return buf

# ==============================================================
# 2. APPOINTMENT LETTER (EXACT TEMPLATE INJECTION ENGINE)
# ==============================================================

def generate_appointment_docx(data, with_letterhead=True):
    """
    Populates official '6. Fomat-Mail merge Appointment Letter Draft.docx'
    with exact 1-page A4 geometry, multi-company support (Aaikrupa/Ashapura/Custom),
    dynamic site deployment, and 60-day notice clause.
    """
    template_path = os.path.join(TEMPLATES_DIR, "6. Fomat-Mail merge Appointment Letter Draft.docx")
    if not os.path.exists(template_path):
        return _generate_fallback_appointment_docx(data)

    doc = Document(template_path)
    sec = doc.sections[0]
    sec.page_width = Inches(8.27)
    sec.page_height = Inches(11.69)
    sec.left_margin = Inches(0.50)
    sec.right_margin = Inches(0.50)
    sec.bottom_margin = Inches(0.20)

    # Multi-Company Details
    comp_name = str(data.get('company_name', data.get('establishment_name', 'AAIKRUPA INFRATECH PVT. LTD.'))).strip()
    is_aaikrupa = "AAIKRUPA" in comp_name.upper()

    if with_letterhead:
        sec.top_margin = Inches(0.40)
        # If not Aaikrupa, remove Aaikrupa pre-embedded banner
        if not is_aaikrupa:
            for p in sec.header.paragraphs:
                p.text = ''
                for d in p._p.xpath('.//w:drawing'):
                    d.getparent().remove(d)
    else:
        # Pre-printed stationery mode: clear header artwork and leave 1.80" top margin
        sec.top_margin = Inches(1.80)
        for p in sec.header.paragraphs:
            p.text = ''
            for d in p._p.xpath('.//w:drawing'):
                d.getparent().remove(d)
        for i in range(min(4, len(doc.paragraphs))):
            doc.paragraphs[i].text = ''
            doc.paragraphs[i].paragraph_format.space_before = Pt(0)
            doc.paragraphs[i].paragraph_format.space_after = Pt(0)
            doc.paragraphs[i].paragraph_format.line_spacing = Pt(0)

    c_name = str(data.get('candidate_name', 'Mr. Candidate')).upper()
    c_code = str(data.get('emp_code', data.get('emp_id', '8300013436')))
    desig = str(data.get('designation', 'FITTER')).upper()
    doj = str(data.get('doj', datetime.today().strftime('%d/%m/%Y')))
    try:
        sal = float(data.get('monthly_salary', 30000))
    except (ValueError, TypeError):
        sal = 30000.0
    site_name = str(data.get('site', 'Mundra Petrochem Limited')).strip()
    notice_days = str(data.get('notice_days', '60'))
    letter_date = str(data.get('date', datetime.today().strftime('%d/%m/%Y')))

    for p in doc.paragraphs:
        if 'Date: 29/04/2026' in p.text or ('Date:' in p.text and len(p.text) < 25):
            p.text = f'Date: {letter_date}'
        elif 'NAVEEN KUMAR MISHRA' in p.text and 'Mr.' in p.text:
            p.text = f'To,\nMr. {c_name}\nEmployee Code: {c_code}'
        elif 'We are pleased to appoint you as' in p.text:
            p.text = f'We are pleased to appoint you as {desig} with {comp_name} with effect from {doj}.'
        elif 'Your employment is project-based' in p.text:
            p.text = f'Your employment is project-based and shall remain valid until completion of assigned project/site at {site_name} or otherwise terminated by the Company as per its requirements and policies.'
        elif 'Compensation Your Gross Monthly Salary' in p.text:
            p.text = f'Compensation Your Gross Monthly Salary shall be ₹ {sal:,.0f} per month.'
        elif 'Either party may terminate this employment' in p.text:
            p.text = f"Either party may terminate this employment by giving {notice_days} days' prior written notice. The Company reserves the right to terminate employment immediately in cases of serious misconduct or violation of Company policies."
        elif 'We welcome you to' in p.text:
            p.text = f'We welcome you to {comp_name} and wish you a successful association with the Company.'
        elif 'For Aai Krupa Infratech Pvt. Ltd.' in p.text or ('For ' in p.text and 'Infratech' in p.text):
            p.text = f'For {comp_name}'
        elif 'hereby confirm that I have read, understood, and accepted' in p.text:
            p.text = f"I, {c_name}, hereby confirm that I have read, understood, and accepted the terms and conditions mentioned in this Appointment Letter and agree to abide by the Company's rules, policies, safety requirements, and code of conduct."
        elif 'Employee Name:' in p.text and 'Designation:' in p.text:
            p.text = f'Employee Name: {c_name}\t\t\t\tDesignation: {desig}'

    # Strip trailing blank paragraphs to guarantee 1-page fit
    while len(doc.paragraphs) > 0 and not doc.paragraphs[-1].text.strip():
        p = doc.paragraphs[-1]
        p._p.getparent().remove(p._p)

    for p in doc.paragraphs:
        if p.text.strip():
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(1.5)
            p.paragraph_format.line_spacing = 1.02
            for r in p.runs:
                r.font.name = 'Aptos Narrow'
                if r.font.size is None or r.font.size.pt > 9.5:
                    r.font.size = Pt(9.0)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def _generate_fallback_appointment_docx(data):
    doc = Document()
    doc.add_paragraph(f"APPOINTMENT LETTER\nFor {data.get('company_name', data.get('establishment_name'))}")
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def generate_appointment_pdf(data, with_letterhead=True):
    """Generates official Appointment Letter A4 PDF using Microsoft Word COM engine."""
    docx_buf = generate_appointment_docx(data, with_letterhead=with_letterhead)
    pdf_buf = docx_to_pdf_word_com(docx_buf)
    if pdf_buf:
        return pdf_buf
    return _generate_reportlab_appointment_pdf(data)

def _generate_reportlab_appointment_pdf(data):
    """Fallback ReportLab generator for Appointment Letter."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=portrait(A4), leftMargin=12*mm, rightMargin=12*mm, topMargin=12*mm, bottomMargin=12*mm)
    styles = getSampleStyleSheet()
    p_style = ParagraphStyle('LetterText', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12)
    p_bold = ParagraphStyle('LetterBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=12)
    title_style = ParagraphStyle('DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, leading=14, alignment=1, textColor=colors.HexColor('#1E3A8A'))

    elements = []
    comp_name = data.get('company_name', data.get('establishment_name', 'AAIKRUPA INFRATECH PVT. LTD.'))
    comp_addr = data.get('company_address', 'Mundra-Kachchh Highway, Mundra, Gujarat - 370421')
    elements.append(Paragraph(comp_name.upper(), title_style))
    elements.append(Paragraph(comp_addr, ParagraphStyle('Sub', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10, alignment=1, textColor=colors.HexColor('#64748B'))))
    elements.append(Spacer(1, 3*mm))

    meta_tbl = Table([
        [Paragraph(f"<b>Date:</b> {data.get('date', datetime.today().strftime('%d/%m/%Y'))}", p_style),
         Paragraph(f"<para align='right'><b>Site:</b> {data.get('site', 'Mundra Petrochem Ltd.')}</para>", p_style)]
    ], colWidths=[90*mm, 90*mm])
    elements.append(meta_tbl)
    elements.append(Spacer(1, 2*mm))

    elements.append(Paragraph("<u><b>APPOINTMENT LETTER</b></u>", ParagraphStyle('Hdr', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10.5, leading=13, alignment=1)))
    elements.append(Spacer(1, 2.5*mm))

    c_name = str(data.get('candidate_name', 'Candidate')).upper()
    c_code = str(data.get('emp_code', data.get('emp_id', '8300013436')))
    desig = str(data.get('designation', 'FITTER')).upper()
    try:
        sal = float(data.get('monthly_salary', 30000))
    except (ValueError, TypeError):
        sal = 30000.0
    doj = str(data.get('doj', datetime.today().strftime('%d/%m/%Y')))
    site_name = str(data.get('site', 'Mundra Petrochem Limited')).strip()
    notice_days = str(data.get('notice_days', '60'))

    elements.append(Paragraph(f"<b>To,</b><br/><b>Mr. {c_name}</b><br/>Employee Code: {c_code}", p_style))
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph(f"<b>Subject: Appointment Letter for '{desig}'</b>", p_bold))
    elements.append(Spacer(1, 1.5*mm))

    body = (
        f"Dear Sir,<br/><br/>"
        f"We are pleased to appoint you as <b>{desig}</b> with <b>{comp_name}</b> with effect from <b>{doj}</b>.<br/><br/>"
        f"<b>1. Deployment & Tenure:</b> Your employment is project-based and shall remain valid until completion of assigned project/site at {site_name} or otherwise terminated by the Company.<br/>"
        f"<b>2. Compensation:</b> Your Gross Monthly Salary shall be <b>₹ {sal:,.0f} /- per month</b>, subject to applicable statutory deductions (PF, Professional Tax, etc.).<br/>"
        f"<b>3. Rules & Safety Standards:</b> You shall perform your duties diligently and strictly comply with all Company Rules, Client Safety Standards, and Site Regulations.<br/>"
        f"<b>4. Confidentiality:</b> Salary, wages, benefits, and business information are strictly confidential and shall not be disclosed to any unauthorized person.<br/>"
        f"<b>5. Notice Period:</b> Either party may terminate this employment by giving <b>{notice_days} days' prior written notice</b>. The Company reserves the right to terminate immediately in cases of serious misconduct.<br/>"
        f"<b>6. Approved Attendance:</b> Attendance shall be recorded strictly through approved company punching systems."
    )
    elements.append(Paragraph(body, p_style))
    elements.append(Spacer(1, 4*mm))

    sig_html = f"<b>For, {comp_name}</b><br/><br/><br/><b>{data.get('signatory_name', 'Tarun Swami')}</b><br/>Authorized Signatory"
    acc_html = f"<b>EMPLOYEE ACCEPTANCE:</b><br/>I, {c_name}, accept the terms and conditions.<br/><br/>Signature: _______________ &nbsp;&nbsp; Date: ________"
    elements.append(Table([[Paragraph(sig_html, p_style), Paragraph(acc_html, p_style)]], colWidths=[90*mm, 90*mm]))

    doc.build(elements)
    buf.seek(0)
    return buf

def generate_appointment_bulk_zip(candidates_list, company_data, with_letterhead=True, doc_type='pdf'):
    """Generates a ZIP archive containing appointment letters for all candidates in the list."""
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for idx, cand in enumerate(candidates_list):
            merged_data = dict(company_data)
            merged_data.update(cand)
            emp_code = str(merged_data.get('emp_code', merged_data.get('emp_id', f'EMP-{idx+1}'))).replace('/', '_')
            emp_name = str(merged_data.get('candidate_name', 'Candidate')).replace(' ', '_')
            
            if doc_type == 'docx':
                doc_buf = generate_appointment_docx(merged_data, with_letterhead=with_letterhead)
                zf.writestr(f"Appointment_{emp_code}_{emp_name}.docx", doc_buf.getvalue())
            else:
                pdf_buf = generate_appointment_pdf(merged_data, with_letterhead=with_letterhead)
                zf.writestr(f"Appointment_{emp_code}_{emp_name}.pdf", pdf_buf.getvalue())
    zip_buf.seek(0)
    return zip_buf

def generate_consolidated_appointment_pdf(candidates_list, company_data, with_letterhead=True):
    """Merges all candidates' 1-page appointment letters into a single batch-printable PDF using pypdfium2."""
    import pypdfium2 as pdfium
    master_pdf = pdfium.PdfDocument.new()
    for cand in candidates_list:
        merged_data = dict(company_data)
        merged_data.update(cand)
        pdf_buf = generate_appointment_pdf(merged_data, with_letterhead=with_letterhead)
        src_pdf = pdfium.PdfDocument(pdf_buf)
        master_pdf.import_pages(src_pdf)
        src_pdf.close()
    
    out_buf = io.BytesIO()
    master_pdf.save(out_buf)
    master_pdf.close()
    out_buf.seek(0)
    return out_buf

# ==============================================================
# 3. INCREMENT LETTER (EXACT TEMPLATE INJECTION ENGINE)
# ==============================================================

def generate_increment_docx(data, with_letterhead=True):
    """
    Populates official '5. Salary Increament Letter- Internal.docx'
    with exact 1-page A4 geometry, 9-row table, multi-company support (Aaikrupa/Ashapura/Custom),
    dynamic site deployment, and dual letterhead modes (digital artwork vs pre-printed stationery).
    """
    template_path = os.path.join(TEMPLATES_DIR, "5. Salary Increament Letter- Internal.docx")
    if not os.path.exists(template_path):
        return _generate_fallback_increment_docx(data)

    doc = Document(template_path)
    sec = doc.sections[0]
    sec.page_width = Inches(8.27)
    sec.page_height = Inches(11.69)
    sec.left_margin = Inches(0.50)
    sec.right_margin = Inches(0.50)
    sec.bottom_margin = Inches(0.30)

    # Multi-Company Details
    comp_name = str(data.get('company_name', data.get('establishment_name', 'AAIKRUPA INFRATECH PVT. LTD.'))).strip()
    is_aaikrupa = "AAIKRUPA" in comp_name.upper()

    if with_letterhead:
        sec.top_margin = Inches(0.40)
        # If not Aaikrupa, clear Aaikrupa pre-embedded header artwork
        if not is_aaikrupa:
            for p in sec.header.paragraphs:
                p.text = ''
                for d in p._p.xpath('.//w:drawing'):
                    d.getparent().remove(d)
    else:
        # Pre-printed stationery mode: clear header artwork and leave 1.80" top margin
        sec.top_margin = Inches(1.80)
        for p in sec.header.paragraphs:
            p.text = ''
            for d in p._p.xpath('.//w:drawing'):
                d.getparent().remove(d)
        for i in range(min(4, len(doc.paragraphs))):
            doc.paragraphs[i].text = ''
            doc.paragraphs[i].paragraph_format.space_before = Pt(0)
            doc.paragraphs[i].paragraph_format.space_after = Pt(0)
            doc.paragraphs[i].paragraph_format.line_spacing = Pt(0)

    # Variables extraction
    letter_date = str(data.get('date', datetime.today().strftime('%d-%m-%Y')))
    emp_name = str(data.get('emp_name', data.get('candidate_name', 'AVDHESH KUMAR SHUKLA'))).upper().strip()
    emp_code = str(data.get('emp_code', data.get('emp_id', 'EMP-1088'))).strip()
    designation = str(data.get('designation', 'Senior Plant Operator')).strip()
    dept = str(data.get('department', 'Operations / Mechanical')).strip()
    site = str(data.get('site', 'Mundra Petrochem Limited')).strip()
    doj = str(data.get('doj', '15-03-2024')).strip()
    length_of_service = str(data.get('length_of_service', data.get('length_service', '2 Years 8 Months'))).strip()
    
    try:
        curr_sal = float(data.get('curr_salary', data.get('curr_sal', 22000)))
    except (ValueError, TypeError):
        curr_sal = 22000.0
    try:
        rev_sal = float(data.get('rev_salary', data.get('rev_sal', 25500)))
    except (ValueError, TypeError):
        rev_sal = 25500.0
        
    inc_amt = rev_sal - curr_sal
    inc_pct = round((inc_amt / curr_sal) * 100, 2) if curr_sal > 0 else 0.0
    eff_from = str(data.get('effective_date', data.get('effective_from', '01-11-2026'))).strip()

    for p in doc.paragraphs:
        txt = p.text
        if 'Date:' in txt and ('____' in txt or len(txt) < 25):
            p.text = f'Date: {letter_date}'
            if p.runs:
                p.runs[0].font.name = 'Copperplate Gothic Light'
                p.runs[0].font.size = Pt(10)
        elif txt.strip() == '_______________________________':
            p.text = f'Mr. {emp_name}'
            if p.runs:
                p.runs[0].font.name = 'Aptos Narrow'
                p.runs[0].font.size = Pt(10)
                p.runs[0].bold = True
        elif 'Employee Code:' in txt and '____' in txt:
            p.text = f'Employee Code: {emp_code}'
            if p.runs:
                p.runs[0].font.name = 'Aptos Narrow'
                p.runs[0].font.size = Pt(10)
        elif 'Designation:' in txt and '____' in txt:
            p.text = f'Designation: {designation}'
            if p.runs:
                p.runs[0].font.name = 'Aptos Narrow'
                p.runs[0].font.size = Pt(10)
        elif 'Department:' in txt and 'Project/Site:' in txt:
            p.text = f'Department: {dept}\nProject/Site: {site}'
            if p.runs:
                p.runs[0].font.name = 'Aptos Narrow'
                p.runs[0].font.size = Pt(10)
        elif 'Dear AVDHESH KUMAR SHUKLA' in txt or ('Dear ' in txt and len(txt) < 40):
            p.text = f'Dear {emp_name},'
            if p.runs:
                p.runs[0].font.name = 'Aptos Narrow'
                p.runs[0].font.size = Pt(10)
                p.runs[0].bold = True
        elif 'We are pleased to inform you that' in txt:
            p.text = f'We are pleased to inform you that, after reviewing your performance, commitment, discipline, and valuable contribution towards the growth of {comp_name}, the Management has approved a revision in your salary.'
            if p.runs:
                p.runs[0].font.name = 'Aptos Narrow'
                p.runs[0].font.size = Pt(10)
        elif 'We congratulate you on your well-deserved' in txt:
            p.text = f'We congratulate you on your well-deserved salary increment and wish you continued success with {comp_name}.'
            if p.runs:
                p.runs[0].font.name = 'Aptos Narrow'
                p.runs[0].font.size = Pt(10)
        elif 'For Aaikrupa Infratech' in txt or ('For ' in txt and 'Infratech' in txt):
            p.text = f'For {comp_name}'
            if p.runs:
                p.runs[0].font.name = 'Aptos Narrow'
                p.runs[0].font.size = Pt(10)
                p.runs[0].bold = True
        elif txt.strip() == 'Aaikrupa Infratech Pvt. Ltd.':
            p.text = comp_name
            if p.runs:
                p.runs[0].font.name = 'Aptos Narrow'
                p.runs[0].font.size = Pt(10)
                p.runs[0].bold = True

    # Fill Table 0
    if doc.tables:
        t = doc.tables[0]
        t.rows[1].cells[1].text = emp_code
        t.rows[2].cells[1].text = designation
        t.rows[3].cells[1].text = doj
        t.rows[4].cells[1].text = length_of_service
        t.rows[5].cells[1].text = f'₹ {curr_sal:,.2f} /- per month'
        t.rows[6].cells[1].text = f'₹ {rev_sal:,.2f} /- per month'
        t.rows[7].cells[1].text = f'₹ {inc_amt:,.2f} /- per month (+{inc_pct}%)'
        t.rows[8].cells[1].text = eff_from

        # Format table cells
        for r in t.rows:
            for c in r.cells:
                for p in c.paragraphs:
                    p.paragraph_format.space_before = Pt(1)
                    p.paragraph_format.space_after = Pt(1)
                    for run in p.runs:
                        run.font.name = 'Aptos Narrow'
                        run.font.size = Pt(9.5)

    # Clean trailing empty paragraphs
    while len(doc.paragraphs) > 0 and not doc.paragraphs[-1].text.strip():
        p = doc.paragraphs[-1]._p
        p.getparent().remove(p)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def _generate_fallback_increment_docx(data):
    doc = Document()
    doc.add_paragraph("SALARY INCREMENT LETTER")
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def generate_increment_pdf(data, with_letterhead=True):
    """Generates official Salary Increment Letter A4 PDF using Microsoft Word COM engine."""
    docx_buf = generate_increment_docx(data, with_letterhead=with_letterhead)
    pdf_buf = docx_to_pdf_word_com(docx_buf)
    if pdf_buf:
        return pdf_buf
    return _generate_reportlab_increment_pdf(data)

def _generate_reportlab_increment_pdf(data):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=portrait(A4), leftMargin=15*mm, rightMargin=15*mm, topMargin=12*mm, bottomMargin=12*mm)
    styles = getSampleStyleSheet()
    p_style = ParagraphStyle('LetterText', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=13.5)
    p_bold = ParagraphStyle('LetterBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=14)
    title_style = ParagraphStyle('DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13, leading=15, alignment=1, textColor=colors.HexColor('#1E3A8A'))

    elements = []
    comp_name = data.get('company_name', data.get('establishment_name', 'AAIKRUPA INFRATECH PVT. LTD.'))
    elements.append(Paragraph(comp_name.upper(), title_style))
    elements.append(Paragraph("Shop No. 18, Ashok Vatika, Dhrab, Mundra, Kutch, Gujarat - 370421", ParagraphStyle('Sub', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10, alignment=1, textColor=colors.HexColor('#64748B'))))
    elements.append(Spacer(1, 3*mm))

    meta_tbl = Table([
        [Paragraph(f"<b>Date:</b> {data.get('date', datetime.today().strftime('%d-%m-%Y'))}", p_style),
         Paragraph(f"<para align='right'><b>Site:</b> {data.get('site', 'MPL')}</para>", p_style)]
    ], colWidths=[90*mm, 90*mm])
    elements.append(meta_tbl)
    elements.append(Spacer(1, 2*mm))

    elements.append(Paragraph("<u><b>ANNUAL SALARY INCREMENT LETTER</b></u>", ParagraphStyle('Hdr', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, leading=14, alignment=1)))
    elements.append(Spacer(1, 3*mm))

    emp_name = str(data.get('emp_name', data.get('candidate_name', 'Employee'))).upper()
    emp_code = str(data.get('emp_code', data.get('emp_id', 'EMP001')))
    desig = str(data.get('designation', 'Staff'))
    try:
        curr_sal = float(data.get('curr_salary', data.get('curr_sal', 22000)))
    except (ValueError, TypeError):
        curr_sal = 22000.0
    try:
        rev_sal = float(data.get('rev_salary', data.get('rev_sal', 25500)))
    except (ValueError, TypeError):
        rev_sal = 25500.0
    inc_amt = rev_sal - curr_sal
    inc_pct = round((inc_amt / curr_sal) * 100, 1) if curr_sal > 0 else 0

    elements.append(Paragraph(f"<b>To,</b><br/><b>{emp_name}</b> (Emp Code: {emp_code})<br/>Designation: {desig}<br/>Site: {data.get('site', 'Site')}", p_style))
    elements.append(Spacer(1, 2.5*mm))
    elements.append(Paragraph("<b>Subject: Revision of Salary / Annual Increment</b>", p_bold))
    elements.append(Spacer(1, 2*mm))

    body = (
        f"Dear {emp_name},<br/><br/>"
        f"After reviewing your performance, commitment, discipline, and valuable contribution towards the growth of <b>{comp_name}</b>, the Management has approved a revision in your salary effective from <b>{data.get('effective_date', data.get('effective_from', '01-11-2026'))}</b>.<br/><br/>"
        f"The revised salary particulars are outlined below:"
    )
    elements.append(Paragraph(body, p_style))
    elements.append(Spacer(1, 3*mm))

    tbl_data = [
        [Paragraph("<b>Particulars</b>", p_bold), Paragraph("<b>Details</b>", p_bold)],
        [Paragraph("Employee Code", p_style), Paragraph(emp_code, p_style)],
        [Paragraph("Designation", p_style), Paragraph(desig, p_style)],
        [Paragraph("Current Monthly Gross Salary", p_style), Paragraph(f"₹ {curr_sal:,.2f}", p_style)],
        [Paragraph("<b>Revised Monthly Gross Salary</b>", p_bold), Paragraph(f"<b>₹ {rev_sal:,.2f}</b>", p_bold)],
        [Paragraph("Increment Amount", p_style), Paragraph(f"₹ {inc_amt:,.2f} ({inc_pct} %)", p_style)],
        [Paragraph("Revised Annual CTC", p_style), Paragraph(f"₹ {rev_sal * 12:,.2f}", p_style)],
        [Paragraph("Effective From", p_style), Paragraph(str(data.get('effective_date', data.get('effective_from', '01-11-2026'))), p_style)],
    ]
    tbl = Table(tbl_data, colWidths=[90*mm, 90*mm])
    tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(tbl)
    elements.append(Spacer(1, 4*mm))

    elements.append(Paragraph(f"All other terms and conditions of your employment contract remain unchanged. We congratulate you and wish you continued success with {comp_name}.", p_style))
    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph(f"<b>For, {comp_name}</b><br/><br/><br/><b>{data.get('signatory_name', 'Tarun Swami')}</b><br/>Authorized Signatory", p_style))

    doc.build(elements)
    buf.seek(0)
    return buf

def generate_increment_bulk_zip(records_list, company_data, with_letterhead=True, doc_type='pdf'):
    """Generates a ZIP archive containing increment letters for all employees in the list."""
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for idx, rec in enumerate(records_list):
            merged_data = dict(company_data)
            merged_data.update(rec)
            emp_code = str(merged_data.get('emp_code', merged_data.get('emp_id', f'EMP-{idx+1}'))).replace('/', '_')
            emp_name = str(merged_data.get('emp_name', merged_data.get('candidate_name', 'Employee'))).replace(' ', '_')
            
            if doc_type == 'docx':
                doc_buf = generate_increment_docx(merged_data, with_letterhead=with_letterhead)
                zf.writestr(f"Increment_{emp_code}_{emp_name}.docx", doc_buf.getvalue())
            else:
                pdf_buf = generate_increment_pdf(merged_data, with_letterhead=with_letterhead)
                zf.writestr(f"Increment_{emp_code}_{emp_name}.pdf", pdf_buf.getvalue())
    zip_buf.seek(0)
    return zip_buf

def generate_consolidated_increment_pdf(records_list, company_data, with_letterhead=True):
    """Merges all employees' 1-page increment letters into a single batch-printable PDF using pypdfium2."""
    import pypdfium2 as pdfium
    master_pdf = pdfium.PdfDocument.new()
    for rec in records_list:
        merged_data = dict(company_data)
        merged_data.update(rec)
        pdf_buf = generate_increment_pdf(merged_data, with_letterhead=with_letterhead)
        src_pdf = pdfium.PdfDocument(pdf_buf)
        master_pdf.import_pages(src_pdf)
        src_pdf.close()
    
    out_buf = io.BytesIO()
    master_pdf.save(out_buf)
    master_pdf.close()
    out_buf.seek(0)
    return out_buf

# ==============================================================
# 4. EXPERIENCE CERTIFICATE (EXACT TEMPLATE INJECTION ENGINE)
# ==============================================================

def generate_experience_docx(data, with_letterhead=True):
    """Populates official '1. Experience Letter- Sample Format.docx' with exact 1-page A4 geometry."""
    template_path = os.path.join(TEMPLATES_DIR, "1. Experience Letter- Sample Format.docx")
    if not os.path.exists(template_path):
        return _generate_fallback_experience_docx(data)

    doc = Document(template_path)
    sec = doc.sections[0]
    
    sec.page_width = Inches(8.27)
    sec.page_height = Inches(11.69)
    
    if with_letterhead:
        sec.top_margin = Inches(1.35)
        sec.bottom_margin = Inches(0.40)
        sec.left_margin = Inches(0.80)
        sec.right_margin = Inches(0.80)
    else:
        sec.top_margin = Inches(1.90)
        sec.bottom_margin = Inches(0.40)
        sec.left_margin = Inches(0.80)
        sec.right_margin = Inches(0.80)
        for p in sec.header.paragraphs:
            p.text = ''
            for d in p._p.xpath('.//w:drawing'):
                d.getparent().remove(d)

    ref_no = str(data.get('ref_no', 'AIPL/HR/EXP/2026/089'))
    letter_date = str(data.get('date', datetime.today().strftime('%d %B %Y')))
    name = str(data.get('candidate_name', data.get('emp_name', 'Mr. Employee'))).upper()
    desig = str(data.get('designation', 'Senior Technician')).upper()
    dept = str(data.get('department', 'Mechanical & Piping')).upper()
    site = str(data.get('site', 'Mundra Petrochem Limited')).upper()
    start_d = str(data.get('doj', data.get('start_date', '01-05-2023')))
    end_d = str(data.get('dor', data.get('end_date', '31-10-2026')))

    # P2: Ref No & Date
    if len(doc.paragraphs) > 2:
        p2 = doc.paragraphs[2]
        p2.text = f"Ref. No.: {ref_no}\t\t\t\t\t\tDate: {letter_date}"
        p2.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for r in p2.runs:
            r.font.name = 'Aptos Narrow'
            r.font.size = Pt(10)
            r.font.bold = True

    # P8: Main certification text
    if len(doc.paragraphs) > 8:
        p8 = doc.paragraphs[8]
        p8.text = f"This is to certify that {name} was associated with AAIKRUPA INFRATECH PVT. LTD. in the capacity of {desig} in {dept} at our project site {site}. He was associated with the Company from {start_d} to {end_d} and was responsible for managing and coordinating assigned project/site activities, ensuring effective execution of work, coordinating with the project team and supporting the achievement of organizational and project objectives."
        for r in p8.runs:
            r.font.name = 'Aptos Narrow'
            r.font.size = Pt(10.5)

    # Set clean spacing and Aptos Narrow font across all paragraphs
    for p in doc.paragraphs:
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        for r in p.runs:
            r.font.name = 'Aptos Narrow'
            if r.font.size is None:
                r.font.size = Pt(10.5)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def generate_experience_pdf(data, with_letterhead=True):
    """Generates official 1-page A4 PDF Experience Certificate with native Word COM vector quality."""
    docx_buf = generate_experience_docx(data, with_letterhead=with_letterhead)
    pdf_buf = docx_to_pdf_word_com(docx_buf)
    if pdf_buf:
        return pdf_buf
    return _generate_reportlab_experience_pdf(data)

def _generate_reportlab_experience_pdf(data):
    """Fallback ReportLab generator for Experience Certificate."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=portrait(A4), leftMargin=18*mm, rightMargin=18*mm, topMargin=25*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    p_style = ParagraphStyle('ExpP', parent=styles['Normal'], fontName='Helvetica', fontSize=10.5, leading=15, spaceAfter=8)
    elements = [
        Paragraph(f"<b>Ref. No.:</b> {data.get('ref_no')} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Date:</b> {data.get('date')}", p_style),
        Spacer(1, 10*mm),
        Paragraph("<para align='center'><b><u>EXPERIENCE CERTIFICATE</u></b></para>", p_style),
        Paragraph("<para align='center'><b>TO WHOMSOEVER IT MAY CONCERN</b></para>", p_style),
        Spacer(1, 6*mm),
        Paragraph(f"This is to certify that <b>{data.get('emp_name', data.get('candidate_name'))}</b> was associated with <b>AAIKRUPA INFRATECH PVT. LTD.</b> in the capacity of <b>{data.get('designation')}</b> in <b>{data.get('department')}</b> at our project site <b>{data.get('site')}</b> from {data.get('doj')} to {data.get('dor')}.", p_style),
        Paragraph("During his tenure with the Company, he demonstrated professionalism, commitment and responsibility towards his assigned duties. He maintained a professional and responsible approach while coordinating with the project team and Management, contributing effectively to the smooth execution of assigned responsibilities.", p_style),
        Paragraph("His conduct and performance during his tenure with the Company were found to be satisfactory.", p_style),
        Paragraph("We appreciate his contribution and association with the organization and wish him success, growth and prosperity in all his future professional endeavours.", p_style),
        Paragraph("This certificate is being issued at his request for whatever purpose it may serve.", p_style),
        Spacer(1, 12*mm),
        Paragraph(f"<b>For AAIKRUPA INFRATECH PVT. LTD.</b><br/><br/><br/><b>{data.get('signatory_name', 'Authorized Signatory')}</b>", p_style)
    ]
    doc.build(elements)
    buf.seek(0)
    return buf

def _generate_fallback_experience_docx(data):
    doc = Document()
    doc.add_paragraph("EXPERIENCE CERTIFICATE")
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

# ==============================================================
# 5. SALARY CALCULATOR & OFFER LETTER OF EMPLOYMENT (3-PAGE STRICT)
# ==============================================================

def excel_round(x, n=0):
    """Excel standard half-up rounding: floor(x * 10^n + 0.5) / 10^n."""
    factor = 10 ** n
    return math.floor(float(x) * factor + 0.5) / factor

def compute_salary_breakdown(gross, is_staff=True, is_helper=False, esic_opt="YES", pt_val=0):
    """
    Computes official 17-row salary breakdown adhering to Gujarat / Indian industrial standards
    and company payroll formula matrix in '13. Structure of Salary Sample.xlsx'.
    """
    gross = float(gross)
    min_wage = 13351.0 if is_helper else 13897.0
    basic = max(excel_round(gross * 0.50), min_wage)
    hra = excel_round(basic * 0.40)
    bonus = excel_round(basic * 0.0833)
    leave = excel_round(basic * 0.05)
    other = gross - (basic + hra + bonus + leave)
    special = 0.0
    
    pf_wage = min(basic, 25000.0)
    emp_pf = excel_round(pf_wage * 0.12)
    empr_pf = excel_round(pf_wage * 0.13)
    
    # ESIC eligibility ceiling is ₹21,000 gross
    if str(esic_opt).upper() == "YES" and gross <= 21000.0:
        emp_esic = excel_round(gross * 0.0075)
        empr_esic = excel_round(gross * 0.0325)
    else:
        emp_esic = 0.0
        empr_esic = 0.0
        
    tot_ded = emp_pf + emp_esic + float(pt_val)
    in_hand = gross - tot_ded
    monthly_ctc = gross + empr_pf + empr_esic
    annual_ctc = monthly_ctc * 12.0
    
    return {
        'gross': gross,
        'basic': basic,
        'hra': hra,
        'bonus': bonus,
        'leave': leave,
        'other': other,
        'special': special,
        'emp_pf': emp_pf,
        'pt': float(pt_val),
        'emp_esic': emp_esic,
        'tot_ded': tot_ded,
        'in_hand': in_hand,
        'empr_pf': empr_pf,
        'empr_esic': empr_esic,
        'empr_other': 0.0,
        'monthly_ctc': monthly_ctc,
        'annual_ctc': annual_ctc
    }

def solve_gross_from_inhand(target_inhand, is_staff=True, is_helper=False, esic_opt="YES", pt_val=0):
    """Reverse-calculates exact integer Gross from desired Net In-Hand salary in <1ms."""
    target_inhand = float(target_inhand)
    low = max(1000, int(target_inhand))
    high = int(target_inhand * 2 + 25000)
    best_g = low
    min_diff = float('inf')
    while low <= high:
        mid = (low + high) // 2
        res = compute_salary_breakdown(mid, is_staff, is_helper, esic_opt, pt_val)
        diff = res['in_hand'] - target_inhand
        if abs(diff) < min_diff:
            min_diff = abs(diff)
            best_g = mid
        if diff == 0:
            return mid
        elif diff < 0:
            low = mid + 1
        else:
            high = mid - 1
    return best_g

def solve_gross_from_annual_ctc(target_annual_ctc, is_staff=True, is_helper=False, esic_opt="YES", pt_val=0):
    """Reverse-calculates exact integer Gross from offered Annual CTC in <1ms."""
    target_monthly_ctc = float(target_annual_ctc) / 12.0
    low = max(1000, int(target_monthly_ctc * 0.65))
    high = int(target_monthly_ctc)
    best_g = low
    min_diff = float('inf')
    while low <= high:
        mid = (low + high) // 2
        res = compute_salary_breakdown(mid, is_staff, is_helper, esic_opt, pt_val)
        diff = res['monthly_ctc'] - target_monthly_ctc
        if abs(diff) < min_diff:
            min_diff = abs(diff)
            best_g = mid
        if diff == 0:
            return mid
        elif diff < 0:
            low = mid + 1
        else:
            high = mid - 1
    return best_g

def solve_gross_from_monthly_ctc(target_monthly_ctc, is_staff=True, is_helper=False, esic_opt="YES", pt_val=0):
    """Reverse-calculates exact integer Gross from offered Monthly CTC."""
    return solve_gross_from_annual_ctc(float(target_monthly_ctc) * 12.0, is_staff, is_helper, esic_opt, pt_val)

def generate_joining_offer_docx(data, with_letterhead=True):
    """
    Populates official '12.Offer Letter of Employement.docx'
    strictly maintaining the user's calibrated page setup, original margins,
    original paragraph geometry, clean component names, and 17-row Table 2 (Annexure – A).
    """
    template_path = os.path.join(TEMPLATES_DIR, "12.Offer Letter of Employement.docx")
    if not os.path.exists(template_path):
        return _generate_fallback_offer_docx(data)

    doc = Document(template_path)
    sec = doc.sections[0]

    comp_name = str(data.get('establishment_name', data.get('company_name', 'AAIKRUPA INFRATECH PVT. LTD.'))).strip()
    is_aaikrupa = "AAIKRUPA" in comp_name.upper()

    # Header artwork handling: keep user's exact margins untouched
    if not with_letterhead or not is_aaikrupa:
        for p in sec.header.paragraphs:
            p.text = ''
            for d in p._p.xpath('.//w:drawing'):
                d.getparent().remove(d)

    # Candidate and offer parameters
    ref_no = str(data.get('ref_no', '')).strip()
    letter_date = str(data.get('date', datetime.today().strftime('%d/%m/%Y'))).strip()
    c_name = str(data.get('candidate_name', 'VIKRAM SINGH CHAUHAN')).strip()
    email = str(data.get('email', 'vikram.chauhan@example.com')).strip()
    mobile = str(data.get('mobile', data.get('phone', '+91 98250 12345'))).strip()
    desig = str(data.get('designation', 'SENIOR QC ENGINEER')).strip()
    dept = str(data.get('department', 'Quality Assurance & Control')).strip()
    doj = str(data.get('doj', data.get('reporting_date', '01/12/2026'))).strip()
    loc = str(data.get('location', data.get('site', 'MUNDRA PETROCHEM LIMITED (MPL Piping 250)'))).strip()
    rep_to = str(data.get('reporting_to', 'Project Head / Site In-charge')).strip()
    prob_period = str(data.get('probation_period', '90 Calendar Days')).strip()
    notice_period = str(data.get('notice_period', '30 Calendar Days')).strip()
    emp_id = str(data.get('emp_id', 'AIPL-2026-881')).strip()
    sig_name = str(data.get('signatory_name', 'Tarun Swami')).strip()
    sig_desig = str(data.get('signatory_title', 'Authorized Signatory / Managing Director')).strip()

    # Determine or calculate salary breakdown
    if 'salary_breakdown' in data and isinstance(data['salary_breakdown'], dict):
        brk = data['salary_breakdown']
    elif 'brk' in data and isinstance(data['brk'], dict):
        brk = data['brk']
    else:
        is_staff = data.get('is_staff', True)
        is_helper = 'HELPER' in desig.upper() or str(data.get('category', '')).upper() == 'HELPER'
        esic_opt = str(data.get('esic_opt', 'YES')).upper()
        pt_val = float(data.get('pt_val', data.get('pt', 0)))

        if 'gross' in data and float(data.get('gross', 0)) > 0:
            gross = float(data['gross'])
        elif 'in_hand' in data and float(data.get('in_hand', 0)) > 0:
            gross = solve_gross_from_inhand(float(data['in_hand']), is_staff, is_helper, esic_opt, pt_val)
        elif 'annual_ctc' in data and float(data.get('annual_ctc', 0)) > 0:
            gross = solve_gross_from_annual_ctc(float(data['annual_ctc']), is_staff, is_helper, esic_opt, pt_val)
        elif 'monthly_salary' in data and float(data.get('monthly_salary', 0)) > 0:
            gross = float(data['monthly_salary'])
        else:
            gross = 35000.0
            
        brk = compute_salary_breakdown(gross, is_staff=is_staff, is_helper=is_helper, esic_opt=esic_opt, pt_val=pt_val)

    # 1. Exact Text Replacements - maintain all original paragraphs and spacers intact
    for p in doc.paragraphs:
        txt = p.text
        if not txt.strip():
            continue
        if '[DD/MM/YYYY]' in txt:
            p.text = txt.replace('[DD/MM/YYYY]', letter_date)
        if '[EMPLOYEE FULL NAME]' in txt:
            p.text = p.text.replace('[EMPLOYEE FULL NAME]', c_name).replace('[EMAIL ADDRESS]', email).replace('[MOBILE NUMBER]', mobile)
        if '[EMPLOYEE NAME]' in txt:
            p.text = p.text.replace('[EMPLOYEE NAME]', c_name)
        if '[DESIGNATION]' in txt:
            p.text = p.text.replace('[DESIGNATION]', desig)
        if '[Employee Full Name]' in txt:
            p.text = p.text.replace('[Employee Full Name]', c_name)
        if '[Date of Joining]' in txt:
            p.text = p.text.replace('[Date of Joining]', doj)
        if '[Employee Name]' in txt:
            p.text = p.text.replace('[Employee Name]', c_name).replace('[Designation]', desig).replace('[Employee ID]', emp_id)
        if 'Employee Name: __________________________' in txt:
            p.text = p.text.replace('Employee Name: __________________________', f'Employee Name: {c_name}')
        if 'Name: __________________________' in txt and 'Designation: ____________________' in txt:
            p.text = p.text.replace('Name: __________________________', f'Name: {sig_name}').replace('Designation: ____________________', f'Designation: {sig_desig}')

        if not is_aaikrupa:
            if 'AAIKRUPA INFRATECH PVT. LTD.' in p.text:
                p.text = p.text.replace('AAIKRUPA INFRATECH PVT. LTD.', comp_name)
            if 'Aaikrupa Infratech Pvt. Ltd.' in p.text:
                p.text = p.text.replace('Aaikrupa Infratech Pvt. Ltd.', comp_name)

    # 2. Format Table 0 (Summary Particulars)
    t0 = doc.tables[0]
    t0.rows[1].cells[1].text = desig
    t0.rows[2].cells[1].text = dept
    t0.rows[3].cells[1].text = doj
    t0.rows[4].cells[1].text = loc
    t0.rows[5].cells[1].text = rep_to
    t0.rows[6].cells[1].text = prob_period
    t0.rows[7].cells[1].text = notice_period
    t0.rows[8].cells[1].text = f"₹ {brk['annual_ctc']:,.2f} (As specified in Annexure – A)"

    # 3. Clean Standard Components for Table 2 (Annexure - A) - No formulas or rules in component names
    clean_components = [
        "Basic Salary",
        "HRA",
        "Advance / Variable Bonus",
        "Leave Component",
        "Other Earnings",
        "Special Allowance",
        "GROSS SALARY",
        "Employee PF Contribution",
        "Professional Tax",
        "ESIC / Other Deductions",
        "TOTAL DEDUCTIONS",
        "NET PAY (IN HAND)",
        "Employer PF Contribution",
        "Employer ESIC Contribution",
        "Other Employer Contributions",
        "TOTAL CTC"
    ]

    t2 = doc.tables[2]
    row_values = [
        (1, clean_components[0], brk['basic'], brk['basic'] * 12),
        (2, clean_components[1], brk['hra'], brk['hra'] * 12),
        (3, clean_components[2], brk['bonus'], brk['bonus'] * 12),
        (4, clean_components[3], brk['leave'], brk['leave'] * 12),
        (5, clean_components[4], brk['other'], brk['other'] * 12),
        (6, clean_components[5], brk['special'], brk['special'] * 12),
        (7, clean_components[6], brk['gross'], brk['gross'] * 12),
        (8, clean_components[7], brk['emp_pf'], brk['emp_pf'] * 12),
        (9, clean_components[8], brk['pt'], brk['pt'] * 12),
        (10, clean_components[9], brk['emp_esic'], brk['emp_esic'] * 12),
        (11, clean_components[10], brk['tot_ded'], brk['tot_ded'] * 12),
        (12, clean_components[11], brk['in_hand'], brk['in_hand'] * 12),
        (13, clean_components[12], brk['empr_pf'], brk['empr_pf'] * 12),
        (14, clean_components[13], brk['empr_esic'], brk['empr_esic'] * 12),
        (15, clean_components[14], brk['empr_other'], brk['empr_other'] * 12),
        (16, clean_components[15], brk['monthly_ctc'], brk['annual_ctc']),
    ]

    for r_idx, comp_name_clean, m_val, a_val in row_values:
        row = t2.rows[r_idx]
        row.cells[0].text = comp_name_clean
        row.cells[1].text = f"₹ {m_val:,.2f}"
        row.cells[2].text = f"₹ {a_val:,.2f}"

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def generate_joining_offer_pdf(data, with_letterhead=True):
    """Generates official 3-page Joining Offer Letter A4 PDF using Microsoft Word COM engine."""
    docx_buf = generate_joining_offer_docx(data, with_letterhead=with_letterhead)
    pdf_buf = docx_to_pdf_word_com(docx_buf)
    if pdf_buf:
        return pdf_buf
    return _generate_reportlab_offer_pdf(data)

def _generate_fallback_offer_docx(data):
    doc = Document()
    doc.add_paragraph("OFFER OF EMPLOYMENT")
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def _generate_reportlab_offer_pdf(data):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=portrait(A4), leftMargin=15*mm, rightMargin=15*mm, topMargin=12*mm, bottomMargin=12*mm)
    styles = getSampleStyleSheet()
    p_style = ParagraphStyle('LetterText', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=13)
    p_bold = ParagraphStyle('LetterBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.5, leading=13)
    comp_name = data.get('establishment_name', data.get('company_name', 'AAIKRUPA INFRATECH PVT. LTD.'))
    c_name = data.get('candidate_name', 'Employee')
    desig = data.get('designation', '')
    site = data.get('location', data.get('site', 'Mundra'))
    brk = data.get('salary_breakdown', {})
    if not brk:
        brk = compute_salary_breakdown(data.get('gross', 35000))
    
    elements = [
        Paragraph(f"<b>{comp_name.upper()}</b>", ParagraphStyle('H1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13, alignment=1, textColor=colors.HexColor('#1E3A8A'))),
        Paragraph(data.get('company_address', ''), ParagraphStyle('Sub', parent=styles['Normal'], fontName='Helvetica', fontSize=8, alignment=1, textColor=colors.HexColor('#64748B'))),
        Spacer(1, 4*mm),
        Paragraph("<b>OFFER OF EMPLOYMENT</b>", ParagraphStyle('H2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, alignment=1)),
        Spacer(1, 4*mm),
        Paragraph(f"<b>Date:</b> {data.get('date', datetime.today().strftime('%d/%m/%Y'))}<br/><b>To:</b> {c_name}<br/><b>Position:</b> {desig}<br/><b>Site:</b> {site}<br/><b>Annual CTC:</b> ₹ {brk['annual_ctc']:,.2f}", p_style),
        Spacer(1, 4*mm),
        Paragraph("<b>ANNEXURE – A: SALARY BREAKDOWN</b>", p_bold),
        Spacer(1, 2*mm)
    ]
    t_data = [
        ['Component', 'Monthly (₹)', 'Annual (₹)'],
        ['Basic Salary', f"₹ {brk['basic']:,.2f}", f"₹ {brk['basic']*12:,.2f}"],
        ['HRA', f"₹ {brk['hra']:,.2f}", f"₹ {brk['hra']*12:,.2f}"],
        ['Advance / Variable Bonus', f"₹ {brk['bonus']:,.2f}", f"₹ {brk['bonus']*12:,.2f}"],
        ['Leave Component', f"₹ {brk['leave']:,.2f}", f"₹ {brk['leave']*12:,.2f}"],
        ['Other Earnings', f"₹ {brk['other']:,.2f}", f"₹ {brk['other']*12:,.2f}"],
        ['GROSS SALARY', f"₹ {brk['gross']:,.2f}", f"₹ {brk['gross']*12:,.2f}"],
        ['Employee PF Contribution', f"₹ {brk['emp_pf']:,.2f}", f"₹ {brk['emp_pf']*12:,.2f}"],
        ['Professional Tax', f"₹ {brk['pt']:,.2f}", f"₹ {brk['pt']*12:,.2f}"],
        ['ESIC / Other Deductions', f"₹ {brk['emp_esic']:,.2f}", f"₹ {brk['emp_esic']*12:,.2f}"],
        ['TOTAL DEDUCTIONS', f"₹ {brk['tot_ded']:,.2f}", f"₹ {brk['tot_ded']*12:,.2f}"],
        ['NET PAY (IN HAND)', f"₹ {brk['in_hand']:,.2f}", f"₹ {brk['in_hand']*12:,.2f}"],
        ['Employer PF Contribution', f"₹ {brk['empr_pf']:,.2f}", f"₹ {brk['empr_pf']*12:,.2f}"],
        ['Employer ESIC Contribution', f"₹ {brk['empr_esic']:,.2f}", f"₹ {brk['empr_esic']*12:,.2f}"],
        ['TOTAL CTC', f"₹ {brk['monthly_ctc']:,.2f}", f"₹ {brk['annual_ctc']:,.2f}"],
    ]
    t = Table(t_data, colWidths=[80*mm, 50*mm, 50*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
    ]))
    elements.append(t)
    doc.build(elements)
    buf.seek(0)
    return buf

def generate_joining_offer_bulk_zip(records_list, company_data, with_letterhead=True, doc_type='pdf'):
    """Generates a ZIP archive containing 3-page offer letters for all candidates in the list."""
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for idx, rec in enumerate(records_list):
            merged_data = dict(company_data)
            merged_data.update(rec)
            c_name = str(merged_data.get('candidate_name', f'Candidate_{idx+1}')).replace(' ', '_')
            emp_id = str(merged_data.get('emp_id', f'OFFER_{idx+1}')).replace('/', '_')
            
            if doc_type == 'docx':
                doc_buf = generate_joining_offer_docx(merged_data, with_letterhead=with_letterhead)
                zf.writestr(f"Offer_{emp_id}_{c_name}.docx", doc_buf.getvalue())
            else:
                pdf_buf = generate_joining_offer_pdf(merged_data, with_letterhead=with_letterhead)
                zf.writestr(f"Offer_{emp_id}_{c_name}.pdf", pdf_buf.getvalue())
    zip_buf.seek(0)
    return zip_buf

def generate_consolidated_joining_offer_pdf(records_list, company_data, with_letterhead=True):
    """Merges all candidates' 3-page offer letters into a single batch-printable master PDF."""
    import pypdfium2 as pdfium
    master_pdf = pdfium.PdfDocument.new()
    for rec in records_list:
        merged_data = dict(company_data)
        merged_data.update(rec)
        pdf_buf = generate_joining_offer_pdf(merged_data, with_letterhead=with_letterhead)
        src_pdf = pdfium.PdfDocument(pdf_buf)
        master_pdf.import_pages(src_pdf)
        src_pdf.close()
    
    out_buf = io.BytesIO()
    master_pdf.save(out_buf)
    master_pdf.close()
    out_buf.seek(0)
    return out_buf

def generate_warning_docx(data):
    doc = Document()
    doc.add_paragraph(f"DISCIPLINARY NOTICE: {data.get('warning_level', 'FIRST WARNING').upper()}\n")
    doc.add_paragraph(f"To, {data.get('emp_name')} ({data.get('emp_id')})\nDesignation: {data.get('designation')}\nSite: {data.get('site')}\n\nSubject: {data.get('violation_type')}\n\nDetails: {data.get('incident_details')}\n\nPlease submit written explanation within {data.get('reply_days', 48)} hours.")
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def generate_warning_pdf(data):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=portrait(A4), leftMargin=15*mm, rightMargin=15*mm, topMargin=12*mm, bottomMargin=12*mm)
    styles = getSampleStyleSheet()
    p_style = ParagraphStyle('LetterText', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14)
    elements = [
        Paragraph("<b>AAIKRUPA INFRATECH PVT. LTD.</b>", ParagraphStyle('H1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14, alignment=1)),
        Spacer(1, 4*mm),
        Paragraph(f"<b>DISCIPLINARY NOTICE — {data.get('warning_level', 'FIRST WARNING').upper()}</b>", ParagraphStyle('H2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, alignment=1, textColor=colors.red)),
        Spacer(1, 4*mm),
        Paragraph(f"<b>To:</b> {data.get('emp_name')} ({data.get('emp_id')})<br/><b>Violation:</b> {data.get('violation_type')}<br/><b>Details:</b> {data.get('incident_details')}<br/><b>Deadline:</b> {data.get('reply_days', 48)} Hours", p_style),
        Spacer(1, 8*mm),
        Paragraph("For, Aaikrupa Infratech Pvt. Ltd.<br/><br/>Authorized Signatory", p_style)
    ]
    doc.build(elements)
    buf.seek(0)
    return buf

def generate_review_docx(data):
    doc = Document()
    doc.add_paragraph("CONFIRMATION OF SERVICE LETTER\n")
    doc.add_paragraph(f"To, {data.get('emp_name')} ({data.get('emp_id')})\nDesignation: {data.get('designation')}\nSite: {data.get('site')}\n\nEffective Date: {data.get('effective_date')}\nRating: {data.get('rating')}\nRemarks: {data.get('remarks')}")
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

def generate_review_pdf(data):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=portrait(A4), leftMargin=15*mm, rightMargin=15*mm, topMargin=12*mm, bottomMargin=12*mm)
    styles = getSampleStyleSheet()
    p_style = ParagraphStyle('LetterText', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14)
    elements = [
        Paragraph("<b>AAIKRUPA INFRATECH PVT. LTD.</b>", ParagraphStyle('H1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14, alignment=1)),
        Spacer(1, 4*mm),
        Paragraph("<b>CONFIRMATION OF EMPLOYMENT LETTER</b>", ParagraphStyle('H2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, alignment=1)),
        Spacer(1, 4*mm),
        Paragraph(f"<b>To:</b> {data.get('emp_name')} ({data.get('emp_id')})<br/><b>Confirmation Effective Date:</b> {data.get('effective_date')}<br/><b>Rating:</b> {data.get('rating')}<br/><b>Remarks:</b> {data.get('remarks')}", p_style),
        Spacer(1, 8*mm),
        Paragraph("For, Aaikrupa Infratech Pvt. Ltd.<br/><br/>Authorized Signatory", p_style)
    ]
    doc.build(elements)
    buf.seek(0)
    return buf
