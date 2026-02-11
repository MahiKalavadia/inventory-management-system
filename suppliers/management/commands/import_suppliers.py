import csv
from django.core.management.base import BaseCommand
from suppliers.models import Supplier
from inventory.models import Category


class Command(BaseCommand):
    help = "Import suppliers from CSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file",
            type=str,
            help="Path to supplier CSV file"
        )

    def handle(self, *args, **kwargs):
        csv_file = kwargs["csv_file"]

        with open(csv_file, newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                if not row.get("name"):
                    continue

                supplier, created = Supplier.objects.update_or_create(
                    name=row["name"].strip(),
                    defaults={
                        "contact_person": row.get("contact_person", "").strip(),
                        "phone": row.get("phone", "").strip(),
                        "email": row.get("email", "").strip() or None,
                        "address": row.get("address", "").strip(),
                        "is_active": True
                    }
                )

                # ManyToMany Categories
                categories_raw = row.get("categories", "")
                if categories_raw:
                    category_names = [c.strip()
                                      for c in categories_raw.split("|")]
                    category_objs = []

                    for cname in category_names:
                        category, _ = Category.objects.get_or_create(
                            name=cname)
                        category_objs.append(category)

                    supplier.categories_supplies.set(category_objs)

        self.stdout.write(self.style.SUCCESS(
            "✅ Suppliers imported successfully"))
