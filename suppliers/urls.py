from django.urls import path
from .views import supplier_list, supplier_dashboard, add_supplier, update_supplier, delete_supplier, active_supplier, inactive_supplier, toggle_supplier_status, suppliers_by_value, export_supplier_csv, export_supplier_excel, export_supplier_pdf

urlpatterns = [
    path('suppliers/dashboard/', supplier_dashboard, name="supplier_dashboard"),
    path('suppliers/list/', supplier_list, name='supplier_list'),
    path('suppliers/active', active_supplier, name="active_supplier"),
    path('suppliers/inactive', inactive_supplier, name="inactive_supplier"),
    path('supplier/toggle_supplier_status/<int:pk>/',
         toggle_supplier_status, name="toggle_supplier_status"),
    path('suppliers/add/', add_supplier, name='add_supplier'),
    path('suppliers/update/<int:pk>/', update_supplier, name='update_supplier'),
    path('suppliers/delete/<int:pk>/', delete_supplier, name='delete_supplier'),
    path("suppliers/suppliers_by_value/",
         suppliers_by_value, name="suppliers_by_value"),
    path('supplier/export/csv', export_supplier_csv, name="export_supplier_csv"),
    path('supplier/export/excel', export_supplier_excel,
         name="export_supplier_excel"),
    path('supplier/export/pdf', export_supplier_pdf, name="export_supplier_pdf"),
]
