from django.utils import timezone
from datetime import timedelta
from notifications.models import Notification


def delete_old_notifications():

    fifteen_days_ago = timezone.now() - timedelta(days=15)

    Notification.objects.filter(
        notification_type__in=['product', 'supplier', 'category'],
        is_read=True,
        created_at__lt=fifteen_days_ago
    ).delete()
