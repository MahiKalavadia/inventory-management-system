import csv
from django.core.management.base import BaseCommand
from inventory.models import Category


class Command(BaseCommand):
    help = "Import categories from CSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file",
            type=str,
            help="Path to category CSV file"
        )

    def handle(self, *args, **kwargs):
        csv_file = kwargs["csv_file"]

        with open(csv_file, newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                if not row.get("name"):
                    continue

                Category.objects.get_or_create(
                    name=row["name"].strip()
                )

        self.stdout.write(self.style.SUCCESS(
            "✅ Categories imported successfully"))
