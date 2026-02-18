from django.db import models
from django.contrib.auth import get_user_model
from inventory.models import Product
from suppliers.models import Supplier

User = get_user_model()


def get_default_warehouse_address():
    try:
        from settings_app.models import SystemSettings
        return SystemSettings.load().default_warehouse_address
    except Exception:
        return 'Ahmedabad, Gujarat'


class PurchaseRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE)
    description = models.CharField(max_length=500, default='None')
    quantity = models.PositiveIntegerField()
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.name} - {self.status}"


class PurchaseOrder(models.Model):
    request = models.OneToOneField(
        PurchaseRequest, on_delete=models.SET_NULL, null=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)

    STATUS = [
        ('draft', 'draft'),
        ('ordered', 'Ordered'),
        ('shipped', 'Shipped'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('delayed', 'Delayed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    expected_delivery = models.DateField(null=True, blank=True)
    actual_delivery = models.DateField(null=True, blank=True)
    warehouse_address = models.TextField(default='Ahmedabad, Gujarat')

    total_cost = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PO-{self.id} for {self.request.product.name}"
