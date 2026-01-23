from django.urls import path
from .views import supplier_list, supplier_dashboard, add_supplier, update_supplier, delete_supplier

urlpatterns = [
    path('suppliers/dashboard/', supplier_dashboard, name="supplier_dashboard"),
    path('suppliers/list/', supplier_list, name='supplier_list'),
    path('suppliers/add/', add_supplier, name='add_supplier'),
    path('suppliers/update/<int:pk>/', update_supplier, name='update_supplier'),
    path('suppliers/delete/<int:pk>/', delete_supplier, name='delete_supplier'),
]
