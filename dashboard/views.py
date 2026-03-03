from django.shortcuts import render
from inventory.models import Product, Category, StockLog
from suppliers.models import Supplier
from accounts.decorators import role_required
from inventory.config import get_low_stock_threshold
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from notifications.models import Notification
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Count, FloatField, Q
from orders.models import OrderItem, Order
from purchases.models import PurchaseRequest, PurchaseOrder
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models.functions import TruncMonth, TruncDate
import json


def landing(request):
    return render(request, "landing.html")


def get_user_notifications(user, limit=5):

    if not user.is_authenticated:
        return Notification.objects.none()

    user_role = get_user_role(user)

    if not user_role:
        return Notification.objects.none()

    unread_notifications = Notification.objects.filter(
        is_read=False
    ).order_by('-created_at')

    filtered = [
        n for n in unread_notifications
        if user_role in n.allowed_roles
    ]

    return filtered[:limit]


def get_user_role(user):
    if not user.is_authenticated:
        return None

    if user.is_superuser:
        return "admin"

    group = user.groups.first()
    return group.name.lower() if group else None


@role_required("Admin")
def admin_dashboard(request):
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_suppliers = Supplier.objects.count()
    low_stock_products = Product.objects.filter(
        quantity__lte=get_low_stock_threshold(), quantity__gt=0, is_active=True)
    low_stock = low_stock_products.count()
    out_of_stock = Product.objects.filter(quantity__lte=0).count()
    in_stock = Product.objects.filter(
        quantity__gt=get_low_stock_threshold()).count()
    # total sales
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
    # 💸 Cost of Goods Sold (COGS)
    total_cogs = (
        OrderItem.objects
        .filter(order__payment_status='Paid')
        .aggregate(total=Sum(
            ExpressionWrapper(
                F('quantity') * F('product__purchase_price'),
                output_field=DecimalField()
            )
        ))['total'] or 0
    )
    # 1️⃣ Revenue Trend (Monthly Paid Orders)
    # -----------------------------
    last_six_months = timezone.now() - timedelta(days=180)
    revenue_data = (
        Order.objects
        .filter(status="Paid", created_at__gte=last_six_months)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('items__price'))
        .order_by('month')
    )

    revenue_labels = []
    revenue_values = []

    for item in revenue_data:
        month_name = item['month'].strftime('%b %Y')
        revenue_labels.append(month_name)
        revenue_values.append(float(item['total'] or 0))

    # -----------------------------
    # 2️⃣ Purchase Order Status
    # -----------------------------
    po_status_data = (
        PurchaseOrder.objects
        .values('status')
        .annotate(count=Count('id'))
    )

    po_labels = [item['status'] for item in po_status_data]
    po_values = [item['count'] for item in po_status_data]

    # -----------------------------
    # 3️⃣ Payment Status (Orders)
    # -----------------------------
    payment_status_data = (
        Order.objects
        .values('payment_status')
        .annotate(count=Count('id'))
    )

    payment_labels = [item['payment_status'] for item in payment_status_data]
    payment_values = [item['count'] for item in payment_status_data]

    color_map = {
        'Paid': '#16a34a',    # green
        'Failed': '#dc2626',  # red
        'Pending': '#f97316',  # orange
    }

    payment_colors = [color_map.get(status, '#888')
                      for status in payment_labels]

    # -----------------------------
    # 4️⃣ Inventory Supplied vs Sold
    # -----------------------------

    supplied = (
        PurchaseRequest.objects
        .filter(status="Approved")
        .aggregate(total=Sum('quantity'))['total'] or 0
    )

    sold = (
        OrderItem.objects
        .filter(order__status="Paid")
        .aggregate(total=Sum('quantity'))['total'] or 0
    )
    # 📈 Gross Margin
    gross_margin = total_sales - total_cogs
    recent_stock_logs = StockLog.objects.select_related(
        'product').order_by('-created_at')[:5]
    # login status
    recent_logins = User.objects.order_by('-last_login')[:4]
    users = User.objects.all()
    # for admin low_stock table and out of stock table
    l_stock = Product.objects.filter(
        quantity__lte=get_low_stock_threshold(), quantity__gt=0, is_active=True).select_related('supplier').order_by('quantity')[:3]
    o_stock = Product.objects.filter(quantity=0).order_by('quantity')[:3]
    # Progress bar indicator to show percentage distribution of stocks
    low_stock_bar = Product.objects.filter(
        quantity__lte=get_low_stock_threshold(), quantity__gt=0, is_active=True).count()
    in_stock_bar = Product.objects.filter(
        quantity__gt=get_low_stock_threshold(), is_active=True).count()
    out_stock_bar = Product.objects.filter(
        quantity__lte=0, is_active=True).count()
    notifications = get_user_notifications(request.user, 5)
    notifications_count = len(notifications)

    # recent activities
    recent_products = Product.objects.order_by('-created_at')[:3]
    recent_stock_log = StockLog.objects.select_related(
        'product').order_by('-created_at')[:3]
    recent_categories = Category.objects.order_by('-id')[:2]
    recent_suppliers = Supplier.objects.order_by('-id')[:2]
    requests = PurchaseRequest.objects.order_by('-created_at')[:3]
    orders = PurchaseOrder.objects.order_by('-created_at')[:3]

    top_suppliers = Supplier.objects.annotate(
        value=Sum(F('product__purchase_price') *
                  F('product__quantity'), output_field=FloatField())
    ).order_by('-value')[:3]

    top_value_products = Product.objects.annotate(
        value=ExpressionWrapper(
            F('purchase_price') * F('quantity'),
            output_field=FloatField()
        )
    ).order_by('-value')[:3]

    activities = []

    for p in recent_products:
        activities.append({
            'type': 'product',
            'message': f'Product added: {p.name}',
            'time': p.created_at
        })

    for s in recent_stock_log:
        activities.append({
            'type': 'stock',
            'message': f'Stock {s.action} - {s.product.name} ({s.quantity})',
            'time': s.created_at
        })

    for c in recent_categories:
        activities.append({
            'type': 'category',
            'message': f'Category added: {c.name}',
            'time': timezone.now() - timedelta(seconds=c.id)
        })

    for sup in recent_suppliers:
        activities.append({
            'type': 'supplier',
            'message': f'Supplier added: {sup.name}',
            'time': timezone.now() - timedelta(seconds=sup.id)
        })

    activities = sorted(
        activities,
        key=lambda x: x['time'],
        reverse=True
    )[:6]

    def percent(count):
        return round((count / total_products) * 100, 1) if total_products else 0

    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_suppliers': total_suppliers,
        'low_stock_products': low_stock_products,
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
        'in_stock': in_stock,
        'recent_stock_logs': recent_stock_logs,
        'total_sales': total_sales,
        'total_cogs': total_cogs,
        'gross_margin': gross_margin,
        # for admin
        'l_stock': l_stock,
        'o_stock': o_stock,
        # login status
        'recent_logins': recent_logins,
        'users': users,
        # progress bar
        'low_stock_bar': percent(low_stock_bar),
        'in_stock_bar': percent(in_stock_bar),
        'out_stock_bar': percent(out_stock_bar),
        'notifications': notifications,
        'notifications_count': notifications_count,
        # recent activity
        'recent_activity': activities,
        'requests': requests,
        'orders': orders,
        # quick actions
        "unread_notifications_count": notifications_count,
        'top_value_products': top_value_products,
        'top_suppliers': top_suppliers,
        "pending_requests_count": PurchaseRequest.objects.filter(
            status="Pending"
        ).count(),

        # Active = anything not delivered
        "active_po_count": PurchaseOrder.objects.exclude(
            status="delivered"
        ).count(),
        "revenue_labels": revenue_labels,
        "revenue_values": revenue_values,

        "po_labels": po_labels,
        "po_values": po_values,

        "payment_labels": payment_labels,
        "payment_values": payment_values,
        "payment_colors": payment_colors,

        "supplied": supplied,
        "sold": sold,
    }

    return render(request, "admin_dashboard.html", context)


