from django.shortcuts import render, redirect, get_object_or_404
from .forms import PurchaseOrderForm, PurchaseOrderItemForm
from .models import PurchaseOrder, PurchaseOrderItem
# Create your views here.


def purchase_dashboard(request):
    return render(request, "dashboards/purchase_dashboard.html")


def purchase_list(request):
    purchases = PurchaseOrder.objects.all().order_by('-created_at')
    return render(request, "inventory/purchase_list.html", {'purchases': purchases})


def purchase_detail(request, pk):
    purchase = get_object_or_404(PurchaseOrder, pk=pk)
    return render(request, "inventory/purchase_detail.html", {'purchase': purchase })


def create_purchase(request):
    if request.method == "POST":
        p_form = PurchaseOrderForm(request.POST)
        pi_form = PurchaseOrderItemForm(request.POST)

        if p_form.is_valid() and pi_form.is_valid():
            pass
    return render(request, "inventory/create_purchase.html")


def edit_purchase(request, pk):
    return render(request, "inventory/update_purchase.html")


def delete_purchase(request, pk):
    return render(request, "inventory/delete_purchase.html")
