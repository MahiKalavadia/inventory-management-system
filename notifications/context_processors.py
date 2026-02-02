from .models import Notification
from django.db.models import Q


def notification_data(request):
    if request.user.is_authenticated:

        # Detect role
        if request.user.is_superuser:
            role = "admin"
        elif request.user.groups.filter(name="Manager").exists():
            role = "manager"
        else:
            role = "staff"

        unread = Notification.objects.filter(
            Q(role_target=role) | Q(user_target=request.user),
            is_read=False
        ).order_by('-created_at')

        return {
            'notifications': unread[:5],
            'notifications_count': unread.count()
        }

    return {}
