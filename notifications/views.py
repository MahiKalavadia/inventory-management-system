from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST


def get_user_role(user):
    if user.is_superuser:
        return "admin"
    group = user.groups.first()
    return group.name.lower() if group else "staff"


@login_required
def dashboard_notifications(request):
    user_role = get_user_role(request.user)

    if user_role == 'admin':
        notifications = Notification.objects.all().order_by('-created_at')
    else:
        notifications = Notification.objects.filter(
            role_target__iexact=user_role
        ).order_by('-created_at')

    notifications_count = notifications.filter(is_read=False).count()
    top_notifications = notifications[:5]

    return render(request, 'inventory/dashboard_notifications.html', {
        'notifications': top_notifications,
        'notifications_count': notifications_count
    })


@login_required
def mark_as_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk)
    user_role = get_user_role(request.user)

    if notif.role_target.lower() == user_role or user_role == 'admin':
        notif.is_read = True
        notif.save()

    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def all_notifications(request):
    # Determine user role
    if request.user.is_superuser:
        user_role = 'admin'
    else:
        # Use getattr safely; default to 'staff' if 'role' doesn't exist
        user_role = getattr(request.user, 'role', 'staff')

    # Fetch notifications
    if user_role == 'admin':
        notifications = Notification.objects.all().order_by('-created_at')
    else:
        notifications = Notification.objects.filter(
            role_target=user_role).order_by('-created_at')

    paginator = Paginator(notifications, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/all_notifications.html', {'page_obj': page_obj})


@login_required
def delete_notfification(request, pk):
    notify = get_object_or_404(Notification, pk=pk)
    if request.method == "POST":
        if notify.user_target == request.user or notify.user_target is None:
            notify.delete()
            return redirect('notifications:all_notifications')

    return render(request, 'inventory/delete_notification.html', {'notify': notify})


@login_required
@require_POST
def mark_all_notifications_read(request):
    user = request.user
    user_role = get_user_role(user)

    Notification.objects.filter(
        role_target__iexact=user_role,
        is_read=False
    ).update(is_read=True)

    Notification.objects.filter(
        user_target=user,
        is_read=False
    ).update(is_read=True)

    return redirect(request.META.get('HTTP_REFERER', '/'))
