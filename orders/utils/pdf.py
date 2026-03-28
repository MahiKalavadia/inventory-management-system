from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame
import os


# ── Palette ──────────────────────────────────────────────
C_DARK    = colors.HexColor("#111827")
C_INDIGO  = colors.HexColor("#4f46e5")
C_INDIGO2 = colors.HexColor("#1e1b4b")
C_SKY     = colors.HexColor("#0ea5e9")
C_GREEN   = colors.HexColor("#16a34a")
C_GREEN_L = colors.HexColor("#ecfdf5")
C_GREEN_B = colors.HexColor("#a7f3d0")
C_LIGHT   = colors.HexColor("#f8fafc")
C_BORDER  = colors.HexColor("#e5e7eb")
C_MUTED   = colors.HexColor("#9ca3af")
C_WHITE   = colors.white
C_RED_L   = colors.HexColor("#fef2f2")
C_RED_B   = colors.HexColor("#fecaca")
C_RED     = colors.HexColor("#b91c1c")
C_AMBER_L = colors.HexColor("#fffbeb")
C_AMBER_B = colors.HexColor("#fde68a")
C_AMBER   = colors.HexColor("#b45309")


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


# ── Style helpers ─────────────────────────────────────────
def S(name, font="Helvetica", size=9, color=C_DARK, align=0, leading=None, bold=False):
    return ParagraphStyle(
        name,
        fontName="Helvetica-Bold" if bold else font,
        fontSize=size,
        textColor=color,
        alignment=align,
        leading=leading or (size * 1.4),
    )


def P(text, style):
    return Paragraph(text, style)


