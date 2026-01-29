from django.contrib.auth.models import User, Group
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from .forms import AddUserForm, UpdateUserForm, ResetPasswordForm
# Only superuser can access
superuser_required = user_passes_test(lambda u: u.is_superuser)


@user_passes_test(lambda u: u.is_superuser)
def user_dashboard(request):
    total_users = User.objects.count()
    total_managers = User.objects.filter(groups__name='Manager').count()
    total_staff = User.objects.filter(groups__name='Staff').count()
    inactive_users = User.objects.filter(is_active=False).count()
    recent_logins = User.objects.order_by('-last_login')[:3]
    users = User.objects.all()

    context = {
        'total_users': total_users,
        'total_managers': total_managers,
        'total_staff': total_staff,
        'inactive_users': inactive_users,
        'recent_logins': recent_logins,
        'users': users,
    }
    return render(request, 'dashboards/user_dashboard.html', context)


def view_users(request):
    all_users = User.objects.all()
    context = {'users': all_users}
    return render(request, 'inventory/view_users.html', context)

# Activate / Deactivate user


@user_passes_test(lambda u: u.is_superuser)
def toggle_user_status(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f"{user.username} has been {status}.")
    return redirect('user_dashboard')


@superuser_required
def add_user(request):
    if request.method == 'POST':
        form = AddUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User added successfully!")
            return redirect('view_users')
    else:
        form = AddUserForm()
    return render(request, 'inventory/add_user.html', {'form': form})

# Update User


@superuser_required
def update_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    initial_role = user.groups.first().name if user.groups.exists() else None
    if request.method == 'POST':
        form = UpdateUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully!")
            return redirect('view_users')
    else:
        form = UpdateUserForm(instance=user, initial={'role': initial_role})
    return render(request, 'inventory/update_user.html', {'form': form, 'user': user})

# Reset Password


@superuser_required
def reset_user_password(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, f"Password for {user.username} updated!")
            return redirect('view_users')
    else:
        form = ResetPasswordForm()
    return render(request, 'inventory/reset_password.html', {'form': form, 'user': user})
