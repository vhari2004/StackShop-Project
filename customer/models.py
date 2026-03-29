from django.db import models
class Cart(models.Model):
    user = models.OneToOneField("core.CustomUser", on_delete=models.CASCADE, related_name="cart")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.user.username}'s Cart"
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("seller.ProductVariant", on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price_at_time = models.FloatField(default=0.0, null=True, blank=True)
    def __str__(self):
        return f"{self.quantity} x {self.variant.product.name} in {self.cart.user.username}'s cart"
    def get_total(self):
        return self.quantity * self.price_at_time
    

class Wishlist(models.Model):
    user = models.ForeignKey("core.CustomUser", on_delete=models.CASCADE, related_name="wishlists")
    wishlist_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    is_default = models.BooleanField(default=False)
    def save(self, *args, **kwargs):
        if self.is_default:
            Wishlist.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.wishlist_name} ({self.user.username})"
    

class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("seller.ProductVariant", on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.variant.product.name} in {self.wishlist.wishlist_name}"

class Review(models.Model):
    user = models.ForeignKey("core.CustomUser", on_delete=models.CASCADE)
    product = models.ForeignKey("seller.Product", on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()
    seller_reply = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        indexes = [
            models.Index(fields=['product']),
        ]

    def __str__(self):
        return f"{self.user.username} review for {self.product.name} ({self.rating})"

    @classmethod
    def can_user_review(cls, user, product):
        from customer.models import OrderItem

        if not user.is_authenticated:
            return False

        return OrderItem.objects.filter(
            order__user=user,
            variant__product=product,
            order__payment_status__in=["SUCCESS", "CONFIRMED", "DELIVERED"],
        ).exists()

    @classmethod
    def get_user_review(cls, user, product):
        if not user.is_authenticated:
            return None
        return cls.objects.filter(user=user, product=product).first()

class Order(models.Model):
    PAYMENT_CHOICES = [
        ('online', 'Online Payment'),
        ('cod', 'Cash on Delivery'),
    ]
    
    user = models.ForeignKey("core.CustomUser", on_delete=models.CASCADE, related_name="orders")
    address = models.ForeignKey("core.Address", on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    order_number = models.CharField(max_length=100, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='online')
    payment_status = models.CharField(max_length=20)
    order_status = models.CharField(max_length=20)
    ordered_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return(f"{self.order_number}")

class OrderItem(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("cancelled", "Cancelled"),
        ("delivered", "Delivered"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("seller.ProductVariant", on_delete=models.CASCADE)
    seller = models.ForeignKey("seller.SellerProfile", on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    def __str__(self):
        return f"{self.variant} - {self.status}"
    
class PaymentOrder(models.Model):
    order = models.OneToOneField("Order",on_delete=models.CASCADE,related_name="payment")
    user = models.ForeignKey("core.CustomUser", on_delete=models.CASCADE, related_name="payment_orders", null=True, blank=True)
    amount = models.IntegerField()
    razorpay_order_id = models.CharField(max_length=200)
    razorpay_payment_id = models.CharField(max_length=200, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=500, blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=[("PENDING","Pending"),("SUCCESS","Success")],
        default="PENDING"
    )

    created_at = models.DateTimeField(auto_now_add=True)


class ReactivationRequest(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    user = models.ForeignKey("core.CustomUser", on_delete=models.CASCADE, related_name="reactivation_requests")
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    admin_notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.user.username} reactivation request ({self.status})"
# Create your models here.
