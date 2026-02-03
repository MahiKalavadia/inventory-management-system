import csv
from django.core.management.base import BaseCommand
from inventory.models import Product, Category, Supplier


class Command(BaseCommand):
    help = "Import products from CSV (Excel exported)"

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to CSV file'
        )

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']

        with open(csv_file, newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                # Skip empty rows
                if not row.get('sku'):
                    continue

                # CATEGORY
                category, _ = Category.objects.get_or_create(
                    name=row['category'].strip()
                )

                # SUPPLIER
                supplier = None
                if row.get('supplier'):
                    supplier, _ = Supplier.objects.get_or_create(
                        name=row['supplier'].strip()
                    )

                # WARRANTY (SAFE EVEN IF COLUMN NOT PRESENT)
                warranty_value = row.get('warranty')
                if warranty_value:
                    warranty_value = warranty_value.strip()

                # CREATE or UPDATE PRODUCT
                Product.objects.update_or_create(
                    sku=row['sku'].strip(),
                    defaults={
                        'name': row['name'].strip(),
                        'brand': row['brand'].strip(),
                        'price': row['price'],
                        'quantity': int(row['quantity']),
                        'category': category,
                        'supplier': supplier,
                        'description': row.get('description', '').strip(),
                        'warranty': warranty_value  # 👈 NEW FIELD
                    }
                )

        self.stdout.write(
            self.style.SUCCESS("✅ Products imported/updated successfully")
        )
