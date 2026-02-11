from django.urls import path
from .views import landing, admin_dashboard, manager_dashboard, staff_dashboard, view_all, admin_orders

urlpatterns = [
    path("", landing, name="landing"),
    path("admin-dashboard/", admin_dashboard, name="admin_dashboard"),
    path("manager-dashboard/", manager_dashboard, name="manager_dashboard"),
    path("staff-dashboard/", staff_dashboard, name="staff_dashboard"),
    path('view-all/', view_all, name="view_all"),
    path('admin-orders/', admin_orders, name="admin_orders"),
]
