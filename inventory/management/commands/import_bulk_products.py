"""
Django management command to import bulk product data
Usage: python manage.py import_bulk_products
"""
from django.core.management.base import BaseCommand
from inventory.models import Product, Category
from suppliers.models import Supplier
import csv
from decimal import Decimal


class Command(BaseCommand):
    help = 'Import bulk products from CSV'

    def handle(self, *args, **kwargs):
        csv_file = 'generated_data/products_bulk.csv'
        
        self.stdout.write('Importing products...')
        
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            count = 0
            errors = 0
            
            for idx, row in enumerate(reader, start=2):  # start=2 because row 1 is header
                try:
                    # Skip empty rows
                    if not row.get('sku') or not row.get('name'):
                        continue
                    
                    # Get or create category
                    category, _ = Category.objects.get_or_create(name=row['category'].strip())
                    
                    # Get or create supplier
                    supplier, _ = Supplier.objects.get_or_create(
                        name=row['supplier'].strip(),
                        defaults={
                            'contact_person': 'Contact Person',
                            'phone': '9876543210',
                            'email': f"{row['supplier'].lower().replace(' ', '')}@email.com",
                            'address': 'India'
                        }
                    )
                    
                    # Create product if doesn't exist
                    if not Product.objects.filter(sku=row['sku'].strip()).exists():
                        Product.objects.create(
                            sku=row['sku'].strip(),
                            name=row['name'].strip(),
                            brand=row['brand'].strip(),
                            purchase_price=Decimal(row['purchase_price'].strip()),
                            price=Decimal(row['price'].strip()),
                            quantity=int(row['quantity'].strip()),
                            category=category,
                            supplier=supplier,
                            description=row['description'].strip(),
                            warranty_months=int(row['warranty_months'].strip()),
                            is_active=True
                        )
                        count += 1
                except Exception as e:
                    errors += 1
                    self.stdout.write(self.style.ERROR(f'Error on row {idx}: {e}'))
                    self.stdout.write(self.style.ERROR(f'Row data: {row}'))
                    if errors > 5:  # Stop after 5 errors to avoid spam
                        self.stdout.write(self.style.ERROR('Too many errors, stopping...'))
                        break
        
        self.stdout.write(self.style.SUCCESS(f'✓ Imported {count} products ({errors} errors)'))
