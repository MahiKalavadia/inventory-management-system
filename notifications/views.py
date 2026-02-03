from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification
from django.core.paginator import Paginator


@login_required
def dashboard_notifications(request):
    user = request.user
    user_role = 'admin' if user.is_superuser else getattr(
        user.profile, 'role', 'staff')

    if user_role == 'admin':
        notifications = Notification.objects.all().order_by('-created_at')
    else:
        notifications = Notification.objects.filter(
            role_target=user_role).order_by('-created_at')

    notifications_count = notifications.filter(is_read=False).count()
    top_notifications = notifications[:5]  # latest 5 for bell

    return render(request, 'inventory/dashboard_notifications.html', {
        'notifications': top_notifications,
        'notifications_count': notifications_count
    })


@login_required
def mark_as_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk)
    user_role = 'admin' if request.user.is_superuser else getattr(
        request.user.profile, 'role', 'staff')

    # Only allow marking if user has access
    if notif.role_target == user_role or user_role == 'admin':
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

    paginator = Paginator('notifications', 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/all_notifications.html', {'notifications': notifications, 'page_obj': page_obj})


@login_required
def delete_notfification(request, pk):
    notify = get_object_or_404(Notification, pk=pk)
    if request.method == "POST":
        if notify.user == request.user or notify.user is None:
            notify.delete()
            return redirect('notifications:all_notifications')

    return render(request, 'inventory/delete_notification.html', {'notify': notify})
