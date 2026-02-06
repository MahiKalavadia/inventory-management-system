from django.utils import timezone
from datetime import timedelta
from notifications.models import Notification


def delete_old_notifications():
    cutoff = timezone.now() - timedelta(days=15)

    Notification.objects.filter(
        notification_type__in=[
            'product_added', 'product_updated', 'product_deleted',
            'category_added', 'category_updated', 'category_deleted',
            'supplier_added', 'supplier_updated', 'supplier_deleted',
        ],
        created_at__lt=cutoff
    ).delete()
