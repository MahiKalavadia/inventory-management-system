from django.db import models


class SystemSettings(models.Model):
    # ================= GENERAL / BUSINESS INFO =================
    company_name = models.CharField(
        max_length=200, default='Smart Inventory System')
    company_address = models.TextField(
        default='Surat, Gujarat, India')
    company_phone = models.CharField(
        max_length=20, default='+91 9876543210')
    company_email = models.EmailField(
        default='support@smartinventory.com')
    currency_symbol = models.CharField(
        max_length=5, default='\u20b9')

    # ================= INVENTORY SETTINGS =================
    low_stock_threshold = models.PositiveIntegerField(default=5)
    default_warranty_months = models.PositiveIntegerField(default=12)
    items_per_page = models.PositiveIntegerField(default=10)

    # ================= NOTIFICATION SETTINGS =================
    notification_retention_days = models.PositiveIntegerField(default=15)
    enable_product_notifications = models.BooleanField(default=True)
    enable_stock_notifications = models.BooleanField(default=True)
    enable_order_notifications = models.BooleanField(default=True)
    enable_supplier_notifications = models.BooleanField(default=True)
    enable_category_notifications = models.BooleanField(default=True)
    enable_purchase_notifications = models.BooleanField(default=True)

    # ================= WAREHOUSE / PURCHASE SETTINGS =================
    default_warehouse_address = models.TextField(
        default='Ahmedabad, Gujarat')
    default_supplier_lead_days = models.PositiveIntegerField(default=7)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'System Settings'
        verbose_name_plural = 'System Settings'

    def __str__(self):
        return 'System Settings'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
