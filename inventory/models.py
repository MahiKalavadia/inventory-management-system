from django.db import models
from suppliers.models import Supplier
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    purchase_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    profit = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    margin_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    supplier = models.ForeignKey(
        Supplier, on_delete=models.SET_NULL, null=True)   # ✅ add this
    image = models.ImageField(
        upload_to='product_images/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    warranty_months = models.PositiveIntegerField(
        help_text="Warranty period in months")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} {self.sku}'

    def save(self, *args, **kwargs):
        if self.purchase_price and self.price:
            self.profit = self.price - self.purchase_price
            self.margin_percent = (self.profit / self.purchase_price) * 100
        super().save(*args, **kwargs)

    @property
    def profit_per_unit(self):
        if self.price and self.purchase_price:
            return self.price - self.purchase_price
        return 0

    @property
    def stock_value(self):
        if self.purchase_price and self.quantity:
            return self.purchase_price * self.quantity
        return 0


class StockLog(models.Model):
    STOCK_IN = 'IN'
    STOCK_OUT = 'OUT'

    ACTION_CHOICES = [
        (STOCK_IN, 'Stock In'),
        (STOCK_OUT, 'Stock Out'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True)
    action = models.CharField(max_length=3, choices=ACTION_CHOICES)
    quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
