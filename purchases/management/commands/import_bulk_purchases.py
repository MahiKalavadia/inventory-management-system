"""
Django management command to import bulk purchase requests and orders
Usage: python manage.py import_bulk_purchases
"""
from django.core.management.base import BaseCommand
from purchases.models import PurchaseRequest, PurchaseOrder
from inventory.models import Product
from suppliers.models import Supplier
from django.contrib.auth.models import User
import csv
import random
from decimal import Decimal
from datetime import datetime


class Command(BaseCommand):
    help = 'Import bulk purchase requests and orders from CSV'

    def handle(self, *args, **kwargs):
        requests_file = 'generated_data/purchase_requests_bulk.csv'
        orders_file = 'generated_data/purchase_orders_bulk.csv'
        
        # Get existing users - manager1 and staff1 can request purchases
        request_users = []
        for username in ['manager1', 'staff1']:
            try:
                user = User.objects.get(username=username)
                request_users.append(user)
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'User {username} not found'))
        
        if not request_users:
            self.stdout.write(self.style.ERROR('No users found! Create manager1, staff1 first'))
            return
        
        self.stdout.write(f'Using users for requests: {[u.username for u in request_users]}')
        
        # Import purchase requests
        self.stdout.write('Importing purchase requests...')
        
        with open(requests_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            req_count = 0
            
            for row in reader:
                try:
                    product = Product.objects.get(sku=row['product_sku'])
                    supplier = Supplier.objects.get(name=row['supplier'])
                    
                    created_at = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
                    if PurchaseRequest.objects.filter(
                        product=product, supplier=supplier,
                        quantity=int(row['quantity']), status=row['status'],
                        created_at=created_at
                    ).exists():
                        self.stdout.write(f"  Skipped: PurchaseRequest for {row['product_sku']} already exists")
                        continue

                    pr = PurchaseRequest(
                        product=product,
                        supplier=supplier,
                        description=row['description'],
                        quantity=int(row['quantity']),
                        requested_by=random.choice(request_users),
                        status=row['status']
                    )
                    pr.save()
                    PurchaseRequest.objects.filter(pk=pr.pk).update(created_at=created_at)
                    req_count += 1
                except (Product.DoesNotExist, Supplier.DoesNotExist):
                    continue
        
        self.stdout.write(self.style.SUCCESS(f'✓ Imported {req_count} purchase requests'))
        
        # Import purchase orders
        self.stdout.write('Importing purchase orders...')
        
        with open(orders_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            po_count = 0
            linked_requests = set()  # Track which requests already have POs
            
            for row in reader:
                try:
                    supplier = Supplier.objects.get(name=row['supplier'])
                    
                    # Link to request if exists and not already linked
                    request = None
                    if row['request_id']:
                        product = Product.objects.get(sku=row['product_sku'])
                        requests = PurchaseRequest.objects.filter(
                            product=product,
                            supplier=supplier,
                            quantity=int(row['quantity']),
                            status='Approved'
                        ).exclude(id__in=linked_requests)  # Exclude already linked
                        
                        if requests.exists():
                            request = requests.first()
                            linked_requests.add(request.id)  # Mark as linked
                    
                    created_at = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
                    if PurchaseOrder.objects.filter(
                        supplier=supplier, status=row['status'],
                        total_cost=Decimal(row['total_cost']), created_at=created_at
                    ).exists():
                        self.stdout.write(f"  Skipped: PurchaseOrder for {row['supplier']} already exists")
                        continue

                    po = PurchaseOrder(
                        request=request,
                        supplier=supplier,
                        status=row['status'],
                        expected_delivery=datetime.strptime(row['expected_delivery'], '%Y-%m-%d').date() if row['expected_delivery'] else None,
                        actual_delivery=datetime.strptime(row['actual_delivery'], '%Y-%m-%d').date() if row['actual_delivery'] else None,
                        total_cost=Decimal(row['total_cost'])
                    )
                    po.save()
                    PurchaseOrder.objects.filter(pk=po.pk).update(created_at=created_at)
                    po_count += 1
                except (Supplier.DoesNotExist, Product.DoesNotExist):
                    continue
        
        self.stdout.write(self.style.SUCCESS(f'✓ Imported {po_count} purchase orders'))
