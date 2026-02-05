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

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
    ]

    title = models.CharField(max_length=255, default="Notification")
    message = models.TextField()
    type = models.CharField(
        max_length=10, choices=TYPE_CHOICES, default='info')

    role_target = models.CharField(
        max_length=10, choices=ROLE_CHOICES, default='Staff')
    user_target = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.CASCADE)

    link = models.CharField(max_length=255, blank=True, null=True)
    notification_type = models.CharField(
        max_length=20, choices=NOTIFY_CHOICES, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
