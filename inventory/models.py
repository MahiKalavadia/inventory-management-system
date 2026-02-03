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
    price = models.DecimalField(max_digits=10, decimal_places=2)
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
