from django.core.mail import EmailMultiAlternatives
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
            'currency': '₹',
        }


def send_receipt_email(order):
    if not order.customer_email:
        return

    company = get_company_info()
    cur = company['currency']

    # Generate PDF attachment
    pdf_buffer = BytesIO()
    build_receipt_pdf(pdf_buffer, order)
    pdf_buffer.seek(0)

    # Build items rows for HTML
    items_rows = ""
    for item in order.items.all():
        if item.warranty_end:
            warranty = f"{item.warranty_months} months · Until {item.warranty_end.strftime('%d %b %Y')}"
        else:
            warranty = f"{item.warranty_months} months"

        items_rows += f"""
        <tr>
            <td style="padding:10px 12px; border-bottom:1px solid #f0f0f0; font-weight:600; color:#111827;">{item.product.name}</td>
            <td style="padding:10px 12px; border-bottom:1px solid #f0f0f0; text-align:center; color:#374151;">{cur}{item.price:.2f}</td>
            <td style="padding:10px 12px; border-bottom:1px solid #f0f0f0; text-align:center; color:#374151;">{item.quantity}</td>
            <td style="padding:10px 12px; border-bottom:1px solid #f0f0f0; text-align:center; color:#6b7280; font-size:12px;">{warranty}</td>
            <td style="padding:10px 12px; border-bottom:1px solid #f0f0f0; text-align:right; font-weight:700; color:#111827;">{cur}{item.total:.2f}</td>
        </tr>"""

    subject = f"Invoice {order.bill_number} — {company['name']}"

    # ── HTML body ──
    html_body = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0; padding:0; background:#f1f5f9; font-family:'Segoe UI',Arial,sans-serif;">

<div style="max-width:600px; margin:32px auto; background:#fff; border-radius:16px; overflow:hidden; box-shadow:0 8px 32px rgba(0,0,0,0.08);">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#1e1b4b,#4f46e5,#0ea5e9); padding:32px 36px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="font-size:20px; font-weight:800; color:#fff; letter-spacing:-0.02em;">{company['name']}</div>
                <div style="font-size:12px; color:rgba(255,255,255,0.6); margin-top:3px;">Order Confirmation & Invoice</div>
            </div>
            <div style="background:rgba(255,255,255,0.15); border:2px solid rgba(255,255,255,0.35); color:#fff; border-radius:8px; padding:6px 16px; font-size:11px; font-weight:800; letter-spacing:0.1em;">✓ PAID</div>
        </div>
    </div>

    <!-- Greeting -->
    <div style="padding:28px 36px 0;">
        <p style="font-size:15px; color:#111827; font-weight:600; margin:0 0 6px;">Dear {order.customer_name},</p>
        <p style="font-size:14px; color:#6b7280; margin:0 0 24px; line-height:1.6;">
            Thank you for your purchase. Your order has been confirmed and the invoice is attached to this email as a PDF.
        </p>
    </div>

    <!-- Order meta -->
    <div style="margin:0 36px 24px; background:#f8fafc; border:1px solid #e5e7eb; border-radius:12px; padding:16px 20px;">
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
            <div>
                <div style="font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:#9ca3af; margin-bottom:3px;">Bill Number</div>
                <div style="font-size:14px; font-weight:700; color:#4f46e5; font-family:monospace;">{order.bill_number}</div>
            </div>
            <div>
                <div style="font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:#9ca3af; margin-bottom:3px;">Order Date</div>
                <div style="font-size:14px; font-weight:700; color:#111827;">{order.created_at.strftime('%d %b %Y')}</div>
            </div>
            <div>
                <div style="font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:#9ca3af; margin-bottom:3px;">Payment</div>
                <div style="font-size:14px; font-weight:700; color:#16a34a;">{order.payment_status}</div>
            </div>
            <div>
                <div style="font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:#9ca3af; margin-bottom:3px;">Grand Total</div>
                <div style="font-size:16px; font-weight:800; color:#111827;">{cur}{order.total_amount}</div>
            </div>
        </div>
    </div>

    <!-- Items table -->
    <div style="margin:0 36px 24px;">
        <div style="font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:#9ca3af; margin-bottom:10px;">Order Items</div>
        <table style="width:100%; border-collapse:collapse; border:1px solid #e5e7eb; border-radius:10px; overflow:hidden;">
            <thead>
                <tr style="background:#f8fafc;">
                    <th style="padding:10px 12px; text-align:left; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:#94a3b8; border-bottom:1px solid #e5e7eb;">Product</th>
                    <th style="padding:10px 12px; text-align:center; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:#94a3b8; border-bottom:1px solid #e5e7eb;">Price</th>
                    <th style="padding:10px 12px; text-align:center; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:#94a3b8; border-bottom:1px solid #e5e7eb;">Qty</th>
                    <th style="padding:10px 12px; text-align:center; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:#94a3b8; border-bottom:1px solid #e5e7eb;">Warranty</th>
                    <th style="padding:10px 12px; text-align:right; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:#94a3b8; border-bottom:1px solid #e5e7eb;">Total</th>
                </tr>
            </thead>
            <tbody>
                {items_rows}
                <tr style="background:#111827;">
                    <td colspan="4" style="padding:12px; text-align:right; color:rgba(255,255,255,0.7); font-size:13px; font-weight:600;">Grand Total</td>
                    <td style="padding:12px; text-align:right; color:#fff; font-size:16px; font-weight:800;">{cur}{order.total_amount}</td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- Delivery address -->
    <div style="margin:0 36px 28px; background:#f0fdf4; border:1px solid #a7f3d0; border-radius:10px; padding:14px 18px;">
        <div style="font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:#16a34a; margin-bottom:8px;">📍 Delivery Address</div>
        <div style="font-size:13px; color:#374151; line-height:1.6;">
            {order.customer_address}, {order.city} — {order.pincode}<br>
            {order.get_state_display()}
        </div>
    </div>

    <!-- Footer -->
    <div style="padding:20px 36px; border-top:1px dashed #e5e7eb; background:#fafafa; display:flex; justify-content:space-between; align-items:center;">
        <div>
            <div style="font-size:12px; font-weight:700; color:#374151;">{company['name']}</div>
            <div style="font-size:11px; color:#9ca3af; margin-top:2px;">{company['address']}</div>
            <div style="font-size:11px; color:#9ca3af;">{company['email']} · {company['phone']}</div>
        </div>
        <div style="font-size:10px; color:#9ca3af; text-align:right;">
            Invoice attached as PDF<br>
            Do not reply to this email
        </div>
    </div>

</div>
</body>
</html>"""

    # ── Plain text fallback ──
    plain_body = f"""Dear {order.customer_name},

Thank you for your purchase from {company['name']}.

Invoice: {order.bill_number}
Date: {order.created_at.strftime('%d %b %Y')}
Payment: {order.payment_status}
Total: {cur}{order.total_amount}

The invoice PDF is attached to this email.

{company['name']}
{company['address']}
{company['email']} | {company['phone']}
"""

    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.customer_email],
    )
    email.attach_alternative(html_body, "text/html")
    email.attach(
        f"Invoice_{order.bill_number}.pdf",
        pdf_buffer.read(),
        "application/pdf"
    )
    email.send(fail_silently=False)
