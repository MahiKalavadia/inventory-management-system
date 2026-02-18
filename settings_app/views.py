from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import SystemSettings
from .forms import SystemSettingsForm


@login_required
@user_passes_test(lambda u: u.is_superuser)
def settings_dashboard(request):
    settings_obj = SystemSettings.load()

    if request.method == 'POST':
        form = SystemSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings updated successfully!')
            return redirect('setting_dashboard')
    else:
        form = SystemSettingsForm(instance=settings_obj)

    context = {
        'form': form,
        'settings_obj': settings_obj,
    }
    return render(request, 'settings_dashboard.html', context)
