from django import forms
from .models import Product, Category
from settings_app.models import SystemSettings


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product
        exclude = ['profit', 'margin_percent', 'is_active', 'created_at']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Pre-fill warranty_months from system settings only on new product
        if not self.instance.pk:
            try:
                default_warranty = SystemSettings.load().default_warranty_months
            except Exception:
                default_warranty = 12
            self.fields['warranty_months'].initial = default_warranty

        # Make purchase_price and price clearly labeled
        self.fields['purchase_price'].help_text = 'Cost price you paid to the supplier'
        self.fields['price'].help_text = 'Selling price to the customer'
        self.fields['warranty_months'].help_text = 'Warranty period in months (auto-filled from system default, editable)'

        # Mark profit/margin as not required since they're auto-calculated
        self.fields['purchase_price'].required = False


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
