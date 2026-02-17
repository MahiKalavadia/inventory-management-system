from django import forms
from .models import PurchaseRequest, PurchaseOrder


class PurchaseRequestForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequest
        fields = ['product', 'supplier', 'quantity']


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = [
            "status",
            "expected_delivery",]
        widgets = {
            "expected_delivery": forms.DateInput(attrs={'type': 'Date'}),
        }
