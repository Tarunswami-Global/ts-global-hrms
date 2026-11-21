import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

def generate_form18_pdf(master_df, selected_keys, contractor_name, up_to_month_num, page_orient="Landscape", skip_zero_days=True):
    buf = io.BytesIO()
    pg_size = landscape(A4) if page_orient == "Landscape" else portrait(A4)
    doc = SimpleDocTemplate(buf, pagesize=pg_size, leftMargin=10*mm, rightMargin=10*mm, topMargin=10*mm, bottomMargin=10*mm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Normal'], fontName='Times-Bold', fontSize=12, leading=14, alignment=1)
    sub_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontName='Times-Bold', fontSize=9, leading=11, alignment=1)
    cell_hdr = ParagraphStyle('CellHdr', parent=styles['Normal'], fontName='Times-Bold', fontSize=7, leading=8.5, alignment=1)
    meta_style = ParagraphStyle('MetaStyle', parent=styles['Normal'], fontName='Times-Bold', fontSize=8.5, leading=11)

    elements = []
    filtered_df = master_df[master_df['MonthNum'] <= up_to_month_num]
    if skip_zero_days:
        filtered_df = filtered_df[filtered_df['DaysWorked'] > 0]

    valid_keys = [k for k in selected_keys if not filtered_df[filtered_df['EmpKey'] == k].empty]

    for idx, emp_key in enumerate(valid_keys):
        emp_rows = filtered_df[filtered_df['EmpKey'] == emp_key].sort_values(by=['Year', 'MonthNum'])
        last_row = emp_rows.iloc[-1]
        dojs = [d for d in emp_rows['DOJ'] if d != '']
        doj_val = dojs[0] if dojs else ""

        elements.append(Paragraph("FORM NO. 18", title_style))
        elements.append(Paragraph("(Prescribed under Rule 94 of the Gujarat Factories Rules, 1963) — REGISTER OF LEAVE WITH WAGES", sub_style))
        elements.append(Spacer(1, 3*mm))

        meta_table_data = [
            [Paragraph(f"<b>Sr. No.:</b> {idx+1}", meta_style),
             Paragraph(f"<b>Establishment:</b> {contractor_name}", meta_style),
             Paragraph(f"<b>Principal Employer:</b> {last_row['PrincipalEmployer']}", meta_style)],
            [Paragraph(f"<b>Worker Name:</b> {last_row['Name']}", meta_style),
             Paragraph(f"<b>Father's Name:</b> {last_row['Fathername']}", meta_style),
             Paragraph(f"<b>Department:</b> {last_row['Department']}", meta_style)],
            [Paragraph(f"<b>Designation:</b> {last_row['Designation']}", meta_style),
             Paragraph(f"<b>Date of Joining:</b> {doj_val}", meta_style),
             Paragraph(f"<b>Year:</b> {last_row['Year']} (Part-I Adults)", meta_style)]
        ]
        m_tbl = Table(meta_table_data, colWidths=[85*mm, 95*mm, 90*mm] if page_orient == "Landscape" else [60*mm, 65*mm, 65*mm])
        m_tbl.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.75, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(m_tbl)
        elements.append(Spacer(1, 3*mm))

        headers = [
            "Month", "Days\nWorked", "Lay-\noff", "Maternity\nLeave", "Leave\nEnjoyed",
            "Total\n(9-12)", "Reg.\nEarned", "Refused", "Regular\nBalance", "Leave\nPeriod",
            "Normal\nRate (Rs)", "Cash\nEquiv.", "Leave Wage\nRate (Rs)", "Total Leave\nWages (Rs)", "Remarks"
        ]
        tbl_data = [
            [Paragraph(h.replace('\n', '<br/>'), cell_hdr) for h in headers],
            [f"({i+1})" for i in range(len(headers))]
        ]

        tot_worked = tot_layoff = tot_mat = tot_enjoyed = tot_9to12 = tot_wages = 0
        for _, r in emp_rows.iterrows():
            tbl_data.append([
                r['MonthLabel'], r['DaysWorked'], r['Layoff'], r['Maternity'], r['LeaveEnjoyed'],
                r['Total9to12'], r['RegLeaveEarned'], r['Refused'], r['RegularCol'], r['LeavePeriod'],
                r['NormalRate'], r['CashEquiv'], r['RateLeaveWages'], r['TotalLeaveWages'], ""
            ])
            tot_worked += r['DaysWorked']
            tot_layoff += r['Layoff']
            tot_mat += r['Maternity']
            tot_enjoyed += r['LeaveEnjoyed']
            tot_9to12 += r['Total9to12']
            tot_wages += r['TotalLeaveWages']

        tbl_data.append([
            "TOTAL", tot_worked, tot_layoff, tot_mat, tot_enjoyed, tot_9to12,
            0, 0, 0, 0, last_row['NormalRate'], 0, last_row['RateLeaveWages'], tot_wages, ""
        ])

        col_w = [20*mm, 17*mm, 14*mm, 18*mm, 17*mm, 16*mm, 16*mm, 15*mm, 16*mm, 16*mm, 20*mm, 16*mm, 22*mm, 24*mm, 23*mm]
        if page_orient == "Portrait":
            col_w = [w * 0.68 for w in col_w]

        main_tbl = Table(tbl_data, colWidths=col_w, repeatRows=2)
        main_tbl.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.6, colors.black),
            ('BACKGROUND', (0, 0), (-1, 1), colors.HexColor('#EAEAEA')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F5F5F5')),
            ('FONTNAME', (0, 1), (-1, 1), 'Times-Bold'),
            ('FONTNAME', (0, 2), (-1, -2), 'Times-Roman'),
            ('FONTNAME', (0, -1), (-1, -1), 'Times-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(main_tbl)
        elements.append(Spacer(1, 8*mm))
        elements.append(Paragraph(f"<para align='right'><b>For, {contractor_name} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<br/><br/>Authorized Signatory</b></para>", meta_style))

        if idx < len(valid_keys) - 1:
            elements.append(PageBreak())

    doc.build(elements)
    buf.seek(0)
    return buf
