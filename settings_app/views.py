from django.shortcuts import render

# Create your views here.


def settings_dashboard(request):
    return render(request, 'settings_dashboard.html')
