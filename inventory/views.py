from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category, StockLog
from suppliers.models import Supplier
from django.db.models import Q, F
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from .forms import ProductForm, CategoryForm, StockForm
from django.db.models import Count
from inventory.config import LOW_STOCK_THRESHOLD
from django.contrib import messages


def product_dashboard(request):
    # Search & Filters
    search = request.GET.get("search", "")
    category_id = request.GET.get("category", "")
    supplier_id = request.GET.get("supplier", "")
    status = request.GET.get("status", "")
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()

    products = Product.objects.select_related(
        "category", "supplier").filter(is_active=True)

    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(brand__icontains=search)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    if supplier_id:
        products = products.filter(supplier_id=supplier_id)

    if status == "in":
        products = products.filter(quantity__gt=5)
    elif status == "low":
        products = products.filter(
            quantity__lte=LOW_STOCK_THRESHOLD, quantity__gt=0)
    elif status == "out":
        products = products.filter(quantity=0)

    # Pagination
    paginator = Paginator(products, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Stats
    total_products = Product.objects.count()
    in_stock = Product.objects.filter(
        quantity__gt=LOW_STOCK_THRESHOLD, is_active=True).count()
    low_stock = Product.objects.filter(
        quantity__lte=LOW_STOCK_THRESHOLD, quantity__gt=0, is_active=True).count()
    out_of_stock = Product.objects.filter(quantity=0, is_active=True).count()
    total_categories = Category.objects.count()
    total_suppliers = Supplier.objects.count()
    suppliers = Supplier.objects.all()

    context = {
        'products': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        "suppliers": suppliers,
        "total_products": total_products,
        "in_stock": in_stock,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
        "total_categories": total_categories,
        "total_suppliers": total_suppliers,
        "low_stock_limit": LOW_STOCK_THRESHOLD,
    }

    return render(request, "dashboards/product_dashboard.html", context)


def product_list(request):
    products = Product.objects.select_related(
        'category', 'supplier').filter(is_active=True)

    search = request.GET.get('search')
    category = request.GET.get('category')
    supplier = request.GET.get('supplier')
    status = request.GET.get('status')

    if search:
        products = products.filter(name__icontains=search)

    if category:
        products = products.filter(category_id=category)

    if supplier:
        products = products.filter(supplier_id=supplier)

    if status == 'in':
        products = products.filter(quantity__gt=LOW_STOCK_THRESHOLD)
    elif status == 'low':
        products = products.filter(
            quantity__gt=0, quantity__lte=LOW_STOCK_THRESHOLD)
    elif status == 'out':
        products = products.filter(quantity=0)

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/product_list.html', {
        'page_obj': page_obj,
        "low_stock_limit": LOW_STOCK_THRESHOLD,
        'categories': Category.objects.all(),
        'suppliers': Supplier.objects.all(),
    })


def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_dashboard')
    else:
        form = ProductForm()

    return render(request, 'inventory/add_product.html', {'form': form})


def update_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_dashboard')
    else:
        form = ProductForm(instance=product)

    return render(request, 'inventory/update_product.html', {'form': form})


def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        product.is_active = False
        product.save()
        return redirect('product_dashboard')

    return render(request, 'inventory/delete_product.html', {'product': product})


def category_dashboard(request):
    categories_qs = Category.objects.annotate(
        product_count=Count('product', distinct=True)
    ).order_by('name')

    paginator = Paginator(categories_qs, 5)
    page_number = request.GET.get('page')
    categories = paginator.get_page(page_number)

    total_category = categories_qs.count()
    categories_with_products = categories_qs.filter(
        product_count__gt=0).count()
    categories_without_products = categories_qs.filter(product_count=0).count()

    return render(request, "dashboards/category_dashboard.html", {
        'categories': categories,
        'total_category': total_category,
        'categories_with_products': categories_with_products,
        'categories_without_products': categories_without_products,
    })


def category_without_products(request):
    categories_qs = Category.objects.annotate(
        product_count=Count('product', distinct=True)
    ).order_by('name')
    categories_without_products = categories_qs.filter(product_count=0).all()

    paginator = Paginator(categories_without_products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "inventory/category_without_products.html", {'page_obj': page_obj})


