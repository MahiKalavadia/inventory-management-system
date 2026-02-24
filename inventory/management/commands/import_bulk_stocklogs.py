"""
Django management command to import bulk stock logs
Usage: python manage.py import_bulk_stocklogs
"""
from django.core.management.base import BaseCommand
from inventory.models import Product, StockLog
from django.contrib.auth.models import User
import csv
import random
from datetime import datetime


class Command(BaseCommand):
    help = 'Import bulk stock logs from CSV'

    def handle(self, *args, **kwargs):
        csv_file = 'generated_data/stock_logs_bulk.csv'
        
        # Get existing users
        users = []
        for username in ['admin', 'manager1', 'staff1']:
            try:
                user = User.objects.get(username=username)
                users.append(user)
            except User.DoesNotExist:
                pass
        
        if not users:
            self.stdout.write(self.style.ERROR('No users found!'))
            return
        
        self.stdout.write(f'Using users: {[u.username for u in users]}')
        self.stdout.write('Importing stock logs...')
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            
            for row in reader:
                try:
                    product = Product.objects.get(sku=row['product_sku'])
                    
                    StockLog.objects.create(
                        product=product,
                        user=random.choice(users),  # Random user
                        action=row['action'],
                        quantity=int(row['quantity']),
                        created_at=datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
                    )
                    count += 1
                except Product.DoesNotExist:
                    continue
        
        self.stdout.write(self.style.SUCCESS(f'✓ Imported {count} stock logs'))
