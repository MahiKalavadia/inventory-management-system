from django import forms
from .models import Order, OrderItem
from django.forms import modelformset_factory
from inventory.models import Product


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'customer_name', 'customer_email', 'customer_phonenumber',
            'customer_address', 'city', 'state', 'pincode', 'status', 'payment_status'
        ]
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'state': forms.Select(attrs={'class': 'form-select'}),
        }


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 👇 THIS LINE FILTERS OUT OUT-OF-STOCK PRODUCTS
        self.fields['product'].queryset = Product.objects.filter(
            quantity__gt=0,
            is_active=True
        )
