from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category, StockLog
from suppliers.models import Supplier
from django.db.models import Q, F, Sum,  FloatField, ExpressionWrapper, DecimalField, Value, Avg
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from .forms import ProductForm, CategoryForm, StockForm
from django.db.models import Count
from inventory.config import LOW_STOCK_THRESHOLD
from django.contrib import messages
from django.db.models.functions import TruncMonth, Coalesce


@login_required
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

    # charts
    top_categories = (
        Product.objects.values('category__name')
        .annotate(total=Count('id'))
        .order_by('-total')[:8]
    )

    category_names = [c['category__name']
                      or "Uncategorized" for c in top_categories]
    category_counts = [c['total'] for c in top_categories]

    top_expensive = Product.objects.filter(
        price__isnull=False).order_by('-price')[:5]
    expensive_names = [p.name for p in top_expensive]
    expensive_prices = [float(p.price) for p in top_expensive]

    monthly_products = (
        Product.objects
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')
    )

    months = [m['month'].strftime('%b %Y')
              for m in monthly_products if m['month']]
    monthly_counts = [m['total'] for m in monthly_products]

    category_value_data = Category.objects.annotate(
        inventory_value=Sum(
            ExpressionWrapper(
                F('product__price') * F('product__quantity'),
                output_field=FloatField()
            )
        )
    ).order_by('-inventory_value')[:8]

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
        'category_names': category_names,
        'category_counts': category_counts,
        'expensive_names': expensive_names,
        'expensive_prices': expensive_prices,
        'months': months,
        'monthly_counts': monthly_counts,
        'category_value_labels': [c.name for c in category_value_data],
        'category_value_values': [float(c.inventory_value or 0) for c in category_value_data],
    }

    return render(request, "dashboards/product_dashboard.html", context)


@login_required
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


@login_required
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_dashboard')
    else:
        form = ProductForm()

    return render(request, 'inventory/add_product.html', {'form': form})


@login_required
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


@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        product.is_active = False
        product.save()
        return redirect('product_dashboard')

    return render(request, 'inventory/delete_product.html', {'product': product})


@login_required
def category_dashboard(request):
    categories_qs = Category.objects.annotate(
        product_count=Count('product', distinct=True)
    ).order_by('name')

    search = request.GET.get('q')
    if search:
        categories_qs = categories_qs.filter(
            Q(name__icontains=search)
        )

    paginator = Paginator(categories_qs, 5)
    page_number = request.GET.get('page')
    categories = paginator.get_page(page_number)

    total_category = Category.objects.count()
    categories_with_products = Category.objects.annotate(
        product_count=Count('product')
    ).filter(product_count__gt=0).count()
    categories_without_products = Category.objects.annotate(
        product_count=Count('product')
    ).filter(product_count=0).count()

    # Charts
    # Products per Category
    products_per_category = Category.objects.annotate(
        product_count=Count('product')
    )
    # Stock value per category(price * quantity )
    stock_value = Category.objects.annotate(
        total_stock_value=Coalesce(
            Sum(
                ExpressionWrapper(
                    F('product__price') * F('product__quantity'),
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                )
            ),
            Value(0, output_field=DecimalField(
                max_digits=12, decimal_places=2))
        )
    )

    # sales per category
    sales_per_category = Category.objects.annotate(
        total_sales=Coalesce(
            Sum('product__orderitem__price',
                output_field=DecimalField(max_digits=12, decimal_places=2)
                ),
            Value(0, output_field=DecimalField(
                max_digits=12, decimal_places=2))
        )
    )

    context = {
        'categories': categories,
        'total_category': total_category,
        'categories_with_products': categories_with_products,
        'categories_without_products': categories_without_products,
        'search': search,
        'products_per_category': products_per_category,
        'stock_value': stock_value,
        'sales_per_category': sales_per_category,
    }

    return render(request, "dashboards/category_dashboard.html", context)


@login_required
def category_without_products(request):
    categories_qs = Category.objects.annotate(
        product_count=Count('product', distinct=True)
    ).order_by('name')
    categories_without_products = categories_qs.filter(product_count=0).all()

    paginator = Paginator(categories_without_products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "inventory/category_without_products.html", {'page_obj': page_obj})


@login_required
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


@login_required
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


@login_required
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


@login_required
def add_category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('category_dashboard')
    else:
        form = CategoryForm()

    return render(request, 'inventory/add_category.html', {'form': form})


@login_required
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


@login_required
def delete_category(request, pk):
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        category.delete()
        return redirect('category_dashboard')

    return render(request, 'inventory/delete_category.html', {
        'category': category
    })


