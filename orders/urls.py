from django.urls import path
from . import views

urlpatterns = [
    path('orders/dashboard/', views.order_dashboard,
         name='order_dashboard'),
    path('orders/list/', views.order_list, name='order_list'),
    path('orders/detail/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/receipt/<int:pk>/', views.order_receipt, name='order_receipt'),
    path('orders/create/', views.create_order, name='create_order'),
    path('orders/update/<int:pk>/', views.update_order, name='update_order'),
    path('orders/delete/<int:pk>/', views.delete_order, name='delete_order'),
    path('order/<int:pk>/confirm/', views.confirm_order, name='confirm_order'),
    path('order/<int:pk>/paid/', views.mark_paid, name='mark_paid'),
    path("receipt/<int:pk>/download/",
         views.download_receipt, name="download_receipt"),
    path("warranty-check/", views.warranty_check, name="warranty_check"),
    path('orders/order-attention/', views.order_attention, name='order_attention'),
    path('orders/pending-payments/',
         views.pending_payments, name='pending_payments'),
    path("orders/export/csv/", views.export_orders_csv,
         name="export_orderlist_csv"),
    path("orders/export/excel/", views.export_orders_excel,
         name="export_orderlist_excel"),
    path("orders/export/pdf/", views.export_orders_pdf,
         name="export_orderlist_pdf"),


]
