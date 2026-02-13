from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from django.conf import settings
import os


def build_receipt_pdf(buffer, order):
    styles = getSampleStyleSheet()
    elements = []

    # ================= HEADER =================
    logo_path = os.path.join(settings.BASE_DIR, "static/images/image.png")

    header_table_data = []

    if os.path.exists(logo_path):
        logo = Image(logo_path, width=90, height=45)
    else:
        logo = Paragraph("<b>SMART INVENTORY SYSTEM</b>", styles["Title"])

    company_info = Paragraph("""
        <b>SMART INVENTORY SYSTEM</b><br/>
        Surat, Gujarat, India<br/>
        Email: support@smartinventory.com<br/>
        Phone: +91 9876543210
    """, styles["Normal"])

    header_table_data.append([logo, company_info])
    header_table = Table(header_table_data, colWidths=[120, 400])
    elements.append(header_table)
    elements.append(Spacer(1, 15))

    # ================= INVOICE TITLE =================
    title = Paragraph("<b>SALES INVOICE</b>",
                      ParagraphStyle("title", fontSize=16, alignment=1))
    elements.append(title)
    elements.append(Spacer(1, 10))

    # ================= CUSTOMER + ORDER INFO =================
    info_style = ParagraphStyle(name="info", fontSize=10, leading=14)

    left_info = f"""
        <b>Bill No:</b> {order.bill_number}<br/>
        <b>Date:</b> {order.created_at.strftime('%d %b %Y')}<br/>
        <b>Status:</b> {order.payment_status}
    """

    right_info = f"""
        <b>Customer Name:</b> {order.customer_name}<br/>
        <b>Email:</b> {order.customer_email}<br/>
        <b>Phone:</b> {order.customer_phonenumber}<br/>
        <b>Address:</b> {order.customer_address}, {order.city} - {order.pincode}
    """

    info_table = Table([
     
   [Paragraph(left_info, info_style), Paragraph(right_info, info_style)]
    ], colWidths=[260, 260])

    elements.append(info_table)
    elements.append(Spacer(1, 20))
    # ================= ITEMS TABLE =================
    table_data = [["Product", "Unit Price", "Qty", "Warranty", "Total"]]

    for item in order.items.all():
        if item.warranty_months and item.warranty_end:
            warranty_text = f"{item.warranty_months} months<br/>Valid till {item.warranty_end.strftime('%d-%m-%Y')}"
        else:
            warranty_text = "No Warranty"

        table_data.append([
            str(item.product),
            f"₹ {item.price:.2f}",
            str(item.quantity),
            Paragraph(warranty_text, info_style),
            f"₹ {item.total:.2f}",
        ])

    # Total Row
    table_data.append(["", "", "", "<b>Grand Total</b>",
                      f"₹ {order.total_amount:.2f}"])

    table = Table(table_data, colWidths=[200, 80, 40, 120, 80])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),

        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),

        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),

        # Total Row Styling
        ("BACKGROUND", (-2, -1), (-1, -1), colors.lightgrey),
        ("FONTNAME", (-2, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (-2, -1), (-1, -1), 11),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 25))

    # ================= TERMS =================
    elements.append(Paragraph("<b>Terms & Conditions</b>", styles["Heading4"]))
    elements.append(
        Paragraph("1. Warranty starts from invoice date.", styles["Normal"]))
    elements.append(Paragraph(
        "2. Original invoice required for warranty claims.", styles["Normal"]))
    elements.append(
        Paragraph("3. Physical / liquid damage not covered.", styles["Normal"]))
    elements.append(Spacer(1, 15))

    # ================= SIGNATURE FOOTER =================
    footer_table = Table([
        ["", "Authorized Signature"],
        ["", "________________________"]
    ], colWidths=[350, 200])

    elements.append(footer_table)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph(
        "This is a computer generated invoice. No signature required.",
        ParagraphStyle("footer", fontSize=9, textColor=colors.grey)
    ))

    # ================= BUILD PDF =================
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    doc.build(elements)
