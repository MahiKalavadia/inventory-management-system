from django.shortcuts import render, redirect, get_object_or_404
from .forms import OrderForm, OrderItemForm
from .models import Order, OrderItem
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse
from .utils.pdf import build_receipt_pdf
from .utils.email import send_receipt_email
from django.db.models import Sum, F
from django.db import transaction
from django.forms import inlineformset_factory
# Create your views here.


def staff_or_manager(user):
    return user.is_superuser or user.groups.filter(name__in=['Manager', 'Staff']).exists()


def manager_only(user):
    return user.is_superuser or user.groups.filter(name='Manager').exists()


def admin_only(user):
    return user.is_superuser


def order_dashboard(request):
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(
        status='Draft').count()
    confirmed_orders = Order.objects.filter(status='Confirmed').count()
    paid_orders = Order.objects.filter(status='Paid').count()
    cancelled_orders = Order.objects.filter(status='Cancelled').count()
    total_sales = (
        OrderItem.objects
        .filter(order__payment_status='Paid')
        .aggregate(total=Sum(F('quantity') * F('price')))['total']
        or 0
    )

    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'confirmed_orders': confirmed_orders,
        'paid_orders': paid_orders,
        'cancelled_orders': cancelled_orders,
        'total_sales': total_sales,
    }

    return render(request, "dashboards/order_dashboard.html", context)


def order_list(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'inventory/order_list.html', {'orders': orders})


def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'inventory/order_detail.html', {'order': order})


def order_receipt(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if order.payment_status != "Paid":
        return HttpResponseForbidden("Receipt available only for paid orders")

    return render(request, 'inventory/receipt.html', {'order': order})


def create_order(request):
    if not staff_or_manager(request.user):
        return HttpResponseForbidden("Not allowed")

    # Create formset with an empty Order instance
    OrderItemFormSet = inlineformset_factory(
        Order, OrderItem, form=OrderItemForm, extra=1, can_delete=False
    )

    # Use a new unsaved Order instance for the formset
    temp_order = Order()

    if request.method == "POST":
        order_form = OrderForm(request.POST)
        formset = OrderItemFormSet(request.POST, instance=temp_order)

        if order_form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    order = order_form.save(commit=False)
                    order.created_by = request.user
                    order.save()

                    # Save all items with the actual order
                    for form in formset:
                        item = form.save(commit=False)
                        item.order = order

                        if item.product.quantity < item.quantity:
                            raise ValueError(
                                f"Not enough stock for {item.product.name}")

                        item.product.quantity -= item.quantity
                        item.product.save()

                        item.price = item.product.price
                        item.save()

            except Exception as e:
                messages.error(request, str(e))
                return redirect('create_order')

            messages.success(request, "Order created successfully!")
            return redirect('order_list')

    else:
        order_form = OrderForm()
        formset = OrderItemFormSet(instance=temp_order)  # Important!

    context = {
        'order_form': order_form,
        'formset': formset
    }
    return render(request, 'inventory/create_order.html', context)


def update_order(request, pk):
    if not manager_only(request.user):
        return HttpResponseForbidden("Only managers can edit orders")

    order = get_object_or_404(Order, pk=pk)
    item = order.items.first()
    if request.method == "POST":
        order_form = OrderForm(request.POST, instance=order)
        item_form = OrderItemForm(request.POST, instance=item)

        if order_form.is_valid() and item_form.is_valid():
            order_form.save()

            # Update stock correctly
            old_quantity = item.quantity
            updated_item = item_form.save(commit=False)
            diff = updated_item.quantity - old_quantity

            # Check stock
            if updated_item.product.quantity < diff:
                messages.error(
                    request, f"Not enough stock for {updated_item.product.name}")
                return redirect('update_order', pk=order.id)

            # Update stock
            updated_item.product.quantity -= diff
            updated_item.product.save()

            updated_item.save()
            messages.success(request, "Order updated successfully!")
            return redirect('order_detail', pk=order.id)

    else:
        order_form = OrderForm(instance=order)
        item_form = OrderItemForm(instance=item)

    return render(request, 'inventory/update_order.html', {
        'order_form': order_form,
        'item_form': item_form,
        'order': order
    })


def delete_order(request, pk):
    if not admin_only(request.user):
        return HttpResponseForbidden("Only admin can delete orders")
    order = get_object_or_404(Order, pk=pk)

    if request.method == "POST":
        # Restore stock
        for item in order.items.all():
            item.product.quantity += item.quantity
            item.product.save()

        order.delete()
        messages.success(request, "Order deleted successfully.")
        return redirect('order_list')
    return render(request, 'inventory/delete_order.html', {'order': order})


def confirm_order(request, pk):
    if not manager_only(request.user):
        return HttpResponseForbidden("Only managers can confirm orders")

    order = get_object_or_404(Order, pk=pk)
    order.status = "Confirmed"
    order.save()
    return redirect('order_detail', pk=pk)


def mark_paid(request, pk):
    if not manager_only(request.user):
        return HttpResponseForbidden("Only managers can mark payment")

    order = get_object_or_404(Order, pk=pk)
    order.payment_status = "Paid"
    order.status = "Paid"
    order.save()
    return redirect('order_detail', pk=pk)


def download_receipt(request, pk):
    # Get order
    order = Order.objects.get(id=pk)

    # receipt available only after payment is completed
    if order.payment_status != "Paid":
        return HttpResponseForbidden("Receipt available only after payment.")

    # Create HTTP response with PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{order.id}.pdf"'

    # Call your PDF function
    build_receipt_pdf(response, order)

    return response
