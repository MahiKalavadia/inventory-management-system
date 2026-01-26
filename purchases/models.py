from django.db import models
from suppliers.models import Supplier
from inventory.models import Product
# Create your models here.


class PurchaseOrder(models.Model):
    ORDER_STATUS = [
        ('Pending', 'Pending'),
        ('Received', 'Received'),
        ('Cancelled', 'Cancelled')
    ]

    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name='purchases')
    order_date = models.DateField()
    estimated_delivery = models.DateTimeField(blank=True, null=True)
    total_amount = models.DecimalField(
        max_digits=20, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20, choices=ORDER_STATUS, default='Pending')
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PO-{self.id} ({self.supplier.name})"


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_per_unit = models.DecimalField(max_digits=20, decimal_places=2)

    def total_price(self):
        return self.quantity * self.price_per_unit
