from django.shortcuts import render, redirect, get_object_or_404
from .forms import OrderForm, OrderItemForm
from .models import Order, OrderItem
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponse
from .utils.pdf import build_receipt_pdf
from .utils.email import send_receipt_email
from django.db.models import Sum, F
# Create your views here.


def order_dashboard(request):
    total_orders = Order.objects.count()
    pending_bills = Order.objects.filter(
        status='Pending').count()  # Bill created, payment not done
    # Open bill (items being added)
    # Bills currently being handled at counter.
    open_bills = Order.objects.filter(status='Processing').count()
    completed_sales = Order.objects.filter(
        status='Delivered').count()  # Completed sale(payment completed)
    # first purchased almost created bill then told no needed
    cancelled_bills = Order.objects.filter(status='Cancelled').count()
    total_sales = (
        OrderItem.objects
        .filter(order__payment_status='Paid')
        .aggregate(total=Sum(F('quantity') * F('price')))['total']
        or 0
    )

    context = {
        'total_orders': total_orders,
        'pending_bills': pending_bills,
        'open_bills': open_bills,
        'completed_sales': completed_sales,
        'cancelled_bills': cancelled_bills,
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
    if request.method == "POST":
        order_form = OrderForm(request.POST)
        item_form = OrderItemForm(request.POST)

        if order_form.is_valid() and item_form.is_valid():
            # Save Order
            order = order_form.save(commit=False)
            order.created_by = request.user
            order.save()

            # Save OrderItem
            item = item_form.save(commit=False)
            item.order = order

            # Check stock
            if item.product.quantity < item.quantity:
                messages.error(
                    request, f"Not enough stock for {item.product.name}")
                order.delete()
                return redirect('create_order')

            # Reduce stock
            item.product.quantity -= item.quantity
            item.product.save()
            item.price = item.product.price
            item.save()

            try:
                send_receipt_email(order)
            except Exception as e:
                messages.warning(
                    request, f"Order created, but email failed: {str(e)}")

            messages.success(request, "Order created successfully!")
            return redirect('order_list')
    else:
        order_form = OrderForm()
        item_form = OrderItemForm()

    context = {
        'order_form': order_form,
        'item_form': item_form
    }
    return render(request, 'inventory/create_order.html', context)


def update_order(request, pk):
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


def download_receipt(request, order_id):
    # Get order
    order = Order.objects.get(id=order_id)

    # Create HTTP response with PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{order.id}.pdf"'

    # Call your PDF function
    build_receipt_pdf(response, order)

    return response
