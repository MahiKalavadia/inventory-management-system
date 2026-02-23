from django.shortcuts import render, get_object_or_404, redirect
from .models import Supplier
from inventory.models import Product
from inventory.models import Product, Category
from .forms import SupplierForm
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import HttpResponse
import csv
from django.db.models.functions import TruncMonth
from django.db.models import Q, F, Sum,  FloatField, ExpressionWrapper, DecimalField, Count, Value, Avg, Max
import json
from orders.models import OrderItem
from purchases.models import PurchaseRequest
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from openpyxl import Workbook


def supplier_dashboard(request):
    suppliers = Supplier.objects.all()
    total_supplier = Supplier.objects.count()
    active_supplier = Supplier.objects.filter(is_active=True).count()
    inactive_supplier = Supplier.objects.filter(is_active=False).count()
    products = Product.objects.count()
    supply = list(Supplier.objects.annotate(
        top_suppliers=Sum(F('product__purchase_price') *
                          F('product__quantity'), output_field=FloatField())
    ).values(
        'name',
        'top_suppliers'
    ))

    supplier_names = [s['name'] for s in supply]
    top_supplier = [s['top_suppliers'] for s in supply]

    supplier_category_data = list(Supplier.objects.annotate(
        total_categories=Count('categories_supplies')
    ).values('name', 'total_categories'))

    names = [s['name'] for s in supplier_category_data]
    total_category = [s['total_categories'] for s in supplier_category_data]

    monthly_suppliers = Supplier.objects.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total=Count('id')
    ).order_by('month')

    months = []
    totals = []

    for entry in monthly_suppliers:
        months.append(entry['month'].strftime("%b %Y"))
        totals.append(entry['total'])

    supplied = (
        PurchaseRequest.objects
        .filter(status='Approved')
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('quantity'))
        .order_by('month')
    )

    # 🛒 USED (Only Paid Orders)
    used = (
        OrderItem.objects
        .filter(order__status='Paid')
        .annotate(month=TruncMonth('order__created_at'))
        .values('month')
        .annotate(total=Sum('quantity'))
        .order_by('month')
    )

    # Convert to dictionary for safe month matching
    supplied_dict = {d['month']: d['total'] for d in supplied}
    used_dict = {d['month']: d['total'] for d in used}

    all_months = sorted(set(supplied_dict.keys()) | set(used_dict.keys()))

    months = [m.strftime("%b %Y") for m in all_months]
    supplied_totals = [supplied_dict.get(m, 0) for m in all_months]
    used_totals = [used_dict.get(m, 0) for m in all_months]

    search = request.GET.get('q')
    if search:
        suppliers = suppliers.filter(
            Q(name__icontains=search)
        )

    paginator = Paginator(suppliers, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'suppliers': suppliers,
        'total_supplier': total_supplier,
        'active_supplier': active_supplier,
        'inactive_supplier': inactive_supplier,
        'products': products,
        'page_obj': page_obj,
        'supplier_names': json.dumps(supplier_names),
        'top_supplier': json.dumps(top_supplier),
        'supplier_status': [active_supplier, inactive_supplier],
        'names': json.dumps(names),
        'total_category': json.dumps(total_category),
        'months': months,
        'totals': totals,
        'supplied_totals': json.dumps(supplied_totals),
        'used_totals': json.dumps(used_totals),
    }
    return render(request, "dashboards/supplier_dashboard.html", context)


def supplier_list(request):
    suppliers = Supplier.objects.all()

    supplier_data = []

    for supplier in suppliers:
        products = Product.objects.filter(supplier=supplier)

        categories = set([p.category.name for p in products if p.category])
        brands = set([p.brand for p in products if p.brand])

        supplier_data.append({
            'supplier': supplier,
            'categories': ", ".join(categories) if categories else "—",
            'brands': ", ".join(brands) if brands else "—",
            'total_products': products.count()
        })

    paginator = Paginator(supplier_data, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/supplier_list.html', {
        'page_obj': page_obj,
    })


def active_supplier(request):
    active_supplier = Supplier.objects.filter(is_active=True).all()

    paginator = Paginator(active_supplier, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "inventory/active_supplier.html", {'page_obj': page_obj})


def inactive_supplier(request):
    inactive_supplier = Supplier.objects.filter(is_active=False).all()

    paginator = Paginator(inactive_supplier, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "inventory/inactive_supplier.html", {'page_obj': page_obj})


def toggle_supplier_status(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    supplier.is_active = not supplier.is_active
    supplier.save()

    if supplier.is_active:
        messages.success(request, f"{supplier.name} activated.")
    else:
        messages.warning(request, f"{supplier.name} deactivated.")

    return redirect('supplier_dashboard')


def add_supplier(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('supplier_list')
    else:
        form = SupplierForm()

    return render(request, 'inventory/add_supplier.html', {'form': form})


def update_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, request.FILES, instance=supplier)
        if form.is_valid():
            form.save()
            return redirect('supplier_dashboard')
    else:
        form = SupplierForm(instance=supplier)

    return render(request, 'inventory/update_supplier.html', {'form': form})


def delete_supplier(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)

    if request.method == 'POST':
        supplier.delete()
        return redirect('supplier_dashboard')

    return render(request, 'inventory/delete_supplier.html', {
        'category': supplier
    })


def suppliers_by_value(request):
    top_suppliers = Supplier.objects.annotate(
        value=Sum(F('product__purchase_price') *
                  F('product__quantity'), output_field=FloatField())
    ).order_by('-value')

    paginator = Paginator(top_suppliers, 15)
    suppliers = request.GET.get('page_s')
    supply = paginator.get_page(suppliers)

    context = {
        'supply': supply,
    }

    return render(request, 'inventory/suppliers_by_value.html', context)


def export_supplier_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="supplies.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Name", "Contact Person", "Phone", "Email", "Address", "Categories Supplies"
    ])

    for supplier in Supplier.objects.prefetch_related("categories_supplies"):
        categories = ", ".join(
            cat.name for cat in supplier.categories_supplies.all())
        writer.writerow([
            supplier.name, supplier.contact_person, supplier.phone, supplier.email, supplier.address, categories
        ])

    return response


def export_supplier_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Suppliers"

    ws.append(["Name", "Contact Person", "Phone",
              "Email", "Address", "Categories Supplies"])

    for supplier in Supplier.objects.prefetch_related("categories_supplies"):
        categories = ", ".join(
            cat.name for cat in supplier.categories_supplies.all())
        ws.append([
            supplier.name, supplier.contact_person, supplier.phone, supplier.email, supplier.address, categories
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="suppliers.xlsx"'

    wb.save(response)
    return response


def export_supplier_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="suppliers.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(A4))  # landscape mode
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("SUPPLIER LIST", styles["Heading1"]))
    elements.append(Spacer(1, 10))

    # Table Header
    data = [["Name", "Contact Person", "Phone",
             "Email", "Address", "Categories Supplies"]]

    for supplier in Supplier.objects.prefetch_related("categories_supplies"):
        categories = ", ".join(
            cat.name for cat in supplier.categories_supplies.all())
        data.append([
            supplier.name, supplier.contact_person, supplier.phone, supplier.email, supplier.address, categories
        ])

    # Column widths for landscape
    col_widths = [150, 100, 120, 80, 200, 180]

    table = Table(data, colWidths=col_widths, repeatRows=1)

    table.setStyle(TableStyle([

        # Header Style
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2F3E46")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),

        # Body Style
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),

        # Row alternating light grey
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F7F9FB")]),

        # Align price column right
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),

        # Subtle grid
        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#B0BEC5")),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.HexColor("#E0E0E0")),

        # Padding
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),

    ]))

    elements.append(table)
    doc.build(elements)
    return response
