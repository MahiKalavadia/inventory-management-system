from django.urls import path
from . import views

urlpatterns = [
    path('purchase-dashboard/', views.purchase_dashboard,
         name='purchase_dashboard'),
    path('purchase-dashboard_ms/', views.purchase_dashboard_ms,
         name='purchase_dashboard2'),
    path('purchase/request/', views.purchase_request, name="purchase_request"),
    path('request/<int:product_id>/', views.create_request, name="create_request"),
    path('manage/', views.manage_requests, name="manage_requests"),
    path('approve/<int:pk>/', views.approve_request, name="approve_request"),
    path('reject/<int:pk>/', views.reject_request, name="reject_request"),
    path('orders/', views.purchase_orders, name="purchase_orders"),
    path('po/update/<int:pk>/', views.update_po_status, name="update_po_status"),
    path('purchase/records/', views.all_purchase_records, name='records'),
    path("export/requests/csv/", views.export_requests_csv,
         name="export_requests_csv"),
    path("export/requests/excel/", views.export_requests_excel,
         name="export_requests_excel"),
    path("export/requests/pdf/", views.export_requests_pdf,
         name="export_requests_pdf"),

    path("export/orders/csv/", views.export_orders_csv, name="export_orders_csv"),
    path("export/orders/excel/", views.export_orders_excel,
         name="export_orders_excel"),
    path("export/orders/pdf/", views.export_orders_pdf, name="export_orders_pdf"),
]
