from django.shortcuts import render

# Create your views here.


def purchase_dashboard(request):
    return render(request, "dashboards/purchase_dashboard.html")
