from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from inventory.models import Product


@receiver(post_save, sender=Product)
def sync_supplier_categories_on_save(sender, instance, **kwargs):
    """Automatically add product category to supplier's categories_supplies"""
    if instance.supplier and instance.category:
        if instance.category not in instance.supplier.categories_supplies.all():
            instance.supplier.categories_supplies.add(instance.category)


@receiver(post_delete, sender=Product)
def sync_supplier_categories_on_delete(sender, instance, **kwargs):
    """Remove category from supplier if no more products in that category"""
    if instance.supplier and instance.category:
        # Check if supplier has any other products in this category
        remaining = Product.objects.filter(
            supplier=instance.supplier,
            category=instance.category
        ).exists()
        
        if not remaining:
            instance.supplier.categories_supplies.remove(instance.category)
