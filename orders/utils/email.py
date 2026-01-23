from django.core.mail import EmailMessage
from .pdf import build_receipt_pdf
from io import BytesIO


def send_receipt_email(order):
    if not order.customer_email:
        return  # skip if no email

    # Create in-memory PDF
    pdf_buffer = BytesIO()
    build_receipt_pdf(pdf_buffer, order)  # write PDF to buffer
    pdf_buffer.seek(0)  # move to beginning before reading

    # Create email
    email = EmailMessage(
        subject=f"Your Order Receipt - #{order.id}",
        body=f"""
Hello {order.customer_name},

Thank you for your order.

Order ID: {order.id}
Total Amount: ₹ {order.total_amount}

Your receipt is attached with this email.

Regards,
Smart Inventory Team
""",
        to=[order.customer_email],
    )

    # Attach PDF
    email.attach(
        f"receipt_order_{order.id}.pdf",
        pdf_buffer.read(),
        "application/pdf"
    )

    # Send email
    email.send(fail_silently=False)
