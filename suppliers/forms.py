from .models import Supplier
from django import forms


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = '__all__'
