"""
Django management command to import bulk order data
Usage: python manage.py import_bulk_orders
"""
from django.core.management.base import BaseCommand
from orders.models import Order, OrderItem
from inventory.models import Product
from django.contrib.auth.models import User
from django.utils import timezone
import csv
import random
from decimal import Decimal
from datetime import datetime


class Command(BaseCommand):
    help = 'Import bulk orders from CSV'

    def handle(self, *args, **kwargs):
        orders_file = 'generated_data/orders_bulk.csv'
        items_file = 'generated_data/order_items_bulk.csv'
        
        # Get existing users (admin, manager1, staff1)
        users = []
        for username in ['admin', 'manager1', 'staff1']:
            try:
                user = User.objects.get(username=username)
                users.append(user)
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'User {username} not found, skipping'))
        
        if not users:
            self.stdout.write(self.style.ERROR('No users found! Create admin, manager1, staff1 first'))
            return
        
        self.stdout.write(f'Using users: {[u.username for u in users]}')
        self.stdout.write('Importing orders...')
        
        # Import orders
        with open(orders_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            order_count = 0
            
            for row in reader:
                if Order.objects.filter(bill_number=row['bill_number']).exists():
                    self.stdout.write(f"  Skipped: Order {row['bill_number']} already exists")
                    continue
                order = Order(
                    bill_number=row['bill_number'],
                    customer_name=row['customer_name'],
                    customer_email=row['customer_email'],
                    customer_phonenumber=row['customer_phone'],
                    customer_address=row['customer_address'],
                    pincode=row['pincode'],
                    city=row['city'],
                    state=row['state'],
                    status=row['status'],
                    payment_status=row['payment_status'],
                    created_by=random.choice(users),
                )
                order.save()
                naive_dt = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
                aware_dt = timezone.make_aware(naive_dt)
                Order.objects.filter(pk=order.pk).update(created_at=aware_dt)
                order_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Imported {order_count} orders'))
        
        # Import order items
        self.stdout.write('Importing order items...')
        
        with open(items_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            item_count = 0
            
            for row in reader:
                try:
                    order = Order.objects.get(bill_number=f"BILL-{int(row['order_id']):05d}")
                    product = Product.objects.get(sku=row['product_sku'])

                    if OrderItem.objects.filter(order=order, product=product).exists():
                        self.stdout.write(f"  Skipped: OrderItem for {row['product_sku']} in {order.bill_number} already exists")
                        continue

                    warranty_months = int(row['warranty_months'])
                    warranty_start = None
                    warranty_end = None
                    if order.status == 'Paid':
                        from datetime import timedelta
                        warranty_start = order.created_at.date()
                        warranty_end = warranty_start + timedelta(days=30 * warranty_months)

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=int(row['quantity']),
                        price=Decimal(row['price']),
                        warranty_months=warranty_months,
                        warranty_start=warranty_start,
                        warranty_end=warranty_end,
                    )
                    item_count += 1
                except (Order.DoesNotExist, Product.DoesNotExist):
                    continue
        
        self.stdout.write(self.style.SUCCESS(f'✓ Imported {item_count} order items'))
