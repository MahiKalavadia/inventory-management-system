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


def supplier_dashboard(request):
    suppliers = Supplier.objects.all()
    total_supplier = Supplier.objects.count()
    active_supplier = Supplier.objects.filter(is_active=True).count()
    inactive_supplier = Supplier.objects.filter(is_active=False).count()
    products = Product.objects.count()

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
        'page_obj': page_obj
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
    pass


def export_supplier_pdf(request):
    pass