@role_required("Manager")
def manager_dashboard(request):
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_suppliers = Supplier.objects.count()
    in_stock = Product.objects.filter(
        quantity__gt=get_low_stock_threshold(), is_active=True).count()
    low_stock = Product.objects.filter(
        quantity__lte=get_low_stock_threshold(), quantity__gt=0, is_active=True).count()
    out_stock = Product.objects.filter(quantity=0, is_active=True).count()

    l_stock = Product.objects.filter(
        quantity__lte=get_low_stock_threshold(),
        quantity__gt=0
    ).select_related('supplier').order_by('quantity')[:5]

    o_stock = Product.objects.filter(quantity=0).order_by('name')[:5]

    # Recent stock activity
    recent_stock_logs = StockLog.objects.select_related(
        'product').order_by('-created_at')[:5]

    notifications = get_user_notifications(request.user, 5)
    notifications_count = len(notifications)

    # chart 1
    last_six_months = timezone.now() - timedelta(days=180)
    orders_per_month = (Order.objects.filter(created_at__gte=last_six_months).annotate(month=TruncMonth('created_at')).values(
        'month').annotate(total=Count('id')).order_by('month'))

    months = []
    monthly_ordertotals = []

    for item in orders_per_month:
        months.append(item['month'].strftime("%b %Y"))
        monthly_ordertotals.append(item['total'] or 0)

    # chart 2 category wise inventory category --> product --> price * quantity
    category_wise_inventory = (Category.objects.
                               annotate(
                                   total_inventory=ExpressionWrapper(
                                       Sum(F('product__price') * F('product__quantity')), output_field=DecimalField(max_digits=12, decimal_places=2)))
                               .values('name', 'total_inventory').order_by('-total_inventory'))[:5]

    category_names = []
    category_value = []

    for item in category_wise_inventory:
        category_names.append(item['name'])
        category_value.append(float(item['total_inventory'] or 0))

    # chart 3 top 5 low stock product product model used
    top_low_stock = (Product.objects.filter(
        quantity__lte=get_low_stock_threshold(), quantity__gt=0).order_by('quantity'))[:5]

    low_stock_name = []
    low_stock_quantity = []

    for item in top_low_stock:
        low_stock_name.append(item.name)
        low_stock_quantity.append(item.quantity)

    # monthly summary
    today = timezone.now()
    start_month = today.replace(day=1)

    monthly_stockin = PurchaseOrder.objects.filter(
        status='delivered', request__created_at__gte=start_month).aggregate(total=Sum('request__quantity'))["total"] or 0

    monthly_stockout = OrderItem.objects.filter(
        order__payment_status="Paid", order__created_at__gte=start_month).aggregate(total=Sum('quantity'))["total"] or 0

    # Inventory health %
    total_products = total_products if total_products else 1

    def percent(value):
        return round((value / total_products) * 100, 1)

    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_suppliers': total_suppliers,
        'in_stock': in_stock,
        'low_stock': low_stock,
        'out_stock': out_stock,
        'l_stock': l_stock,
        'o_stock': o_stock,
        'recent_stock_logs': recent_stock_logs,
        'in_stock_bar': percent(in_stock),
        'low_stock_bar': percent(low_stock),
        'out_stock_bar': percent(out_stock),
        'notifications': notifications,
        'notifications_count': notifications_count,
        "monthly_stockin": monthly_stockin,
        "monthly_stockout": monthly_stockout,
        'month_labels': json.dumps(months),
        'monthly_ordertotal': json.dumps(monthly_ordertotals),
        'category_names': json.dumps(category_names),
        'category_value': json.dumps(category_value),
        'low_stock_name': json.dumps(low_stock_name),
        'low_stock_quantity': json.dumps(low_stock_quantity),

    }
    return render(request, "manager_dashboard.html", context)


