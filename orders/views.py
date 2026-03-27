from django.shortcuts import render, redirect, get_object_or_404
from .forms import OrderForm, OrderItemForm
from .models import Order, OrderItem
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse
from .utils.pdf import build_receipt_pdf
from .utils.email import send_receipt_email
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Q
from django.db import transaction
from django.forms import inlineformset_factory
from django.utils import timezone
from datetime import date
from django.core.paginator import Paginator
from django.contrib.admin.views.decorators import staff_member_required
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from openpyxl import Workbook
import csv
import json
from datetime import timedelta
from django.db.models.functions import TruncDate
# Create your views here.


def staff_or_manager(user):
    return user.is_superuser or user.groups.filter(name__in=['Manager', 'Staff']).exists()


def manager_only(user):
    return user.is_superuser or user.groups.filter(name='Manager').exists()


def admin_only(user):
    return user.is_superuser


def order_dashboard(request):

    today = timezone.now().date()
    current_month = today.month
    current_year = today.year

    # ---- Order Counts ----
    total_orders = Order.objects.count()
    draft_orders = Order.objects.filter(status='Draft').count()
    confirmed_orders = Order.objects.filter(status='Confirmed').count()
    cancelled_orders = Order.objects.filter(status='Cancelled').count()

    # ---- SALES CALCULATIONS ----
    total_sales = (
        OrderItem.objects
        .filter(order__payment_status='Paid')
        .aggregate(total=Sum(
            ExpressionWrapper(
                F('quantity') * F('price'),
                output_field=DecimalField()
            )
        ))['total'] or 0
    )

    # Today's Sales
    today_sales = (
        OrderItem.objects
        .filter(order__payment_status='Paid', order__created_at__date=today)
        .aggregate(total=Sum(
            ExpressionWrapper(
                F('quantity') * F('price'),
                output_field=DecimalField()
            )
        ))['total'] or 0
    )

    # Monthly Sales
    monthly_sales = (
        OrderItem.objects
        .filter(
            order__payment_status='Paid',
            order__created_at__year=current_year,
            order__created_at__month=current_month
        )
        .aggregate(total=Sum(
            ExpressionWrapper(
                F('quantity') * F('price'),
                output_field=DecimalField()
            )
        ))['total'] or 0
    )

    # Pending Payment Amount
    pending_amount = (
        OrderItem.objects
        .filter(order__payment_status='Pending')
        .aggregate(total=Sum(
            ExpressionWrapper(
                F('quantity') * F('price'),
                output_field=DecimalField()
            )
        ))['total'] or 0
    )

    # Total Products Sold
    total_products_sold = (
        OrderItem.objects
        .filter(order__payment_status='Paid')
        .aggregate(total=Sum('quantity'))['total'] or 0
    )

    # Top Selling Product
    top_product = (
        OrderItem.objects
        .filter(order__payment_status='Paid')
        .values('product__name')
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')
        .first()
    )

    top_products = (
        OrderItem.objects
        .filter(order__payment_status='Paid')
        .values('product__name', 'product__supplier__name')
        .annotate(total_sold=Sum('quantity'))
        .order_by('-total_sold')[:5]
    )

    recent_orders = Order.objects.order_by('-created_at')[:5]
    attention_orders = Order.objects.filter(
        payment_status="Pending"
    )[:5]
    pending_payments = Order.objects.filter(payment_status='Pending')[:5]

    payment_paid = Order.objects.filter(payment_status='Paid').count()
    payment_cancel = Order.objects.filter(payment_status='Pending').count()
    payment_fail = Order.objects.filter(payment_status='Failed').count()

    # revenue chart
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)

    revenue = OrderItem.objects.filter(
        order__created_at__date__gte=last_30_days, order__payment_status='Paid').annotate(date=TruncDate('order__created_at'), item_total=ExpressionWrapper(
            F('price') * F('quantity'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )).values('date').annotate(total=Sum('item_total')).order_by('date')

    dates = []
    totals = []

    for item in revenue:
        dates.append(item['date'].strftime("%d %b"))
        totals.append(float(item['total']))

    context = {
        'total_orders': total_orders,
        'draft_orders': draft_orders,
        'confirmed_orders': confirmed_orders,
        'cancelled_orders': cancelled_orders,
        'total_sales': total_sales,
        'today_sales': today_sales,
        'monthly_sales': monthly_sales,
        'pending_amount': pending_amount,
        'total_products_sold': total_products_sold,
        'top_product': top_product,
        'recent_orders': recent_orders,
        'attention_orders': attention_orders,
        'pending_payments': pending_payments,
        'top_products': top_products,
        'payment_paid': payment_paid,
        'payment_cancel': payment_cancel,
        'payment_fail': payment_fail,
        'dates': json.dumps(dates),
        'totals': json.dumps(totals),
    }

    return render(request, "dashboards/order_dashboard.html", context)


def order_list(request):
    orders = Order.objects.all().order_by('-created_at')
    total_orders = Order.objects.all().count()
    total_sales = (
        OrderItem.objects
        .filter(order__payment_status='Paid')
        .aggregate(total=Sum(
            ExpressionWrapper(
                F('quantity') * F('price'),
                output_field=DecimalField()
            )
        ))['total'] or 0
    )
    pending_amount = (
        OrderItem.objects
        .filter(order__payment_status='Pending')
        .aggregate(total=Sum(
            ExpressionWrapper(
                F('quantity') * F('price'),
                output_field=DecimalField()
            )
        ))['total'] or 0
    )

    search = request.GET.get("search")
    if search:
        orders = orders.filter(
            Q(customer_name__icontains=search) |
            Q(bill_number__icontains=search) |
            Q(customer_phonenumber__icontains=search)
        )

    # 🎯 Filters
    status = request.GET.get("status")
    if status:
        orders = orders.filter(status=status)

    payment = request.GET.get("payment")
    if payment:
        orders = orders.filter(payment_status=payment)

    paginator = Paginator(orders, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'total_orders': total_orders,
        'total_sales': total_sales,
        'pending_amount': pending_amount,
        'search': search,
    }

    return render(request, 'inventory/order_list.html', context)


def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'inventory/order_detail.html', {'order': order})