def category_with_products(request):
    categories_qs = Category.objects.annotate(
        product_count=Count('product', distinct=True)
    ).order_by('name')
    categories_with_products = categories_qs.filter(
        product_count__gt=0).all()

    paginator = Paginator(categories_with_products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "inventory/category_with_products.html", {'page_obj': page_obj})


def category_list(request):
    categories = Category.objects.all()
    data = []

    for category in categories:
        product_count = Product.objects.filter(category=category).count()
        data.append({
            'category': category,
            'total_products': product_count
        })
    paginator = Paginator(data, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/category_list.html', {
        'page_obj': page_obj,
        'data': data
    })


def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    product_list = Product.objects.filter(category=category, is_active=True)

    paginator = Paginator(product_list, 10)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    return render(request, 'inventory/category_products.html', {
        'category': category,
        'products': products
    })


def add_category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('category_dashboard')
    else:
        form = CategoryForm()

    return render(request, 'inventory/add_category.html', {'form': form})


def update_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_dashboard')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'inventory/update_category.html', {'form': form})


def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        category.delete()
        return redirect('category_dashboard')

    return render(request, 'inventory/delete_category.html', {
        'category': category
    })


def report_dashboard(request):
    return render(request, "dashboards/report_dashboard.html")


@login_required
def stock_dashboard(request):
    total_products = Product.objects.all().count()
    in_stock = Product.objects.filter(
        quantity__gt=LOW_STOCK_THRESHOLD, is_active=True).count()
    low_stock = Product.objects.filter(
        quantity__lte=LOW_STOCK_THRESHOLD, quantity__gt=0, is_active=True).count()
    out_stock = Product.objects.filter(quantity=0, is_active=True).count()

    context = {
        'total_products': total_products,
        'in_stock': in_stock,
        'low_stock': low_stock,
        'out_stock': out_stock
    }
    return render(request, 'dashboards/stock_dashboard.html', context)


@login_required
def stock_in(request, product_id=None):
    product_instance = None
    if product_id:
        product_instance = get_object_or_404(Product, id=product_id)

    form = StockForm(request.POST)
    if request.method == 'POST' and form.is_valid():
        product = form.cleaned_data['product'] if not product_instance else product_instance
        qty = form.cleaned_data['quantity']

        product.quantity = F('quantity') + qty
        product.save(update_fields=['quantity'])

        StockLog.objects.create(
            product=product,
            action=StockLog.STOCK_IN,
            quantity=qty
        )

        messages.success(request, "Stock added successfully")
        return redirect('admin_dashboard')
    else:
        # Pre-fill form with product if available
        initial_data = {
            'product': product_instance} if product_instance else {}
        form = StockForm(initial=initial_data)
    return render(request, 'inventory/stock_in.html', {'form': form, 'product': product_id})


@login_required
def stock_out(request):
    form = StockForm(request.POST or 'None')
    if request.method == "POST" and form.is_valid():
        product = form.cleaned_data['product']
        qty = form.cleaned_data['quantity']

        product.refresh_from_db()
        if qty > product.quantity:
            messages.error(request, 'Insufficent Stock availability!')
            return redirect('stock_out')

        product.quantity = F('quantity') - qty
        product.save(update_fields=['quantity'])

        StockLog.objects.create(
            product=product,
            action=StockLog.STOCK_OUT,
            quantity=qty
        )

        messages.success(request, "Stock removed successfully!")
        return redirect('admin_dashboard')

    return render(request, 'inventory/stock_out.html', {'form': form})


def in_stock_products(request):
    products = Product.objects.filter(
        quantity__gt=LOW_STOCK_THRESHOLD, is_active=True)

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/in_stock.html', {'page_obj': page_obj})


def low_stock_products(request):
    products = Product.objects.filter(
        quantity__lte=LOW_STOCK_THRESHOLD, quantity__gt=0, is_active=True)

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/low_stock.html', {'page_obj': page_obj, "low_stock_limit": LOW_STOCK_THRESHOLD})


def out_stock_products(request):
    products = Product.objects.filter(quantity=0, is_active=True)

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "inventory/out_stock.html", {"page_obj": page_obj})
