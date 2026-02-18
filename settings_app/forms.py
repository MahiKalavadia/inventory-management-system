from django import forms
from .models import SystemSettings


class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        exclude = ['updated_at']
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. Smart Inventory System'}),
            'company_address': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2, 'placeholder': 'e.g. Surat, Gujarat, India'}),
            'company_phone': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. +91 9876543210'}),
            'company_email': forms.EmailInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. support@company.com'}),
            'currency_symbol': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g. \u20b9'}),
            'low_stock_threshold': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 1}),
            'default_warranty_months': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 0}),
            'items_per_page': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 5, 'max': 100}),
            'notification_retention_days': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 1}),
            'enable_product_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input', 'role': 'switch'}),
            'enable_stock_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input', 'role': 'switch'}),
            'enable_order_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input', 'role': 'switch'}),
            'enable_supplier_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input', 'role': 'switch'}),
            'enable_category_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input', 'role': 'switch'}),
            'enable_purchase_notifications': forms.CheckboxInput(attrs={
                'class': 'form-check-input', 'role': 'switch'}),
            'default_warehouse_address': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 2, 'placeholder': 'e.g. Ahmedabad, Gujarat'}),
            'default_supplier_lead_days': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 1}),
        }
        labels = {
            'company_name': 'Company Name',
            'company_address': 'Company Address',
            'company_phone': 'Phone Number',
            'company_email': 'Email Address',
            'currency_symbol': 'Currency Symbol',
            'low_stock_threshold': 'Low Stock Threshold',
            'default_warranty_months': 'Default Warranty (months)',
            'items_per_page': 'Items Per Page',
            'notification_retention_days': 'Auto-Delete After (days)',
            'enable_product_notifications': 'Product Notifications',
            'enable_stock_notifications': 'Stock Notifications',
            'enable_order_notifications': 'Order Notifications',
            'enable_supplier_notifications': 'Supplier Notifications',
            'enable_category_notifications': 'Category Notifications',
            'enable_purchase_notifications': 'Purchase Notifications',
            'default_warehouse_address': 'Default Warehouse Address',
            'default_supplier_lead_days': 'Default Supplier Lead Time (days)',
        }
        help_texts = {
            'low_stock_threshold': 'Products with quantity at or below this will be flagged as low stock',
            'notification_retention_days': 'Read notifications older than this will be auto-deleted',
            'items_per_page': 'Number of items shown per page in lists and tables',
            'default_supplier_lead_days': 'Expected number of days for supplier deliveries',
        }
