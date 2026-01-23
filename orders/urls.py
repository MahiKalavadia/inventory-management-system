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
    path("receipt/<int:pk>/download/",
         views.download_receipt, name="download_receipt"),
]
