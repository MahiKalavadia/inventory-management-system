from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from inventory.models import Product, Category, StockLog
from suppliers.models import Supplier
from orders.models import Order
from purchases.models import PurchaseRequest
from .models import Notification

# Utility function to create notifications for multiple roles


def create_notification(title, message, type, notification_type, roles):
    for role in roles:
        Notification.objects.create(
            title=title,
            message=message,
            type=type,
            notification_type=notification_type,
            role_target=role
        )

# ================= PRODUCT =================


@receiver(post_save, sender=Product)
def product_saved(sender, instance, created, **kwargs):
    roles = ['admin', 'manager', 'staff'] if created else [
        'admin', 'manager', 'staff']
    action = "added to" if created else "updated"
    create_notification(
        title=f"Product {'Added' if created else 'Updated'}",
        message=f"{instance.name} was {action} inventory.",
        type="success" if created else "info",
        notification_type="product",
        roles=roles
    )


@receiver(post_delete, sender=Product)
def product_deleted(sender, instance, **kwargs):
    create_notification(
        title="Product Deleted",
        message=f"{instance.name} was removed from inventory.",
        type="danger",
        notification_type="product",
        roles=['admin', 'manager', 'staff']
    )

# ================= CATEGORY =================


@receiver(post_save, sender=Category)
def category_saved(sender, instance, created, **kwargs):
    roles = ['admin', 'manager']
    create_notification(
        title=f"Category {'Added' if created else 'Updated'}",
        message=f"{instance.name} was {'added to' if created else 'updated in'} inventory.",
        type="success" if created else "info",
        notification_type="category",
        roles=roles
    )


@receiver(post_delete, sender=Category)
def category_deleted(sender, instance, **kwargs):
    create_notification(
        title="Category Deleted",
        message=f"{instance.name} was removed from inventory.",
        type="danger",
        notification_type="category",
        roles=['admin', 'manager']
    )

# ================= SUPPLIER =================


@receiver(post_save, sender=Supplier)
def supplier_saved(sender, instance, created, **kwargs):
    roles = ['admin', 'manager']
    create_notification(
        title=f"Supplier {'Added' if created else 'Updated'}",
        message=f"{instance.name} was {'added to' if created else 'updated in'} inventory.",
        type="success" if created else "info",
        notification_type="supplier",
        roles=roles
    )


@receiver(post_delete, sender=Supplier)
def supplier_deleted(sender, instance, **kwargs):
    create_notification(
        title="Supplier Deleted",
        message=f"{instance.name} was removed from inventory.",
        type="danger",
        notification_type="supplier",
        roles=['admin', 'manager']
    )

# ================= STOCK =================


@receiver(post_save, sender=StockLog)
def stock_log_created(sender, instance, created, **kwargs):
    if created:
        create_notification(
            title="Stock Movement",
            message=f"{instance.quantity} units {'added to' if instance.action == 'IN' else 'removed from'} {instance.product.name}",
            type="warning",
            notification_type="stock",
            roles=['admin', 'manager', 'staff']
        )

# ================= ORDER =================


@receiver(post_save, sender=Order)
def order_saved(sender, instance, created, **kwargs):
    roles = ['admin', 'manager', 'staff']
    create_notification(
        title=f"Order {'Created' if created else 'Updated'}",
        message=f"Order #{instance.id} for {instance.customer_name if created else 'status: ' + instance.status}",
        type="success" if created else "info",
        notification_type="order",
        roles=roles
    )


@receiver(post_delete, sender=Order)
def order_deleted(sender, instance, **kwargs):
    create_notification(
        title="Order Deleted",
        message=f"Order #{instance.id} was deleted.",
        type="danger",
        notification_type="order",
        roles=['admin', 'manager', 'staff']
    )

# ================= PURCHASE REQUEST =================


@receiver(post_save, sender=PurchaseRequest)
def purchase_request_saved(sender, instance, created, **kwargs):
    create_notification(
        title="Purchase Request",
        message=f"{instance.product.name} request is {instance.status}",
        type="warning",
        notification_type="purchase",
        roles=['admin', 'manager']  # Only admin and manager
    )