# ── Canvas-level header drawn on every page ───────────────
def draw_header(c: rl_canvas.Canvas, doc, company, order):
    W, H = A4
    lm = doc.leftMargin

    # Gradient-feel header band (two rectangles)
    c.setFillColor(C_INDIGO2)
    c.rect(0, H - 52 * mm, W * 0.55, 52 * mm, fill=1, stroke=0)
    c.setFillColor(C_INDIGO)
    c.rect(W * 0.45, H - 52 * mm, W * 0.3, 52 * mm, fill=1, stroke=0)
    c.setFillColor(C_SKY)
    c.rect(W * 0.7, H - 52 * mm, W * 0.3, 52 * mm, fill=1, stroke=0)

    # Decorative circles
    c.setFillColor(colors.HexColor("#ffffff"), alpha=0.06)
    c.circle(W - 18 * mm, H - 10 * mm, 28 * mm, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#ffffff"), alpha=0.04)
    c.circle(W * 0.6, H - 48 * mm, 18 * mm, fill=1, stroke=0)

    # Company name
    c.setFillColor(C_WHITE)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(lm, H - 18 * mm, company['name'].upper())

    # Tagline
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#ffffff"), alpha=0.6)
    c.drawString(lm, H - 24 * mm, "Official Tax Invoice")

    # Contact line
    c.setFont("Helvetica", 7.5)
    c.setFillColor(colors.HexColor("#ffffff"), alpha=0.55)
    c.drawString(lm, H - 30 * mm, f"{company['address']}   ·   {company['email']}   ·   {company['phone']}")

    # PAID stamp (rounded rect)
    stamp_x = W - 42 * mm
    stamp_y = H - 26 * mm
    c.setFillColor(colors.HexColor("#ffffff"), alpha=0.18)
    c.roundRect(stamp_x, stamp_y, 32 * mm, 10 * mm, 3 * mm, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#ffffff"), alpha=0.4)
    c.setLineWidth(1.2)
    c.roundRect(stamp_x, stamp_y, 32 * mm, 10 * mm, 3 * mm, fill=0, stroke=1)
    c.setFillColor(C_WHITE)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(stamp_x + 16 * mm, stamp_y + 3.2 * mm, "✓  PAID")

    # Thin accent line below header
    c.setStrokeColor(C_INDIGO)
    c.setLineWidth(2)
    c.line(0, H - 52 * mm, W, H - 52 * mm)


def draw_footer(c: rl_canvas.Canvas, doc, order):
    W, H = A4
    lm = doc.leftMargin

    # Footer line
    c.setStrokeColor(C_BORDER)
    c.setLineWidth(0.5)
    c.line(lm, 18 * mm, W - lm, 18 * mm)

    c.setFont("Helvetica", 7.5)
    c.setFillColor(C_MUTED)
    c.drawString(lm, 13 * mm, "This is a computer-generated invoice. No signature required.")
    c.drawRightString(W - lm, 13 * mm, f"Bill: {order.bill_number}   ·   Date: {order.created_at.strftime('%d %b %Y')}")


class InvoiceDocTemplate(BaseDocTemplate):
    def __init__(self, buffer, company, order, **kwargs):
        super().__init__(buffer, **kwargs)
        self.company = company
        self.order = order
        frame = Frame(
            self.leftMargin, self.bottomMargin,
            self.width, self.height,
            id='normal'
        )
        template = PageTemplate(id='invoice', frames=frame,
                                onPage=self._on_page)
        self.addPageTemplates([template])

    def _on_page(self, canvas, doc):
        canvas.saveState()
        draw_header(canvas, doc, self.company, self.order)
        draw_footer(canvas, doc, self.order)
        canvas.restoreState()


def build_receipt_pdf(buffer, order):
    company = get_company_info()
    cur = company['currency']

    W_page, H_page = A4
    LM = 18 * mm
    RM = 18 * mm
    TM = 56 * mm   # below header band
    BM = 22 * mm

    doc = InvoiceDocTemplate(
        buffer, company, order,
        pagesize=A4,
        leftMargin=LM, rightMargin=RM,
        topMargin=TM, bottomMargin=BM,
    )

    W = W_page - LM - RM   # usable width ≈ 174mm
    elements = []

    # ══════════════════════════════════════════
    # META BAND  (Bill / Date / Payment / Total)
    # ══════════════════════════════════════════
    def meta_cell(lbl, val, val_color=C_DARK, mono=False):
        font = "Courier-Bold" if mono else "Helvetica-Bold"
        return [
            P(lbl, S("ml", size=6.5, color=C_MUTED, bold=False)),
            P(f'<font name="{font}" size="10" color="#{val_color.hexval()[2:]}">{val}</font>',
              S("mv", size=10)),
        ]

    indigo_hex = "4f46e5"
    green_hex  = "16a34a"

    meta_row = [[
        meta_cell("BILL NUMBER", order.bill_number, C_INDIGO, mono=True),
        meta_cell("DATE", order.created_at.strftime("%d %b %Y")),
        meta_cell("PAYMENT STATUS", order.payment_status, C_GREEN),
        meta_cell("GRAND TOTAL", f"{cur}{order.total_amount:.2f}", C_DARK),
    ]]

    meta_table = Table(meta_row, colWidths=[W / 4] * 4)
    meta_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_LIGHT),
        ("BOX",           (0, 0), (-1, -1), 0.5, C_BORDER),
        ("INNERGRID",     (0, 0), (-1, -1), 0.5, C_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 8))

    # ══════════════════════════════════════════
    # CUSTOMER  +  ADDRESS
    # ══════════════════════════════════════════
    lbl_s  = S("lbl", size=6.5, color=C_MUTED)
    val_s  = S("val", size=9, color=C_DARK)
    bold_s = S("vb",  size=9, color=C_DARK, bold=True)

    def info_section(title, rows):
        cells = [P(title, lbl_s)]
        for k, v in rows:
            cells.append(Table(
                [[P(k, S("ik", size=8, color=C_MUTED)), P(v, S("iv", size=8.5, color=C_DARK, bold=True))]],
                colWidths=[W * 0.18, W * 0.30]
            ))
        return cells

    cust_rows = [
        ("Name",  order.customer_name),
        ("Email", order.customer_email),
        ("Phone", order.customer_phonenumber),
    ]
    addr_rows = [
        ("Address", order.customer_address),
        ("City",    f"{order.city} — {order.pincode}"),
        ("State",   order.get_state_display()),
    ]

    info_table = Table(
        [[info_section("CUSTOMER", cust_rows), info_section("DELIVERY ADDRESS", addr_rows)]],
        colWidths=[W / 2, W / 2]
    )
    info_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_LIGHT),
        ("BOX",           (0, 0), (-1, -1), 0.5, C_BORDER),
        ("LINEAFTER",     (0, 0), (0, -1),  0.5, C_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10))

    # ══════════════════════════════════════════
    # ITEMS TABLE
    # ══════════════════════════════════════════
    elements.append(P("ORDER ITEMS", S("it", size=6.5, color=C_MUTED)))
    elements.append(Spacer(1, 4))

    col_w = [W * 0.34, W * 0.13, W * 0.07, W * 0.27, W * 0.19]

    th = S("th", size=7.5, color=C_WHITE, bold=True, align=1)
    th_l = S("thl", size=7.5, color=C_WHITE, bold=True)
    td_c = S("tdc", size=9, color=C_DARK, align=1)
    td_r = S("tdr", size=9, color=C_DARK, align=2, bold=True)
    td_s = S("tds", size=7.5, color=C_MUTED)

    rows = [[
        P("PRODUCT", th_l),
        P("UNIT PRICE", th),
        P("QTY", th),
        P("WARRANTY", th),
        P("TOTAL", th),
    ]]

    for i, item in enumerate(order.items.all()):
        if item.warranty_end:
            w_line1 = f"{item.warranty_months} months"
            w_line2 = f"Until {item.warranty_end.strftime('%d %b %Y')}"
            w_status = "Active" if item.is_under_warranty() else "Expired"
            w_color  = "16a34a" if item.is_under_warranty() else "b91c1c"
            warranty_cell = [
                P(w_line1, S("wl1", size=8, color=C_DARK, bold=True)),
                P(w_line2, S("wl2", size=7, color=C_MUTED)),
                P(f'<font color="#{w_color}"><b>{w_status}</b></font>', S("ws", size=7)),
            ]
        else:
            warranty_cell = [
                P(f"{item.warranty_months} months", S("wl1", size=8, color=C_DARK, bold=True)),
                P("Not started", S("wl2", size=7, color=C_MUTED)),
            ]

        rows.append([
            P(f"<b>{item.product.name}</b>", S("pn", size=9, color=C_DARK)),
            P(f"{cur}{item.price:.2f}", td_c),
            P(f"<b>×{item.quantity}</b>", S("qty", size=9, color=C_DARK, align=1, bold=True)),
            warranty_cell,
            P(f"<b>{cur}{item.total:.2f}</b>", td_r),
        ])

    # Grand total row
    rows.append([
        P("", td_c), P("", td_c), P("", td_c),
        P("<b>GRAND TOTAL</b>", S("gtl", size=9.5, color=C_WHITE, bold=True, align=2)),
        P(f"<b>{cur}{order.total_amount:.2f}</b>", S("gtv", size=11, color=C_WHITE, bold=True, align=2)),
    ])

    items_table = Table(rows, colWidths=col_w, repeatRows=1)
    n_body = len(rows) - 2  # data rows (excl header + total)

    items_table.setStyle(TableStyle([
        # Header
        ("BACKGROUND",    (0, 0), (-1, 0),  C_DARK),
        ("TOPPADDING",    (0, 0), (-1, 0),  9),
        ("BOTTOMPADDING", (0, 0), (-1, 0),  9),
        ("LEFTPADDING",   (0, 0), (0, 0),   10),
        ("RIGHTPADDING",  (-1, 0), (-1, 0), 10),

        # Alternating rows
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [C_WHITE, C_LIGHT]),
        ("TOPPADDING",    (0, 1), (-1, -2), 8),
        ("BOTTOMPADDING", (0, 1), (-1, -2), 8),
        ("LEFTPADDING",   (0, 1), (0, -1),  10),
        ("RIGHTPADDING",  (-1, 1), (-1, -1), 10),

        # Total row
        ("BACKGROUND",    (0, -1), (-1, -1), C_DARK),
        ("TOPPADDING",    (0, -1), (-1, -1), 11),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 11),

        # Borders
        ("LINEBELOW",     (0, 0), (-1, -2), 0.4, C_BORDER),
        ("BOX",           (0, 0), (-1, -1), 0.6, C_BORDER),

        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 12))

    # ══════════════════════════════════════════
    # TERMS  +  SIGNATURE
    # ══════════════════════════════════════════
    terms_text = (
        "<b>Terms & Conditions</b><br/>"
        "<font size='8' color='#9ca3af'>"
        "1. Warranty starts from invoice date.&nbsp;&nbsp;"
        "2. Original invoice required for warranty claims.&nbsp;&nbsp;"
        "3. Physical / liquid damage not covered."
        "</font>"
    )
    sig_text = (
        "<font size='8' color='#9ca3af'><b>Authorized Signatory</b></font><br/><br/><br/>"
        "<font size='8' color='#9ca3af'>________________________</font>"
    )

    bottom_table = Table(
        [[P(terms_text, S("tc", size=8.5)), P(sig_text, S("sc", size=8, align=2))]],
        colWidths=[W * 0.65, W * 0.35]
    )
    bottom_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), C_LIGHT),
        ("BOX",           (0, 0), (-1, -1), 0.5, C_BORDER),
        ("LINEAFTER",     (0, 0), (0, -1),  0.5, C_BORDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(KeepTogether(bottom_table))

    doc.build(elements)
