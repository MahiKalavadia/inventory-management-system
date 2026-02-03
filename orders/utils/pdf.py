from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from django.conf import settings
import os


def build_receipt_pdf(buffer, order):
    styles = getSampleStyleSheet()
    elements = []

    # -------- Company Header --------
    logo_path = os.path.join(settings.BASE_DIR, "static/images/logo.jpeg")
    if os.path.exists(logo_path):
        elements.append(Image(logo_path, width=120, height=60))

    elements.append(
        Paragraph("<b>SMART INVENTORY SYSTEM</b>", styles["Title"]))
    elements.append(Paragraph("Sales Receipt / Invoice", styles["Heading2"]))
    elements.append(Spacer(1, 12))

    # -------- Customer + Order Info --------
    info_style = ParagraphStyle(name='info', fontSize=10, leading=14)

    elements.append(
        Paragraph(f"<b>Bill No:</b> {order.bill_number}", info_style))
    elements.append(
        Paragraph(f"<b>Customer:</b> {order.customer_name}", info_style))
    elements.append(
        Paragraph(f"<b>Email:</b> {order.customer_email}", info_style))
    elements.append(
        Paragraph(f"<b>Date:</b> {order.created_at.strftime('%d %b %Y')}", info_style))
    elements.append(Spacer(1, 15))

    # -------- Items Table --------
    table_data = [["Product", "Unit Price", "Qty", "Warranty", "Total"]]

    for item in order.items.all():

        # Warranty display
        if item.warranty_months > 0 and item.warranty_end:
            warranty_text = f"{item.warranty_months}Months\nValid till {item.warranty_end.strftime('%d-%m-%Y')}"
        else:
            warranty_text = "No Warranty"

        table_data.append([
            str(item.product),
            f"₹ {item.price}",
            item.quantity,
            warranty_text,
            f"₹ {item.total}",
        ])

    # Grand total row
    table_data.append(["", "", "", "Grand Total", f"₹ {order.total_amount}"])

    table = Table(table_data, colWidths=[160, 80, 40, 120, 80])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
        ("BACKGROUND", (-2, -1), (-1, -1), colors.lightgrey),
        ("FONTNAME", (-2, -1), (-1, -1), "Helvetica-Bold"),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # -------- Warranty Terms Footer --------
    elements.append(Paragraph("<b>Warranty Terms:</b>", styles["Normal"]))
    elements.append(
        Paragraph("• Warranty starts from invoice date.", styles["Normal"]))
    elements.append(
        Paragraph("• Original bill required for claims.", styles["Normal"]))
    elements.append(
        Paragraph("• Physical / liquid damage not covered.", styles["Normal"]))
    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph("Thank you for your purchase!", styles["Normal"]))
    elements.append(
        Paragraph("This is a computer-generated invoice.", styles["Italic"]))

    # Build PDF
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    doc.build(elements)
