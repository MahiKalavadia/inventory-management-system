"""
Django management command to import bulk stock logs
Usage: python manage.py import_bulk_stocklogs
"""
from django.core.management.base import BaseCommand
from inventory.models import Product, StockLog
from django.contrib.auth.models import User
import csv
import random
from django.utils import timezone


class Command(BaseCommand):
    help = 'Import bulk stock logs from CSV'

    def handle(self, *args, **kwargs):
        csv_file = 'generated_data/stock_logs_bulk.csv'

        users = []
        for username in ['admin', 'manager1', 'staff1']:
            try:
                users.append(User.objects.get(username=username))
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
                    created_at = timezone.make_aware(
                        timezone.datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S')
                    )

                    # created_at uses auto_now_add so filter by it after update
                    if StockLog.objects.filter(
                        product=product,
                        action=row['action'],
                        quantity=int(row['quantity']),
                        created_at=created_at
                    ).exists():
                        self.stdout.write(f"  Skipped: StockLog for {row['product_sku']} already exists")
                        continue

                    # Save first, then update created_at to bypass auto_now_add
                    log = StockLog(
                        product=product,
                        user=random.choice(users),
                        action=row['action'],
                        quantity=int(row['quantity']),
                    )
                    log.save()
                    StockLog.objects.filter(pk=log.pk).update(created_at=created_at)
                    count += 1
                except Product.DoesNotExist:
                    continue

        self.stdout.write(self.style.SUCCESS(f'✓ Imported {count} stock logs'))