def order_receipt(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if order.payment_status != "Paid":
        return HttpResponseForbidden("Receipt available only for paid orders")

    return render(request, 'inventory/receipt.html', {'order': order})


def create_order(request):
    if not staff_or_manager(request.user):
        return HttpResponseForbidden("Not allowed")

    # Create formset with an empty Order instance
    OrderItemFormSet = inlineformset_factory(
        Order, OrderItem, form=OrderItemForm, extra=1, can_delete=False
    )

    # Use a new unsaved Order instance for the formset
    temp_order = Order()

    if request.method == "POST":
        order_form = OrderForm(request.POST)
        formset = OrderItemFormSet(request.POST, instance=temp_order)

        if order_form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    order = order_form.save(commit=False)
                    order.created_by = request.user
                    order.save()

                    # Save all items with the actual order
                    for form in formset:
                        item = form.save(commit=False)
                        item.order = order

                        if item.product.quantity < item.quantity:
                            raise ValueError(
                                f"Not enough stock for {item.product.name}")

                        item.product.quantity -= item.quantity
                        item.product.save()

                        item.price = item.product.price
                        item.save()

            except Exception as e:
                raise e

        messages.success(request, "Order created successfully!")
        try:
            send_receipt_email(order)
        except Exception as e:
            print("EMAIL ERROR:", e)
        return redirect('order_list')

    else:
        order_form = OrderForm()
        formset = OrderItemFormSet(instance=temp_order)  # Important!

    context = {
        'order_form': order_form,
        'formset': formset
    }
    return render(request, 'inventory/create_order.html', context)


def update_order(request, pk):
    if not manager_only(request.user):
        return HttpResponseForbidden("Only managers can edit orders")

    order = get_object_or_404(Order, pk=pk)
    item = order.items.first()
    if request.method == "POST":
        order_form = OrderForm(request.POST, instance=order)
        item_form = OrderItemForm(request.POST, instance=item)

        if order_form.is_valid() and item_form.is_valid():
            order_form.save()

            # Update stock correctly
            old_quantity = item.quantity
            updated_item = item_form.save(commit=False)
            diff = updated_item.quantity - old_quantity

            # Check stock
            if updated_item.product.quantity < diff:
                messages.error(
                    request, f"Not enough stock for {updated_item.product.name}")
                return redirect('update_order', pk=order.id)

            # Update stock
            updated_item.product.quantity -= diff
            updated_item.product.save()

            updated_item.save()
            messages.success(request, "Order updated successfully!")
            return redirect('order_detail', pk=order.id)

    else:
        order_form = OrderForm(instance=order)
        item_form = OrderItemForm(instance=item)

    return render(request, 'inventory/update_order.html', {
        'order_form': order_form,
        'item_form': item_form,
        'order': order
    })


def delete_order(request, pk):
    if not admin_only(request.user):
        return HttpResponseForbidden("Only admin can delete orders")
    order = get_object_or_404(Order, pk=pk)

    if request.method == "POST":
        # Restore stock
        for item in order.items.all():
            item.product.quantity += item.quantity
            item.product.save()

        order.delete()
        messages.success(request, "Order deleted successfully.")
        return redirect('order_list')
    return render(request, 'inventory/delete_order.html', {'order': order})


def confirm_order(request, pk):
    if not manager_only(request.user):
        return HttpResponseForbidden("Only managers can confirm orders")

    order = get_object_or_404(Order, pk=pk)
    order.status = "Confirmed"
    order.save()
    return redirect('order_detail', pk=pk)


def mark_paid(request, pk):
    if not manager_only(request.user):
        return HttpResponseForbidden("Only managers can mark payment")

    order = get_object_or_404(Order, pk=pk)
    order.payment_status = "Paid"
    order.status = "Paid"
    order.save()
    return redirect('order_detail', pk=pk)


def download_receipt(request, pk):
    # Get order
    order = Order.objects.get(id=pk)

    # receipt available only after payment is completed
    if order.payment_status != "Paid":
        return HttpResponseForbidden("Receipt available only after payment.")

    # Create HTTP response with PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{order.id}.pdf"'

    # Call your PDF function
    build_receipt_pdf(response, order)

    return response


def warranty_check(request):
    order_id = request.GET.get("order_id")
    items = None

    if order_id:
        items = OrderItem.objects.filter(order__id=order_id)

    return render(
        request,
        "inventory/warranty_check.html",
        {"items": items}
    )


def order_attention(request):
    attention_orders = Order.objects.filter(
        payment_status="Pending"
    )

    paginator = Paginator(attention_orders, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'inventory/order_attention.html', context)


def pending_payments(request):

    pending_payments = Order.objects.filter(payment_status='Pending')

    paginator = Paginator(pending_payments, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }

    return render(request, 'inventory/pending_payments.html', context)


@staff_member_required
def export_orders_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="orders.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Bill No", "Customer", "Email", "Phone",
        "City", "State", "Status", "Payment Status",
        "Total Amount", "Created At"
    ])

    for order in Order.objects.prefetch_related("items"):
        writer.writerow([
            order.bill_number,
            order.customer_name,
            order.customer_email,
            order.customer_phonenumber,
            order.city,
            order.get_state_display(),
            order.status,
            order.payment_status,
            order.total_amount,
            order.created_at.strftime("%Y-%m-%d %H:%M"),
        ])

    return response


