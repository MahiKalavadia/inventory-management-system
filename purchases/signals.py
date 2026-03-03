from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from decimal import Decimal
from django.utils.timezone import now

from .models import PurchaseOrder, PurchaseRequest
from notifications.models import Notification


# ==========================================
# STORE OLD STATUS FOR REQUEST
# ==========================================
@receiver(pre_save, sender=PurchaseRequest)
def store_old_request_status(sender, instance, **kwargs):
    """
    Store the previous status of a PurchaseRequest.
    Works normally for updates, safely skips if object is being created (fixture load).
    """
    if kwargs.get("raw", False):  # skip during fixture load
        instance._old_status = None
        return

    try:
        old = PurchaseRequest.objects.get(pk=instance.pk)
        instance._old_status = old.status
    except PurchaseRequest.DoesNotExist:
        instance._old_status = None

# ==========================================
# PURCHASE REQUEST LOGIC
# ==========================================


@receiver(post_save, sender=PurchaseRequest)
def purchase_request_signal(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            title="New Purchase Request",
            message=f"{instance.requested_by.username} requested {instance.product.name}",
            type="warning",
            notification_type="purchase",
            allowed_roles="admin"
        )
        return

    old_status = getattr(instance, "_old_status", None)
    if old_status != instance.status:
        group = instance.requested_by.groups.first()
        creator_role = group.name.lower() if group else "staff"

        if instance.status == "Approved":
            Notification.objects.create(
                title="Request Approved",
                message=f"Your request for {instance.product.name} was approved",
                type="success",
                notification_type="purchase",
                allowed_roles=creator_role
            )
        elif instance.status == "Rejected":
            Notification.objects.create(
                title="Request Rejected",
                message=f"Your request for {instance.product.name} was rejected",
                type="danger",
                notification_type="purchase",
                allowed_roles=creator_role
            )

# ==========================================
# STORE OLD STATUS FOR PO
# ==========================================


@receiver(pre_save, sender=PurchaseOrder)
def store_old_po_status(sender, instance, **kwargs):
    """
    Store the previous status of a PurchaseOrder.
    Works normally for updates, safely skips if object is being created (fixture load).
    """
    if kwargs.get("raw", False):
        instance._old_status = None
        return

    try:
        old = PurchaseOrder.objects.get(pk=instance.pk)
        instance._old_status = old.status
    except PurchaseOrder.DoesNotExist:
        instance._old_status = None

# ==========================================
# PURCHASE ORDER LOGIC
# ==========================================


@receiver(post_save, sender=PurchaseOrder)
def purchase_order_signal(sender, instance, created, **kwargs):
    if created:
        return  # no notification on creation

    old_status = getattr(instance, "_old_status", None)
    if old_status != instance.status:
        notify_roles = "manager,staff"

        # 🚚 SHIPPED
        if instance.status == "shipped":
            if instance.request and instance.request.product:
                Notification.objects.create(
                    title="Order Shipped",
                    message=f"PO-{instance.id} for {instance.request.product.name} has been shipped",
                    type="info",
                    notification_type="order",
                    allowed_roles=notify_roles
                )

        # 🚛 IN TRANSIT
        elif instance.status == "in_transit":
            Notification.objects.create(
                title="Order In Transit",
                message=f"PO-{instance.id} is on the way",
                type="info",
                notification_type="order",
                allowed_roles=notify_roles
            )

        # 📦 DELIVERED
        elif instance.status == "delivered":
            product = None
            qty = 0
            if instance.request and instance.request.product:
                product = instance.request.product
                qty = instance.request.quantity

                # Increase stock safely
                product.quantity += qty
                product.save(update_fields=["quantity"])

                # Update cost safely (no signal recursion)
                PurchaseOrder.objects.filter(pk=instance.pk).update(
                    total_cost=(product.purchase_price or Decimal("0")) * qty
                )

            # Save delivery date
            PurchaseOrder.objects.filter(pk=instance.pk).update(
                actual_delivery=now().date()
            )

            # Only send notification if product exists
            if product:
                Notification.objects.create(
                    title="Order Delivered",
                    message=f"{product.name} has arrived in inventory",
                    type="success",
                    notification_type="order",
                    allowed_roles=notify_roles
                )

        # ⏳ DELAYED
        elif instance.status == "delayed":
            Notification.objects.create(
                title="Order Delayed",
                message=f"PO-{instance.id} delivery is delayed",
                type="warning",
                notification_type="order",
                allowed_roles=notify_roles
            )
