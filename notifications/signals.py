from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from inventory.models import Product, Category, StockLog
from suppliers.models import Supplier
from orders.models import Order
from .models import Notification


# ================= UTILITY FUNCTION =================

def is_notification_enabled(notification_type):
    try:
        from settings_app.models import SystemSettings
        settings_obj = SystemSettings.load()
        flag_map = {
            'product': settings_obj.enable_product_notifications,
            'stock': settings_obj.enable_stock_notifications,
            'order': settings_obj.enable_order_notifications,
            'supplier': settings_obj.enable_supplier_notifications,
            'category': settings_obj.enable_category_notifications,
            'purchase': settings_obj.enable_purchase_notifications,
        }
        return flag_map.get(notification_type, True)
    except Exception:
        return True


def create_notification(title, message, type, notification_type, roles, user=None):
    if not is_notification_enabled(notification_type):
        return
    Notification.objects.create(
        title=title,
        message=message,
        type=type,
        notification_type=notification_type,
        allowed_roles=roles,
        created_by=user  # can be None
    )


# ================= PRODUCT =================

@receiver(post_save, sender=Product)
def product_saved(sender, instance, created, **kwargs):
    roles = ['admin', 'manager', 'staff']

    create_notification(
        title=f"Product {'Added' if created else 'Updated'}",
        message=f"{instance.name} was {'added' if created else 'updated'} in inventory.",
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
    create_notification(
        title=f"Category {'Added' if created else 'Updated'}",
        message=f"{instance.name} was {'added to' if created else 'updated in'} inventory.",
        type="success" if created else "info",
        notification_type="category",
        roles=['admin', 'manager', 'staff']
    )


@receiver(post_delete, sender=Category)
def category_deleted(sender, instance, **kwargs):
    create_notification(
        title="Category Deleted",
        message=f"{instance.name} was removed from inventory.",
        type="danger",
        notification_type="category",
        roles=['admin', 'manager', 'staff']
    )


# ================= SUPPLIER =================

@receiver(post_save, sender=Supplier)
def supplier_saved(sender, instance, created, **kwargs):
    create_notification(
        title=f"Supplier {'Added' if created else 'Updated'}",
        message=f"{instance.name} was {'added to' if created else 'updated in'} inventory.",
        type="success" if created else "info",
        notification_type="supplier",
        roles=['admin', 'manager']
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
            message=f"{instance.quantity} units "
            f"{'added to' if instance.action == 'IN' else 'removed from'} "
            f"{instance.product.name}",
            type="warning",
            notification_type="stock",
            roles=['admin', 'manager', 'staff']
        )


# ================= ORDER =================

@receiver(post_save, sender=Order)
def order_saved(sender, instance, created, **kwargs):
    create_notification(
        title=f"Order {'Created' if created else 'Updated'}",
        message=(
            f"Order #{instance.id} for {instance.customer_name}"
            if created
            else f"Order #{instance.id} status updated to {instance.status}"
        ),
        type="success" if created else "info",
        notification_type="order",
        roles=['admin', 'manager', 'staff']
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
