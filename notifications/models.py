from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):

    NOTIFY_CHOICES = [
        ('product', 'Product Activity'),
        ('category', 'Category Activity'),
        ('supplier', 'Supplier Activity'),
        ('stock', 'Stock Activity'),
        ('purchase', 'Purchase Activity'),
        ('order', 'Order Activity'),
    ]

    TYPE_CHOICES = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('danger', 'Danger'),
    ]

    title = models.CharField(max_length=255, default="Notification")
    message = models.TextField()
    type = models.CharField(
        max_length=10, choices=TYPE_CHOICES, default='info')

    notification_type = models.CharField(max_length=20, choices=NOTIFY_CHOICES)

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)

    allowed_roles = models.CharField(max_length=100)  # 🔥 IMPORTANT

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
