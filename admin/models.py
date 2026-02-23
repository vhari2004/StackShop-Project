from django.db import models
from seller.models import Product,SellerProfile
from customer.models import OrderItem
from core.models import Category

class Offer(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

class Discount(models.Model):
    name = models.CharField(max_length=100)
    discount_type = models.CharField(max_length=20)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.IntegerField()
    used_count = models.IntegerField(default=0)

class OfferDiscountBridge(models.Model):
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)
    discount = models.ForeignKey(Discount, on_delete=models.CASCADE)

class ProductOfferBridge(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)

class CategoryOfferBridge(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)

class ProductDiscountBridge(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    discount = models.ForeignKey(Discount, on_delete=models.CASCADE)

class CategoryDiscountBridge(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    discount = models.ForeignKey(Discount, on_delete=models.CASCADE)

class PlatformCommission(models.Model):
    seller = models.ForeignKey(SellerProfile, on_delete=models.CASCADE)
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE)
    commission_percentage = models.FloatField()
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    settlement_status = models.CharField(max_length=20)
    settled_at = models.DateTimeField(null=True, blank=True)