@role_required("Staff")
def staff_dashboard(request):
    total_products = Product.objects.count()
    in_stock = Product.objects.filter(
        quantity__gt=get_low_stock_threshold(), is_active=True).count()
    low_stock = Product.objects.filter(
        quantity__lte=get_low_stock_threshold(), quantity__gt=0, is_active=True).count()
    out_stock = Product.objects.filter(quantity=0, is_active=True).count()
    low_stock_products = Product.objects.filter(
        quantity__lte=get_low_stock_threshold(),
        quantity__gt=0,
        is_active=True
    ).select_related('supplier')[:5]
    recent_stock_logs = StockLog.objects.select_related(
        'product'
    ).order_by('-created_at')[:5]

    notifications = get_user_notifications(request.user, 5)
    notifications_count = len(notifications)

    # chart1 staff approve reject pie chart
    user = request.user
    purchase_request_approve = PurchaseRequest.objects.filter(
        requested_by=user, status='Approved').count()
    purchase_request_reject = PurchaseRequest.objects.filter(
        requested_by=user, status='Rejected').count()
    purchase_request_pending = PurchaseRequest.objects.filter(
        requested_by=user, status='Pending').count()

    # chart 2 purchase order status doughnut chart
    ordered_status = PurchaseOrder.objects.filter(status='ordered').count()
    shipped_status = PurchaseOrder.objects.filter(status='shipped').count()
    intransit_status = PurchaseOrder.objects.filter(
        status='in_transit').count()
    delivered_status = PurchaseOrder.objects.filter(status='delivered').count()
    delayed_status = PurchaseOrder.objects.filter(status='delayed').count()

    # chart3 low stock alerts horizontal bar
    low_stock_alert = Product.objects.filter(
        quantity__lte=get_low_stock_threshold(), quantity__gt=0).order_by('quantity')[:5]

    low_stock_label = []
    low_stock_data = []

    for item in low_stock_alert:
        low_stock_label.append(item.name)
        low_stock_data.append(item.quantity)

    # chart4 inventory movement last 7 days
    last_7_days = timezone.now() - timedelta(days=7)

    movement = (
        StockLog.objects
        .filter(created_at__gte=last_7_days)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(
            stock_in=Sum('quantity', filter=Q(action='STOCK_IN')),
            stock_out=Sum('quantity', filter=Q(action='STOCK_OUT')),
        )
        .order_by('day')
    )

    dates = []
    stock_in_data = []
    stock_out_data = []

    for item in movement:
        dates.append(item['day'].strftime("%d %b"))
        stock_in_data.append(item['stock_in'] or 0)
        stock_out_data.append(item['stock_out'] or 0)

    context = {
        'total_products': total_products,
        'in_stock': in_stock,
        'low_stock': low_stock,
        'out_stock': out_stock,
        'low_stock_products': low_stock_products,
        'recent_stock_logs': recent_stock_logs,
        'notifications': notifications,
        'notifications_count': notifications_count,
        # purchase request chart
        'purchase_request_approve': purchase_request_approve,
        'purchase_request_reject': purchase_request_reject,
        'purchase_request_pending': purchase_request_pending,
        'purchase_labels': json.dumps(['Approved', 'Pending', 'Rejected']),
        'purchase_count': json.dumps([purchase_request_approve, purchase_request_pending, purchase_request_reject]),
        # purchase order chart
        'purchase_order_labels': json.dumps(['Ordered', 'Shipped', 'In Transit', 'Delivered', 'Delayed']),
        'purchase_order_counts': json.dumps([ordered_status, shipped_status, intransit_status, delivered_status, delayed_status]),
        # top 5 low stock product chart
        'low_stock_labels': json.dumps(low_stock_label),
        'low_stock_data': json.dumps(low_stock_data),
        # inventory movement last 7 days
        'movement_dates': json.dumps(dates),
        'stock_in_data': json.dumps(stock_in_data),
        'stock_out_data': json.dumps(stock_out_data),
    }
    return render(request, "staff_dashboard.html", context)


def view_all(request):
    recent_logins = User.objects.order_by('-last_login')
    users = User.objects.all()
    return render(request, 'inventory/view_all.html', {'users': users, 'recent_logins': recent_logins})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_orders(request):
    status = request.GET.get("status")
    payment_status = request.GET.get("payment_status")

    orders = Order.objects.all()

    if status:
        orders = orders.filter(status__iexact=status)

    if payment_status:
        orders = orders.filter(payment_status__iexact=payment_status)

    orders = orders.order_by("-created_at")

    return render(request, "inventory/order_list.html", {
        "orders": orders
    })
