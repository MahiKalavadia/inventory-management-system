from django.core.mail import EmailMessage
from django.conf import settings
from io import BytesIO
from .pdf import build_receipt_pdf


def send_receipt_email(order):
    if not order.customer_email:
        return

    # Generate PDF
    pdf_buffer = BytesIO()
    build_receipt_pdf(pdf_buffer, order)
    pdf_buffer.seek(0)

    # Warranty Details
    warranty_info = ""
    for item in order.items.all():
        warranty_info += f"- {item.product.name}: {item.warranty_months} months\n"

    # Professional Email Body
    subject = f"Invoice & Order Confirmation - {order.bill_number}"

    body = f"""
Dear {order.customer_name},

Thank you for your purchase from **Smart Inventory System**.

Your order has been successfully processed. Please find the invoice attached to this email.

----------------------------------------
🧾 Invoice Number: {order.bill_number}
📅 Order Date: {order.created_at.strftime('%d %b %Y')}
💳 Payment Status: {order.payment_status}
💰 Total Amount: ₹ {order.total_amount}
----------------------------------------

🛡️ Warranty Details:
{warranty_info}

If you have any questions regarding your order or warranty, feel free to contact our support team.

Best Regards,  
Smart Inventory System  
Surat, Gujarat  
Email: support@smartinventory.com  
Phone: +91 98765 43210  

This is an automated email. Please do not reply.
"""

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.customer_email],
    )

    # Attach Invoice PDF
    email.attach(
        f"Invoice_{order.bill_number}.pdf",
        pdf_buffer.read(),
        "application/pdf"
    )

    email.send(fail_silently=False)
