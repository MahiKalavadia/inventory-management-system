from django.core.mail import EmailMessage
from .pdf import build_receipt_pdf
from io import BytesIO


def send_receipt_email(order):
    if not order.customer_email:
        return

    pdf_buffer = BytesIO()
    build_receipt_pdf(pdf_buffer, order)
    pdf_buffer.seek(0)

    email = EmailMessage(
        subject=f"Invoice for Your Order #{order.id}",
        body=f"""
Hello {order.customer_name},

Your order has been successfully placed.

🧾 Order ID: {order.id}
💰 Total Amount: ₹ {order.total_amount}

Please find your invoice attached.

Thank you for shopping with us!
SMART INVENTORY SYSTEM
""",
        to=[order.customer_email],
    )

    email.attach(
        f"invoice_{order.id}.pdf",
        pdf_buffer.read(),
        "application/pdf"
    )

    email.send(fail_silently=False)
