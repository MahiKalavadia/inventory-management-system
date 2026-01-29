from django.shortcuts import render
from inventory.models import Product, Category, StockLog
from suppliers.models import Supplier
from accounts.decorators import role_required
from inventory.config import LOW_STOCK_THRESHOLD
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


def landing(request):
    return render(request, "landing.html")


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
    # recent activities
    recent_products = Product.objects.order_by('-created_at')[:3]
    recent_stock_log = StockLog.objects.select_related(
        'product').order_by('-created_at')[:3]
    recent_categories = Category.objects.order_by('-id')[:2]
    recent_suppliers = Supplier.objects.order_by('-id')[:2]

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
        # recent activity
        'recent_activity': activities,
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
        quantity__lte=LOW_STOCK_THRESHOLD, is_active=True).count()
    out_stock = Product.objects.filter(quantity=0, is_active=True).count()

    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_suppliers': total_suppliers,
        'in_stock': in_stock,
        'low_stock': low_stock,
        'out_stock': out_stock,
    }
    return render(request, "manager_dashboard.html", context)


@role_required("Staff")
def staff_dashboard(request):
    total_products = Product.objects.count()
    in_stock = Product.objects.filter(
        quantity__gt=LOW_STOCK_THRESHOLD, is_active=True).count()
    low_stock = Product.objects.filter(
        quantity__lte=LOW_STOCK_THRESHOLD, is_active=True).count()
    out_stock = Product.objects.filter(quantity=0, is_active=True).count()

    context = {
        'total_products': total_products,
        'in_stock': in_stock,
        'low_stock': low_stock,
        'out_stock': out_stock,
    }
    return render(request, "staff_dashboard.html", context)


def view_all(request):
    recent_logins = User.objects.order_by('-last_login')
    users = User.objects.all()
    return render(request, 'inventory/view_all.html', {'users': users, 'recent_logins': recent_logins})
