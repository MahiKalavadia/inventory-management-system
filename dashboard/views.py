from django.shortcuts import render
from inventory.models import Product, Category, StockLog
from suppliers.models import Supplier
from accounts.decorators import role_required
from inventory.config import LOW_STOCK_THRESHOLD
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from notifications.models import Notification
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Count, FloatField
from orders.models import OrderItem, Order
from purchases.models import PurchaseRequest, PurchaseOrder
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator


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
        quantity__lte=LOW_STOCK_THRESHOLD, quantity__gt=0, is_active=True)
    low_stock = low_stock_products.count()
    out_of_stock = Product.objects.filter(quantity__lte=0).count()
    in_stock = Product.objects.filter(quantity__gt=LOW_STOCK_THRESHOLD).count()
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

    # 📈 Gross Margin
    gross_margin = total_sales - total_cogs
    recent_stock_logs = StockLog.objects.select_related(
        'product').order_by('-created_at')[:5]
    # login status
    recent_logins = User.objects.order_by('-last_login')[:3]
    users = User.objects.all()
    # for admin low_stock table and out of stock table
    l_stock = Product.objects.filter(
        quantity__lte=LOW_STOCK_THRESHOLD, quantity__gt=0, is_active=True).select_related('supplier').order_by('quantity')[:3]
    o_stock = Product.objects.filter(quantity=0).order_by('quantity')[:3]
    # Progress bar indicator to show percentage distribution of stocks
    low_stock_bar = Product.objects.filter(
        quantity__lte=LOW_STOCK_THRESHOLD, quantity__gt=0, is_active=True).count()
    in_stock_bar = Product.objects.filter(
        quantity__gt=LOW_STOCK_THRESHOLD, is_active=True).count()
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
    ).order_by('-value')

    top_value_products = Product.objects.annotate(
        value=ExpressionWrapper(
            F('purchase_price') * F('quantity'),
            output_field=FloatField()
        )
    ).order_by('-value')

    paginator = Paginator(top_suppliers, 5)
    suppliers = request.GET.get('page_s')
    supply = paginator.get_page(suppliers)

    paginator = Paginator(top_value_products, 5)
    page_number = request.GET.get('page')
    productt = paginator.get_page(page_number)

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
        'supply': supply,
        'productt': productt,

        "pending_requests_count": PurchaseRequest.objects.filter(
            status="Pending"
        ).count(),

        # Active = anything not delivered
        "active_po_count": PurchaseOrder.objects.exclude(
            status="delivered"
        ).count(),
    }

    return render(request, "admin_dashboard.html", context)


@role_required("Manager")
def manager_dashboard(request):
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_suppliers = Supplier.objects.count()
    in_stock = Product.objects.filter(
        quantity__gt=LOW_STOCK_THRESHOLD, is_active=True).count()
    low_stock = Product.objects.filter(
        quantity__lte=LOW_STOCK_THRESHOLD, quantity__gt=0, is_active=True).count()
    out_stock = Product.objects.filter(quantity=0, is_active=True).count()

    l_stock = Product.objects.filter(
        quantity__lte=LOW_STOCK_THRESHOLD,
        quantity__gt=0
    ).select_related('supplier').order_by('quantity')[:5]

    o_stock = Product.objects.filter(quantity=0).order_by('name')[:5]

    # Recent stock activity
    recent_stock_logs = StockLog.objects.select_related(
        'product').order_by('-created_at')[:5]

    notifications = get_user_notifications(request.user, 5)
    notifications_count = len(notifications)

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

    }
    return render(request, "manager_dashboard.html", context)


@role_required("Staff")
def staff_dashboard(request):
    total_products = Product.objects.count()
    in_stock = Product.objects.filter(
        quantity__gt=LOW_STOCK_THRESHOLD, is_active=True).count()
    low_stock = Product.objects.filter(
        quantity__lte=LOW_STOCK_THRESHOLD, quantity__gt=0, is_active=True).count()
    out_stock = Product.objects.filter(quantity=0, is_active=True).count()
    low_stock_products = Product.objects.filter(
        quantity__lte=LOW_STOCK_THRESHOLD,
        quantity__gt=0,
        is_active=True
    ).select_related('supplier')[:5]
    recent_stock_logs = StockLog.objects.select_related(
        'product'
    ).order_by('-created_at')[:5]

    notifications = get_user_notifications(request.user, 5)
    notifications_count = len(notifications)

    context = {
        'total_products': total_products,
        'in_stock': in_stock,
        'low_stock': low_stock,
        'out_stock': out_stock,
        'low_stock_products': low_stock_products,
        'recent_stock_logs': recent_stock_logs,
        'notifications': notifications,
        'notifications_count': notifications_count,
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
