from django.shortcuts import render, redirect, get_object_or_404
from .models import PurchaseRequest
from inventory.models import Product
from django.contrib.auth.decorators import login_required


def purchase_dashboard(request):
    if request.user.is_superuser:
        requests = PurchaseRequest.objects.all().order_by('-created_at')
    else:
        requests = PurchaseRequest.objects.filter(requested_by=request.user)

    return render(request, 'dashboards/purchase_dashboard.html')


@login_required
def create_purchase_request(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        qty = int(request.POST.get("quantity"))
        PurchaseRequest.objects.create(
            product=product,
            quantity=qty,
            requested_by=request.user
        )
        return redirect('stock_dashboard')

    return render(request, "inventory/request_form.html", {"product": product})


@login_required
def approve_purchase_request(request, pr_id, action):
    pr = get_object_or_404(PurchaseRequest, id=pr_id)

    if not request.user.is_superuser:
        return redirect('admin_dashboard')

    if action == "approve":
        pr.status = "Approved"
        pr.product.quantity += pr.quantity   # STOCK INCREASE
        pr.product.save()

    elif action == "reject":
        pr.status = "Rejected"

    pr.save()
    return redirect('purchase_dashboard')
