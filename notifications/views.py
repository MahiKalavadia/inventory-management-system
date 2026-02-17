from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from .models import Notification


def get_user_role(user):
    if user.is_superuser:
        return "admin"

    group = user.groups.first()
    return group.name.lower() if group else "staff"


@login_required
def dashboard_notifications(request):
    user_role = get_user_role(request.user)

    all_notifications = Notification.objects.all().order_by('-created_at')

    if user_role == "admin":
        notifications = all_notifications
    else:
        notifications = [
            n for n in all_notifications
            if user_role in n.allowed_roles
        ]

    notifications_count = len([n for n in notifications if not n.is_read])
    top_notifications = notifications[:5]

    return render(request, 'inventory/dashboard_notifications.html', {
        'notifications': top_notifications,
        'notifications_count': notifications_count
    })


@login_required
def mark_as_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk)
    user_role = get_user_role(request.user)

    # Admin can mark anything
    if user_role == "admin" or user_role in notif.allowed_roles:
        notif.is_read = True
        notif.save()

    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def all_notifications(request):
    user_role = get_user_role(request.user)

    all_notifications = Notification.objects.all().order_by('-created_at')

    if user_role == "admin":
        notifications = all_notifications
    else:
        notifications = [
            n for n in all_notifications
            if user_role in n.allowed_roles
        ]

    paginator = Paginator(notifications, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'inventory/all_notifications.html', {
        'page_obj': page_obj
    })


@login_required
def delete_notfification(request, pk):
    notify = get_object_or_404(Notification, pk=pk)
    user_role = get_user_role(request.user)

    if request.method == "POST":
        if user_role == "admin" or user_role in notify.allowed_roles:
            notify.delete()
            return redirect('notifications:all_notifications')

    return render(request, 'inventory/delete_notification.html', {
        'notify': notify
    })


@login_required
@require_POST
def mark_all_notifications_read(request):
    user_role = get_user_role(request.user)

    all_notifications = Notification.objects.filter(is_read=False)

    for notif in all_notifications:
        if user_role == "admin" or user_role in notif.allowed_roles:
            notif.is_read = True
            notif.save()

    return redirect(request.META.get('HTTP_REFERER', '/'))
