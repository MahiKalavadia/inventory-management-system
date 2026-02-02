from django.contrib import admin
from .models import PurchaseRequest


@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'requested_by',
                    'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('product__name', 'requested_by__username')
