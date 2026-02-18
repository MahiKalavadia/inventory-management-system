from django.utils import timezone
from datetime import timedelta
from notifications.models import Notification


def get_retention_days():
    try:
        from settings_app.models import SystemSettings
        return SystemSettings.load().notification_retention_days
    except Exception:
        return 15


def delete_old_notifications():
    retention_days = get_retention_days()
    cutoff = timezone.now() - timedelta(days=retention_days)

    Notification.objects.filter(
        notification_type__in=['product', 'supplier', 'category'],
        is_read=True,
        created_at__lt=cutoff
    ).delete()