@staff_member_required
def export_orders_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Orders"

    ws.append([
        "Bill No", "Customer", "Email", "Phone",
        "City", "State", "Status", "Payment Status",
        "Total Amount", "Created At"
    ])

    for order in Order.objects.prefetch_related("items"):
        ws.append([
            order.bill_number,
            order.customer_name,
            order.customer_email,
            order.customer_phonenumber,
            order.city,
            order.get_state_display(),
            order.status,
            order.payment_status,
            float(order.total_amount),
            order.created_at.strftime("%Y-%m-%d %H:%M"),
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="orders.xlsx"'
    wb.save(response)
    return response


@staff_member_required
def export_orders_pdf(request):
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="orders.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph("Order History Report", styles["Heading1"])
    elements.append(title)
    elements.append(Spacer(1, 12))

    orders = Order.objects.prefetch_related("items", "items__product")

    for order in orders:
        # Order Header
        elements.append(Paragraph(
            f"<b>Bill:</b> {order.bill_number} | <b>Customer:</b> {order.customer_name} | <b>Total:</b> ₹{order.total_amount}",
            styles["Normal"]
        ))
        elements.append(Spacer(1, 6))

        # Table Header
        data = [["Product", "Qty", "Price", "Total"]]

        for item in order.items.all():
            data.append([
                item.product.name if item.product else "Deleted Product",
                item.quantity,
                item.price,
                item.total,
            ])
        colWidths = [200, 60, 80, 80]
        # Create Table
        table = Table(data, colWidths=[200, 60, 80, 80])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 15))

    doc.build(elements)
    return response

    # c = canvas.Canvas("test.pdf")
    # c.drawString(100,750 , "Hello ReportLab")
    # c.save()

    # c = canvas.Canvas("test.pdf", pagesize = A4)
    # width , height = A4

    # c.setFont("", 22)
    # c.drawCenteredString(width/2, height-100, "Hello"). ( here eidth/2 meansa aligned horizontally and height-100 means 100 point below starting point)
