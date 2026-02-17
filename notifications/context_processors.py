from .models import Notification


def notification_data(request):

    if not request.user.is_authenticated:
        return {}

    # Get user group (Manager / Staff)
    group = request.user.groups.first()

    if not group:
        return {
            "unread_notifications": Notification.objects.none(),
            "unread_count": 0
        }

    user_role = group.name.lower()

    unread = Notification.objects.filter(
        allowed_roles__contains=[user_role],
        is_read=False
    ).order_by("-created_at")

    return {
        "unread_notifications": unread,
        "unread_count": unread.count()
    }
