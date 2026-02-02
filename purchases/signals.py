from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PurchaseRequest
from notifications.models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=PurchaseRequest)
def create_purchase_notifications(sender, instance, created, **kwargs):

    # 🆕 When request created → notify Admins
    if created:
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                user=admin,
                message=f"New Purchase Request: {instance.product.name} ({instance.quantity})"
            )

    # ✅ When approved → notify requester
    if instance.status == "Approved":
        Notification.objects.create(
            user=instance.requested_by,
            message=f"Your request for {instance.product.name} was APPROVED"
        )

    # ❌ When rejected
    if instance.status == "Rejected":
        Notification.objects.create(
            user=instance.requested_by,
            message=f"Your request for {instance.product.name} was REJECTED"
        )
