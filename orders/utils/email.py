from django.core.mail import EmailMessage
from django.conf import settings
from io import BytesIO
from .pdf import build_receipt_pdf


def get_company_info():
    try:
        from settings_app.models import SystemSettings
        s = SystemSettings.load()
        return {
            'name': s.company_name,
            'address': s.company_address,
            'email': s.company_email,
            'phone': s.company_phone,
            'currency': s.currency_symbol,
        }
    except Exception:
        return {
            'name': 'Smart Inventory System',
            'address': 'Surat, Gujarat, India',
            'email': 'support@smartinventory.com',
            'phone': '+91 9876543210',
            'currency': '\u20b9',
        }


def send_receipt_email(order):
    if not order.customer_email:
        return

    company = get_company_info()

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

Thank you for your purchase from **{company['name']}**.

Your order has been successfully processed. Please find the invoice attached to this email.

----------------------------------------
\U0001f9fe Invoice Number: {order.bill_number}
\U0001f4c5 Order Date: {order.created_at.strftime('%d %b %Y')}
\U0001f4b3 Payment Status: {order.payment_status}
\U0001f4b0 Total Amount: {company['currency']} {order.total_amount}
----------------------------------------

\U0001f6e1\ufe0f Warranty Details:
{warranty_info}

If you have any questions regarding your order or warranty, feel free to contact our support team.

Best Regards,
{company['name']}
{company['address']}
Email: {company['email']}
Phone: {company['phone']}

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
