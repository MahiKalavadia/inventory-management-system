from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


def build_receipt_pdf(response, order):
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Order Receipt", styles["Title"]))
    elements.append(Paragraph(f"Order ID: {order.id}", styles["Normal"]))
    elements.append(
        Paragraph(f"Customer: {order.customer_name}", styles["Normal"]))
    elements.append(Paragraph("<br/>", styles["Normal"]))

    table_data = [["Product", "Price", "Qty", "Total"]]

    for item in order.items.all():
        table_data.append([
            str(item.product),
            f"₹ {item.price}",
            item.quantity,
            f"₹ {item.total}",
        ])

    table_data.append(["", "", "Grand Total", f"₹ {order.total_amount}"])

    table = Table(table_data, colWidths=[200, 80, 60, 80])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONT", (-2, -1), (-1, -1), "Helvetica-Bold"),
    ]))

    elements.append(table)
    SimpleDocTemplate(response).build(elements)