@login_required
def stock_dashboard(request):
    # ---------- FILTER PARAMETERS ----------
    category_id = request.GET.get('category')
    supplier_id = request.GET.get('supplier')
    status = request.GET.get('status')
    search = request.GET.get('q')

    # ---------- BASE QUERY ----------
    product_qs = Product.objects.select_related(
        'category', 'supplier').filter(is_active=True)

    # ---------- APPLY FILTERS ----------
    if category_id:
        product_qs = product_qs.filter(category_id=category_id)
    if supplier_id:
        product_qs = product_qs.filter(supplier_id=supplier_id)
    if status == 'in':
        product_qs = product_qs.filter(quantity__gt=LOW_STOCK_THRESHOLD)
    elif status == 'low':
        product_qs = product_qs.filter(
            quantity__lte=LOW_STOCK_THRESHOLD, quantity__gt=0)
    elif status == 'out':
        product_qs = product_qs.filter(quantity=0)
    if search:
        product_qs = product_qs.filter(
            Q(name__icontains=search) | Q(sku__icontains=search))

    # ---------- SUMMARY COUNTS ----------
    total_products = Product.objects.filter(is_active=True).count()
    in_stock = Product.objects.filter(
        quantity__gt=LOW_STOCK_THRESHOLD, is_active=True).count()
    low_stock = Product.objects.filter(
        quantity__lte=LOW_STOCK_THRESHOLD, quantity__gt=0, is_active=True).count()
    out_stock = Product.objects.filter(quantity=0, is_active=True).count()

    # ---------- TOTAL STOCK IN/OUT ----------
    total_stock_in = StockLog.objects.filter(action='IN').aggregate(
        Sum('quantity'))['quantity__sum'] or 0
    total_stock_out = StockLog.objects.filter(
        action='OUT').aggregate(Sum('quantity'))['quantity__sum'] or 0

    # ---------- LOW STOCK PRODUCTS ----------
    low_qs = Product.objects.filter(
        quantity__lte=LOW_STOCK_THRESHOLD, quantity__gt=0, is_active=True).select_related('category', 'supplier')

    # ---------- PAGINATION ----------
    product_paginator = Paginator(product_qs.order_by('name'), 5)
    product_page = request.GET.get('page_products')
    products = product_paginator.get_page(product_page)

    low_paginator = Paginator(low_qs.order_by('name'), 5)
    low_page = request.GET.get('page_low')
    low_stock_products = low_paginator.get_page(low_page)

    # ---------- RECENT LOGS ----------
    recent_logs = StockLog.objects.select_related(
        'product', 'user').order_by('-created_at')[:10]

    # ---------- CONTEXT ----------
    context = {
        # cards
        'total_products': total_products,
        'in_stock': in_stock,
        'low_stock': low_stock,
        'out_stock': out_stock,

        # tables
        'products': products,
        'low_stock_products': low_stock_products,
        'recent_logs': recent_logs,

        # stats
        'total_stock_in': total_stock_in,
        'total_stock_out': total_stock_out,

        # filters
        'categories': Category.objects.all(),
        'suppliers': Supplier.objects.all(),
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
        user = request.user

        if user.is_superuser:
            return redirect('admin_dashboard')
        elif user.is_staff:
            return redirect('manager_dashboard')
        else:
            return redirect('staff_dashboard')
    else:
        # Pre-fill form with product if available
        initial_data = {
            'product': product_instance} if product_instance else {}
        form = StockForm(initial=initial_data)
    return render(request, 'inventory/stock_in.html', {'form': form, 'product': product_id})


@login_required
def stock_out(request):
    form = StockForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        product = form.cleaned_data['product']
        qty = form.cleaned_data['quantity']

        product.refresh_from_db()

        if qty > product.quantity:
            messages.error(request, 'Insufficient stock availability!')
            return redirect('stock_out')

        product.quantity = F('quantity') - qty
        product.save(update_fields=['quantity'])

        StockLog.objects.create(
            product=product,
            action=StockLog.STOCK_OUT,
            quantity=qty
        )

        messages.success(request, "Stock removed successfully!")

        # role based redirect
        user = request.user
        if user.is_superuser:
            return redirect('admin_dashboard')
        elif user.is_staff:
            return redirect('manager_dashboard')
        else:
            return redirect('staff_dashboard')

    return render(request, 'inventory/stock_out.html', {'form': form})


@login_required
def stock_history(request):
    logs = StockLog.objects.select_related(
        'product', 'user').order_by('-created_at')

    paginator = Paginator(logs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/stock_history.html', {'page_obj': page_obj})


@login_required
def in_stock_products(request):
    products = Product.objects.filter(
        quantity__gt=LOW_STOCK_THRESHOLD, is_active=True)

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/in_stock.html', {'page_obj': page_obj})


@login_required
def low_stock_products(request):
    products = Product.objects.filter(
        quantity__lte=LOW_STOCK_THRESHOLD, quantity__gt=0, is_active=True)

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/low_stock.html', {'page_obj': page_obj, "low_stock_limit": LOW_STOCK_THRESHOLD})


@login_required
def out_stock_products(request):
    products = Product.objects.filter(quantity=0, is_active=True)

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "inventory/out_stock.html", {"page_obj": page_obj})


@login_required
def report_dashboard(request):
    return render(request, "dashboards/report_dashboard.html")
