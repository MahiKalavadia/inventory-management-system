from django.shortcuts import render
from inventory.models import Product, Category, StockLog
from suppliers.models import Supplier
from accounts.decorators import role_required
from inventory.config import LOW_STOCK_THRESHOLD


def landing(request):
    return render(request, "landing.html")


@role_required("Admin")
def admin_dashboard(request):
    total_products = Product.objects.count()
    total_categories = Category.objects.count()
    total_suppliers = Supplier.objects.count()
    low_stock_products = Product.objects.filter(
        quantity__lte=LOW_STOCK_THRESHOLD, is_active=True)
    low_stock = low_stock_products.count()
    out_of_stock = Product.objects.filter(quantity__lte=0).count()
    in_stock = Product.objects.filter(quantity__gt=LOW_STOCK_THRESHOLD).count()
    recent_stock_logs = StockLog.objects.select_related(
        'product').order_by('-created_at')[:5]

    # Progress bar indicator to show percentage distribution of stocks
    low_stock_bar = Product.objects.filter(
        quantity__lte=LOW_STOCK_THRESHOLD, is_active=True).count()
    in_stock_bar = Product.objects.filter(
        quantity__gt=LOW_STOCK_THRESHOLD, is_active=True).count()
    out_stock_bar = Product.objects.filter(
        quantity__lte=0, is_active=True).count()

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
        # progress bar
        'low_stock_bar': percent(low_stock_bar),
        'in_stock_bar': percent(in_stock_bar),
        'out_stock_bar': percent(out_stock_bar),
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
