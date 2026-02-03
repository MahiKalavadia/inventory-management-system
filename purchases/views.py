from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import PurchaseRequest, PurchaseOrder
from .forms import PurchaseRequestForm, PurchaseOrderForm
from notifications.models import Notification
from django.contrib.auth.models import User


@login_required
def purchase_dashboard(request):
    total_purchases = PurchaseRequest.objects.filter(status='Approved').count()
    order_placed = PurchaseOrder.objects.filter(status="Ordered").count()
    completed_orders = PurchaseOrder.objects.filter(status="Delivered").count()
    overdue = PurchaseOrder.objects.filter(status="Delayed").count()

    context = {
        'total_purchaserequest': total_purchases,
        'order_placed': order_placed,
        'completed_orders': completed_orders,
        'overdue': overdue,
    }
    return render(request, 'dashboards/purchase_dashboard.html', context)


@login_required
def create_purchase_request(request):
    if request.method == "POST":
        form = PurchaseRequestForm(request.POST)
        if form.is_valid():
            pr = form.save(commit=False)
            pr.requested_by = request.user
            pr.save()

            # Notify admin
            admin = User.objects.filter(is_superuser=True).first()
            Notification.objects.create(
                user=admin,
                message=f"Purchase request for {pr.product.name} ({pr.quantity})"
            )

            return redirect('dashboard')
    else:
        form = PurchaseRequestForm()
    return render(request, 'inventory/create_request.html', {'form': form})


@login_required
def approve_request(request, pk):
    pr = get_object_or_404(PurchaseRequest, pk=pk)
    if request.method == "POST":
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            pr.status = 'approved'
            pr.save()

            po = form.save(commit=False)
            po.request = pr
            po.supplier = pr.supplier
            po.total_cost = pr.product.purchase_price * pr.quantity
            po.save()

            return redirect('purchases:purchase_dashboard')
    else:
        form = PurchaseOrderForm()
    return render(request, 'inventory/approve_request.html', {'pr': pr, 'form': form})


@login_required
def reject_request(request, pk):
    pr = get_object_or_404(PurchaseRequest, pk=pk)
    pr.status = 'rejected'
    pr.save()
    return redirect('purchases:purchase_dashboard')


@login_required
def update_order_status(request, pk, status):
    order = get_object_or_404(PurchaseOrder, pk=pk)
    order.status = status

    if status == 'delivered':
        order.actual_delivery = timezone.now().date()
        # Update stock
        product = order.request.product
        product.stock += order.request.quantity
        product.save()

    order.save()
    return redirect('purchases:purchase_dashboard')
