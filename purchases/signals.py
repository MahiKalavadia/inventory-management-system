from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import PurchaseOrder, PurchaseRequest
from notifications.models import Notification
from django.contrib.auth import get_user_model
from decimal import Decimal
from inventory.models import Product
User = get_user_model()


# Store old status
@receiver(pre_save, sender=PurchaseOrder)
def store_old_po_status(sender, instance, **kwargs):
    if instance.pk:
        old = PurchaseOrder.objects.get(pk=instance.pk)
        instance._old_status = old.status
    else:
        instance._old_status = None


@receiver(post_save, sender=PurchaseOrder)
def purchase_order_notifications(sender, instance, created, **kwargs):

    # 🆕 PO CREATED → Notify Admin
    if created:
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                user_target=admin,
                title="Purchase Order Created",
                message=f"PO-{instance.id} created for {instance.request.product.name}"
            )

    # 🔁 STATUS CHANGED
    elif instance._old_status != instance.status:

        managers = User.objects.filter(groups__name="Manager")
        staff = User.objects.filter(groups__name="Staff")

        # 🚚 SHIPPED
        if instance.status == "shipped":
            for user in managers:
                Notification.objects.create(
                    user_target=user,
                    title="Order Shipped",
                    message=f"PO-{instance.id} for {instance.request.product.name} has been shipped"
                )

        # 🚛 IN TRANSIT
        elif instance.status == "in_transit":
            for user in managers:
                Notification.objects.create(
                    user_target=user,
                    title="Order In Transit",
                    message=f"PO-{instance.id} is on the way"
                )

        # 📦 DELIVERED
        elif instance.status == "delivered":
            for user in list(managers) + list(staff):
                Notification.objects.create(
                    user_target=user,
                    title="Order Delivered",
                    message=f"{instance.request.product.name} has arrived in inventory"
                )

        # ⏳ DELAYED
        elif instance.status == "delayed":
            for user in managers:
                Notification.objects.create(
                    user_target=user,
                    title="Order Delayed",
                    message=f"PO-{instance.id} delivery is delayed"
                )

    elif instance.status == "delivered":

        product = instance.request.product
        quantity_received = instance.request.quantity

        # ✅ 1. Increase stock
        product.quantity += quantity_received
        product.save()

        # ✅ 2. Calculate total purchase cost
        purchase_price = product.purchase_price or Decimal("0")
        instance.total_cost = purchase_price * quantity_received
        instance.save(update_fields=["total_cost"])

        # ✅ 3. Notify Manager + Staff
        managers = User.objects.filter(groups__name="Manager")
        staff = User.objects.filter(groups__name="Staff")

        for user in list(managers) + list(staff):
            Notification.objects.create(
                user_target=user,
                title="Stock Updated",
                message=f"{product.name} stock increased by {quantity_received} (PO-{instance.id} delivered)"
            )


@receiver(post_save, sender=PurchaseRequest)
def create_po_after_approval(sender, instance, **kwargs):
    if instance.status == "Approved":
        # Avoid duplicate PO
        if not hasattr(instance, "purchaseorder"):
            PurchaseOrder.objects.create(
                request=instance,
                supplier=instance.supplier,
                total_cost=instance.quantity * instance.product.purchase_price
            )
