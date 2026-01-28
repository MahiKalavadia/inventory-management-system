from django.db import models
from inventory.models import Product
from django.contrib.auth.models import User
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
            last_id = Order.objects.count() + 1
            self.bill_number = f"BILL-{last_id:05d}"
        super().save(*args, **kwargs)

# ✅ STEP 2 — Why This Matters
# Status	Meaning
# Draft	Bill being prepared
# Confirmed	Order finalized
# Paid	Money received
# Cancelled	Reversed


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total(self):
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.product.price
        super().save(*args, **kwargs)
