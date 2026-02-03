from django import forms
from .models import PurchaseRequest, PurchaseOrder


class PurchaseRequestForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequest
        fields = ['product', 'supplier', 'quantity']


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['expected_delivery']
