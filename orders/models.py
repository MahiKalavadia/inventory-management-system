from django.db import models
from inventory.models import Product
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone
from django.db.models import Max
# Create your models here.


class Order(models.Model):
    STATUS_CHOICES = [
        ("Draft", "Draft"),
        ("Confirmed", "Confirmed"),
        ("Paid", "Paid"),
        ("Cancelled", "Cancelled"),
    ]

    PAYMENT_STATUS = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
    ]

    INDIAN_STATES = [
        ('AN', 'Andaman and Nicobar Islands'),
        ('AP', 'Andhra Pradesh'),
        ('AR', 'Arunachal Pradesh'),
        ('AS', 'Assam'),
        ('BR', 'Bihar'),
        ('CH', 'Chandigarh'),
        ('CT', 'Chhattisgarh'),
        ('DN', 'Dadra and Nagar Haveli and Daman and Diu'),
        ('DL', 'Delhi'),
        ('GA', 'Goa'),
        ('GJ', 'Gujarat'),
        ('HR', 'Haryana'),
        ('HP', 'Himachal Pradesh'),
        ('JH', 'Jharkhand'),
        ('KA', 'Karnataka'),
        ('KL', 'Kerala'),
        ('LA', 'Ladakh'),
        ('MP', 'Madhya Pradesh'),
        ('MH', 'Maharashtra'),
        ('MN', 'Manipur'),
        ('ML', 'Meghalaya'),
        ('MZ', 'Mizoram'),
        ('NL', 'Nagaland'),
        ('OD', 'Odisha'),
        ('PB', 'Punjab'),
        ('RJ', 'Rajasthan'),
        ('SK', 'Sikkim'),
        ('TN', 'Tamil Nadu'),
        ('TS', 'Telangana'),
        ('TR', 'Tripura'),
        ('UP', 'Uttar Pradesh'),
        ('UK', 'Uttarakhand'),
        ('WB', 'West Bengal'),
    ]

    # Cuustomer details
    bill_number = models.CharField(max_length=20, unique=True, blank=True)
    customer_name = models.CharField(max_length=200, null=False)
    customer_email = models.EmailField()
    customer_phonenumber = models.CharField(max_length=25)
    customer_address = models.TextField(default=None)
    pincode = models.CharField(max_length=6)
    city = models.CharField(max_length=20, default='Surat')
    state = models.CharField(
        max_length=30, choices=INDIAN_STATES, default='GJ')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='Draft')
    payment_status = models.CharField(
        max_length=10, choices=PAYMENT_STATUS, default='Pending'
    )

    @property
    def total_amount(self):
        return sum(item.total for item in self.items.all())

    def __str__(self):
        return f'Order {self.id}-{self.customer_name}'

    def save(self, *args, **kwargs):
        if not self.bill_number:
            # Get the last bill number
            last_order = Order.objects.order_by('-id').first()
            
            if last_order and last_order.bill_number:
                # Extract number from BILL-00001 format
                last_num = int(last_order.bill_number.split('-')[1])
                self.bill_number = f"BILL-{last_num + 1:05d}"
            else:
                self.bill_number = "BILL-00001"

        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items'
    )
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # ✅ Warranty snapshot
    warranty_months = models.PositiveIntegerField(default=0)
    warranty_start = models.DateField(null=True, blank=True)
    warranty_end = models.DateField(null=True, blank=True)

    @property
    def total(self):
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        # 1️⃣ Set price automatically
        if not self.price and self.product:
            self.price = self.product.price

        # 2️⃣ Copy warranty from product ONLY once
        if not self.pk and self.product:
            self.warranty_months = self.product.warranty_months

        # 3️⃣ Start warranty when order is PAID
        if self.order.status == "Paid" and not self.warranty_start:
            self.warranty_start = timezone.now().date()
            self.warranty_end = self.warranty_start + timedelta(
                days=30 * self.warranty_months
            )

        super().save(*args, **kwargs)

    def is_under_warranty(self):
        return (
            self.warranty_end is not None and
            timezone.now().date() <= self.warranty_end
        )
