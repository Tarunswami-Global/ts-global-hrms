import io
from docx import Document
from docx.shared import Mm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.section import WD_ORIENT

def set_cell_format(cell, text, font_name="Times New Roman", font_size=8.5, bold=False, align=WD_ALIGN_PARAGRAPH.CENTER):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(1)
    run = p.add_run(str(text))
    run.font.name = font_name
    run.font.size = Pt(font_size)
    run.bold = bold
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

def generate_form18_docx(master_df, selected_keys, contractor_name, up_to_month_num, font_name="Times New Roman", page_orient="Landscape", skip_zero_days=True):
    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE if page_orient == "Landscape" else WD_ORIENT.PORTRAIT
    section.page_width = Mm(297) if page_orient == "Landscape" else Mm(210)
    section.page_height = Mm(210) if page_orient == "Landscape" else Mm(297)
    section.top_margin = section.bottom_margin = section.left_margin = section.right_margin = Mm(10)

    filtered_df = master_df[master_df['MonthNum'] <= up_to_month_num]
    if skip_zero_days:
        filtered_df = filtered_df[filtered_df['DaysWorked'] > 0]

    valid_keys = [k for k in selected_keys if not filtered_df[filtered_df['EmpKey'] == k].empty]

    for idx, emp_key in enumerate(valid_keys):
        emp_rows = filtered_df[filtered_df['EmpKey'] == emp_key].sort_values(by=['Year', 'MonthNum'])
        last_row = emp_rows.iloc[-1]
        dojs = [d for d in emp_rows['DOJ'] if d != '']
        doj_val = dojs[0] if dojs else ""

        p1 = doc.add_paragraph()
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r1 = p1.add_run("FORM NO. 18\n")
        r1.font.name = font_name
        r1.font.size = Pt(12)
        r1.bold = True
        r2 = p1.add_run("(Prescribed under Rule 94 of the Gujarat Factories Rules, 1963)\nREGISTER OF LEAVE WITH WAGES")
        r2.font.name = font_name
        r2.font.size = Pt(9.5)
        r2.bold = True

        meta_tbl = doc.add_table(rows=3, cols=3)
        meta_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        meta_data = [
            (f"Sr. No.: {idx + 1}", f"Contractor: {contractor_name}", f"Principal Employer: {last_row['PrincipalEmployer']}"),
            (f"Worker Name: {last_row['Name']}", f"Father's Name: {last_row['Fathername']}", f"Department: {last_row['Department']}"),
            (f"Designation: {last_row['Designation']}", f"Date of Joining: {doj_val}", f"Year: {last_row['Year']} (Part-I : Adults)")
        ]
        for r_i, row_tuple in enumerate(meta_data):
            for c_i, val in enumerate(row_tuple):
                set_cell_format(meta_tbl.cell(r_i, c_i), val, font_name=font_name, font_size=9, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT)

        doc.add_paragraph().paragraph_format.space_after = Pt(2)

        headers = [
            "Month / Period", "Days Worked", "Lay-off", "Maternity Leave",
            "Leave with Wages Enjoyed", "Total (Col 9-12)", "Regular Leave Earned",
            "Refused Leave", "Regular Leave Balance", "Leave Period (Days)",
            "Normal Rate of Wages (Rs.)", "Cash Equiv.", "Rate of Wages for Leave (Rs.)",
            "Total Wages Paid for Leave (Rs.)", "Remarks"
        ]

        tbl = doc.add_table(rows=2, cols=len(headers))
        tbl.style = 'Table Grid'
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

        for c_i, h_text in enumerate(headers):
            set_cell_format(tbl.cell(0, c_i), h_text, font_name=font_name, font_size=8, bold=True)
            set_cell_format(tbl.cell(1, c_i), f"({c_i + 1})", font_name=font_name, font_size=7.5, bold=True)

        tot_worked = tot_layoff = tot_mat = tot_enjoyed = tot_9to12 = tot_wages = 0
        for _, r in emp_rows.iterrows():
            row_cells = tbl.add_row().cells
            vals = [
                r['MonthLabel'], r['DaysWorked'], r['Layoff'], r['Maternity'],
                r['LeaveEnjoyed'], r['Total9to12'], r['RegLeaveEarned'],
                r['Refused'], r['RegularCol'], r['LeavePeriod'],
                r['NormalRate'], r['CashEquiv'], r['RateLeaveWages'],
                r['TotalLeaveWages'], ""
            ]
            tot_worked += r['DaysWorked']
            tot_layoff += r['Layoff']
            tot_mat += r['Maternity']
            tot_enjoyed += r['LeaveEnjoyed']
            tot_9to12 += r['Total9to12']
            tot_wages += r['TotalLeaveWages']
            for c_i, v in enumerate(vals):
                set_cell_format(row_cells[c_i], v, font_name=font_name, font_size=8.5, bold=False)

        tot_cells = tbl.add_row().cells
        tot_vals = [
            "TOTAL", tot_worked, tot_layoff, tot_mat, tot_enjoyed, tot_9to12,
            0, 0, 0, 0, last_row['NormalRate'], 0, last_row['RateLeaveWages'], tot_wages, ""
        ]
        for c_i, v in enumerate(tot_vals):
            set_cell_format(tot_cells[c_i], v, font_name=font_name, font_size=8.5, bold=True)

        p_foot = doc.add_paragraph()
        p_foot.paragraph_format.space_before = Pt(14)
        p_foot.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_foot = p_foot.add_run(f"For, {contractor_name}\n\nAuthorized Signatory")
        r_foot.font.name = font_name
        r_foot.font.size = Pt(9)
        r_foot.bold = True

        if idx < len(valid_keys) - 1:
            doc.add_page_break()

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf
