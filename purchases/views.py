from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from .models import PurchaseRequest, PurchaseOrder
from .forms import PurchaseRequestForm, PurchaseOrderForm
from notifications.models import Notification
from django.contrib.auth.models import User
from django.db.models import Sum, Count, ExpressionWrapper, F, DecimalField
from inventory.models import Product, StockLog, Category
from suppliers.models import Supplier
from django.contrib import messages
from inventory.config import get_low_stock_threshold
from django.core.paginator import Paginator
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.timezone import now
from django.http import HttpResponse
import csv
import json
from openpyxl import Workbook
from reportlab.pdfgen import canvas
from django.db import transaction
from datetime import timedelta
from django.db.models.functions import TruncMonth


def is_manager_or_staff(user):
    return user.groups.filter(name__in=["Manager", "Staff"]).exists()


@login_required
def purchase_dashboard(request):
    low_products = Product.objects.filter(
        quantity__lte=get_low_stock_threshold())
    total_requests = PurchaseRequest.objects.count()
    pending_requests = PurchaseRequest.objects.filter(status='Pending').count()
    approved_requests = PurchaseRequest.objects.filter(
        status='Approved').count()
    rejected_requests = PurchaseRequest.objects.filter(
        status='Rejected').count()

    total_orders = PurchaseOrder.objects.count()
    in_transit = PurchaseOrder.objects.filter(status='in_transit').count()
    delivered = PurchaseOrder.objects.filter(status='delivered').count()

    total_purchase_cost = PurchaseOrder.objects.aggregate(
        Sum('total_cost'))['total_cost__sum'] or 0
    requests = PurchaseRequest.objects.all().order_by("-created_at")

    orders = PurchaseOrder.objects.all().order_by("-created_at")

    paginator = Paginator(requests, 5)
    page_number = request.GET.get('page')
    reque = paginator.get_page(page_number)

    paginator = Paginator(low_products, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    paginator = Paginator(orders, 5)
    page_number = request.GET.get('page')
    urder = paginator.get_page(page_number)

    # charts
    # monthly purchase amount
    monthly_purchases = StockLog.objects.filter(action='IN').annotate(
        month=TruncMonth('created_at'),
        purchase_total=ExpressionWrapper(
            F('quantity') * F('product__purchase_price'),
            output_field=DecimalField(decimal_places=2, max_digits=12)
        )
    ).values('month').annotate(total=Sum('purchase_total')).order_by('month')

    months = []
    monthly_totals = []

    for item in monthly_purchases:
        months.append(item['month'].strftime("%b %Y"))
        monthly_totals.append(float(item['total'] or 0))

    category_purchases = StockLog.objects.filter(action='IN').annotate(
        purchase_total=ExpressionWrapper(
            F('quantity') * F('product__purchase_price'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
    ).values('product__category__name').annotate(total=Sum('purchase_total')).order_by('-total')

    category_labels = []
    category_data = []

    for item in category_purchases:
        category_labels.append(item['product__category__name'])
        category_data.append(float(item['total'] or 0))

    top_products = PurchaseOrder.objects.filter(
        status='delivered'
    ).values(
        'request__product__name'
    ).annotate(
        total_qty=Sum('request__quantity')
    ).order_by('-total_qty')[:5]   # Top 5 products

    product_labels = []
    product_data = []

    for item in top_products:
        product_labels.append(item['request__product__name'])
        product_data.append(item['total_qty'] or 0)

    return render(request, 'dashboards/purchase_dashboard.html', {
        'low_products': low_products,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'rejected_requests': rejected_requests,
        'total_orders': total_orders,
        'in_transit': in_transit,
        'delivered': delivered,
        'total_purchase_cost': total_purchase_cost,
        'page_obj': page_obj,
        'reque': reque,
        'urder': urder,
        # charts
        'monthly_labels': json.dumps(months),
        'monthly_data': json.dumps(monthly_totals),
        'category_labels': json.dumps(category_labels),
        'category_data': json.dumps(category_data),
        'product_name': json.dumps(product_labels),
        'product_purchased': json.dumps(product_data),
    })


@login_required
@user_passes_test(is_manager_or_staff)
def purchase_dashboard_ms(request):
    user = request.user

    # 📉 Low / Out stock products
    low_stock_products = Product.objects.filter(
        quantity__lte=get_low_stock_threshold(),
        quantity__gt=0,
        is_active=True
    ).order_by('-created_at')

    out_of_stock_products = Product.objects.filter(
        quantity__lte=0,
        is_active=True
    ).order_by('-created_at')

    # 📄 Requests created by this user
    my_requests = PurchaseRequest.objects.filter(
        requested_by=user
    ).select_related("product", "supplier").order_by("-created_at")

    paginator = Paginator(low_stock_products, 5)
    low_page = request.GET.get("page_low")
    low = paginator.get_page(low_page)

    paginator = Paginator(out_of_stock_products, 5)
    out_page = request.GET.get("page_out")
    out = paginator.get_page(out_page)

    paginator = Paginator(my_requests, 5)
    req_page = request.GET.get("page_req")
    requests = paginator.get_page(req_page)

    # 📊 Stats cards
    context = {
        "low_stock_count": low_stock_products.count(),
        "out_stock_count": out_of_stock_products.count(),
        "pending_count": my_requests.filter(status="Pending").count(),
        "approved_count": my_requests.filter(status="Approved").count(),

        "low_stock_products": low_stock_products,
        "out_of_stock_products": out_of_stock_products,
        "my_requests": my_requests,

        'low': low,
        'out': out,
        'requests': requests,
    }

    return render(request, "dashboards/purchase_dashboard_ms.html", context)


@login_required
@user_passes_test(is_manager_or_staff)
def create_request(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Prevent duplicate pending requests
    if PurchaseRequest.objects.filter(
        product=product,
        requested_by=request.user,
        status="Pending"
    ).exists():
        messages.warning(request, "Request already pending for this product.")
        return redirect("purchase_dashboard2")

    if request.method == "POST":
        quantity = request.POST.get("quantity")
        description = request.POST.get("description")

        PurchaseRequest.objects.create(
            product=product,
            supplier=product.supplier,
            quantity=quantity,
            description=description,
            requested_by=request.user,
        )

        messages.success(request, "Purchase request sent to admin.")
        return redirect("purchase_dashboard2")

    return render(request, "inventory/create_request.html", {
        "product": product
    })


@login_required
def purchase_request(request):
    low_stock_products = Product.objects.filter(
        quantity__lte=get_low_stock_threshold(), quantity__gt=0).all()
    out_of_stock_products = Product.objects.filter(quantity=0).all()
    paginator = Paginator(low_stock_products, 10)
    low_page = request.GET.get("page_low")
    low = paginator.get_page(low_page)

    paginator = Paginator(out_of_stock_products, 10)
    out_page = request.GET.get("page_out")
    out = paginator.get_page(out_page)

    context = {
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'low': low,
        'out': out,
    }

    return render(request, 'inventory/request_purchase.html', context)
# ================= ADMIN MANAGE REQUESTS =================


@login_required
def manage_requests(request):
    requests = PurchaseRequest.objects.all().order_by("-created_at")

    paginator = Paginator(requests, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "inventory/manage_request.html", {"page_obj": page_obj})


@login_required
def approve_request(request, pk):
    # Get the purchase request
    req = get_object_or_404(PurchaseRequest, id=pk)

    if req.status != "Approved":
        # Approve the request
        req.status = "Approved"
        req.save()

        # Get or create the PurchaseOrder for this request
        po, created = PurchaseOrder.objects.get_or_create(
            request=req,
            defaults={
                'supplier': req.supplier,
                'total_cost': req.quantity * req.product.purchase_price,
                'status': 'draft',
            }
        )

        # Redirect to edit page
        return redirect('edit_purchase_order', pk=po.pk)

    # If already approved, just go back to manage requests
    return redirect("manage_requests")


@login_required
def reject_request(request, pk):
    req = get_object_or_404(PurchaseRequest, id=pk)

    if req.status != "Rejected":
        req.status = "Rejected"
        req.save()

    return redirect("manage_requests")


def edit_purchase_order(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)

    if po.status != 'draft':
        messages.success(
            request, "Filling details is only avaible for draft orders.")
        return redirect('purchase_order_detail', pk=po.pk)

    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=po)
        if form.is_valid():
            po = form.save(commit=False)

            # Check if user clicked "Place Order" button
            if 'place_order' in request.POST:
                po.status = 'ordered'

            po.save()

            # Redirect to detail page
            return redirect('purchase_order_detail', pk=po.pk)
    else:
        form = PurchaseOrderForm(instance=po)

    return render(request, 'inventory/edit_purchase_order.html', {'form': form, 'po': po})


@login_required
def purchase_order_detail(request, pk):
    order = get_object_or_404(
        PurchaseOrder.objects.select_related(
            "request",
            "request__product",
            "request__requested_by",
            "supplier"
        ),
        pk=pk
    )

    context = {
        "order": order,
    }
    return render(request, "inventory/purchase_order_detail.html", context)
# ================= PURCHASE ORDERS =================


@staff_member_required
def purchase_orders(request):
    order = PurchaseOrder.objects.all().order_by("-created_at")

    paginator = Paginator(order, 10)
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)

    return render(request, "inventory/purchase_orders.html", {"orders": orders})


@staff_member_required
def update_po_status(request, pk):
    po = get_object_or_404(PurchaseOrder, id=pk)

    if request.method == "POST":
        new_status = request.POST.get("status")

        if new_status and new_status != po.status:
            po.status = new_status
            po.save()  # signal handles stock + notifications

        return redirect("purchase_orders")

    return render(request, "inventory/update_po.html", {"po": po})


@staff_member_required
def all_purchase_records(request):
    requests = PurchaseRequest.objects.order_by('-created_at')[:10]
    orders = PurchaseOrder.objects.order_by('-created_at')[:10]

    context = {
        'requests': requests,
        'orders': orders,
    }
    return render(request, 'inventory/all_records.html', context)


@staff_member_required
def export_requests_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="purchase_requests.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "ID", "Product", "Quantity", "Supplier",
        "Status", "Requested By", "Created At"
    ])

    for r in PurchaseRequest.objects.select_related(
        "product", "supplier", "requested_by"
    ):
        writer.writerow([
            r.id,
            r.product.name,
            r.quantity,
            r.supplier.name,
            r.status,
            r.requested_by.username,
            r.created_at.strftime("%Y-%m-%d"),
        ])

    return response


@staff_member_required
def export_requests_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Purchase Requests"

    ws.append([
        "ID", "Product", "Quantity", "Supplier",
        "Status", "Requested By", "Created At"
    ])

    for r in PurchaseRequest.objects.select_related(
        "product", "supplier", "requested_by"
    ):
        ws.append([
            r.id,
            r.product.name,
            r.quantity,
            r.supplier.name,
            r.status,
            r.requested_by.username,
            r.created_at.strftime("%Y-%m-%d"),
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="purchase_requests.xlsx"'
    wb.save(response)
    return response


@staff_member_required
def export_requests_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="purchase_requests.pdf"'

    p = canvas.Canvas(response)
    y = 800

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Purchase Requests")
    y -= 30

    p.setFont("Helvetica", 10)

    for r in PurchaseRequest.objects.select_related("product", "supplier"):
        p.drawString(
            50,
            y,
            f"#{r.id} | {r.product.name} | Qty: {r.quantity} | {r.status}"
        )
        y -= 15

        if y < 50:
            p.showPage()
            p.setFont("Helvetica", 10)
            y = 800

    p.save()
    return response


@staff_member_required
def export_orders_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="purchase_orders.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "PO ID", "Product", "Quantity", "Supplier",
        "Status", "Total Cost", "Created At"
    ])

    for po in PurchaseOrder.objects.select_related(
        "request__product", "supplier"
    ):
        writer.writerow([
            po.id,
            po.request.product.name,
            po.request.quantity,
            po.supplier.name,
            po.status,
            po.total_cost,
            po.created_at.strftime("%Y-%m-%d"),
        ])

    return response


@staff_member_required
def export_orders_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Purchase Orders"

    ws.append([
        "PO ID", "Product", "Quantity", "Supplier",
        "Status", "Total Cost", "Created At"
    ])

    for po in PurchaseOrder.objects.select_related(
        "request__product", "supplier"
    ):
        ws.append([
            po.id,
            po.request.product.name,
            po.request.quantity,
            po.supplier.name,
            po.status,
            po.total_cost,
            po.created_at.strftime("%Y-%m-%d"),
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="purchase_orders.xlsx"'
    wb.save(response)
    return response


@staff_member_required
def export_orders_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="purchase_orders.pdf"'

    p = canvas.Canvas(response)
    y = 800

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Purchase Orders")
    y -= 30

    p.setFont("Helvetica", 10)

    for po in PurchaseOrder.objects.select_related(
        "request__product", "supplier"
    ):
        p.drawString(
            50,
            y,
            f"PO #{po.id} | {po.request.product.name} | "
            f"Qty: {po.request.quantity} | {po.status}"
        )
        y -= 15

        if y < 50:
            p.showPage()
            p.setFont("Helvetica", 10)
            y = 800

    p.save()
    return response
