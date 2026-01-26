from django.urls import path
from . import views

urlpatterns = [
    path('purchase/dashboard/', views.purchase_dashboard,
         name='purchase_dashboard'),
    path('purchase/list/', views.purchase_list, name="purchase_list"),
    path('purchase/detail/<int:pk>/',
         views.purchase_detail, name="purchase_detail"),
    path('purchase/create-purchase/',
         views.create_purchase, name='create_purchase'),
    path('purchase/update/<int:pk>/', views.edit_purchase, name='edit_purchase'),
    path('purchase/delete/<int:pk>/',
         views.delete_purchase, name='delete_purchase'),
]
