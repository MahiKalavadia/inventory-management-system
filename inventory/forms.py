from django import forms
from .models import Product, Category


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'   # or list fields explicitly


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'


class StockForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True),
        empty_label='Select Product'
    )
    quantity = forms.IntegerField(min_value=1)
