from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from django.utils import timezone
from datetime import timedelta


@receiver(post_save, sender=Order)
def start_warranty_on_completion(sender, instance, **kwargs):
    if instance.status == "completed":
        for item in instance.orderitem_set.all():
            if not item.warranty_start:
                item.warranty_start = timezone.now().date()
                item.warranty_end = item.warranty_start + \
                    timedelta(days=30 * item.warranty_months)
                item.save()
