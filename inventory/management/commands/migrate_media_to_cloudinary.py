from django.core.management.base import BaseCommand
from inventory.models import Product
import cloudinary.uploader
import os


class Command(BaseCommand):
    help = 'Migrate existing media images to Cloudinary'

    def handle(self, *args, **kwargs):
        products = Product.objects.exclude(image='')
        for product in products:
            if product.image and product.image.name:
                local_path = product.image.path

                if os.path.exists(local_path):
                    self.stdout.write(f"Uploading: {local_path}")

                    # Upload to Cloudinary
                    result = cloudinary.uploader.upload(local_path)

                    # Update model with Cloudinary URL
                    product.image = result['secure_url']
                    product.save()

                    self.stdout.write(
                        self.style.SUCCESS('Uploaded and updated'))
                else:
                    self.stdout.write(self.style.WARNING(
                        f"File not found: {local_path}"))
