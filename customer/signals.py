from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Review
from seller.models import Product

@receiver(post_save, sender=Review)
def update_review_count_on_save(sender, instance, created, **kwargs):
    """Update review count when a review is created or updated"""
    if created:
        # New review added
        instance.product.review_count += 1
        instance.product.save(update_fields=['review_count'])

@receiver(post_delete, sender=Review)
def update_review_count_on_delete(sender, instance, **kwargs):
    """Update review count when a review is deleted"""
    if instance.product.review_count > 0:
        instance.product.review_count -= 1
        instance.product.save(update_fields=['review_count'])