from django.db import models
from core.models import CustomUser,SubCategory
from django.utils.text import slugify
import uuid

class SellerProfile(models.Model):
    STATUS_CHOICES=(('pending','PENDING'),
                    ('approved','APPROVED'),
                    ('rejected','REJECTED'))
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="seller_profile")
    store_name = models.CharField(max_length=255)
    store_slug = models.SlugField(unique=True)
    gst_number = models.CharField(max_length=50)
    pan_number = models.CharField(max_length=50)
    bank_account_number = models.CharField(max_length=50,null=True)
    ifsc_code = models.CharField(max_length=20,null=True)
    business_address = models.TextField(max_length=200,null=True)
    description=models.TextField(max_length=200,null=True,blank=True)
    rating = models.FloatField(default=0)
    verification_status = models.CharField(max_length=10,choices=STATUS_CHOICES,default='pending')
    admin_remarks = models.TextField(blank=True, null=True, help_text="Admin remarks for seller verification")
    created_at = models.DateTimeField(auto_now_add=True)
    store_image=models.ImageField(upload_to='sellerprofile_image')
    
    class Meta:
        verbose_name = "Seller Profile"
        verbose_name_plural = "Seller Profiles"
        indexes = [
            models.Index(fields=['verification_status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['store_slug']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return self.store_name
    def save(self, *args, **kwargs):
        if not self.store_slug:
            base_slug = slugify(self.store_name)
            slug = base_slug
            counter = 1

            while SellerProfile.objects.filter(store_slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.store_slug = slug

        super().save(*args, **kwargs)
class Product(models.Model):
    product_choices=(('pending','PENDING'),
                    ('approved','APPROVED'),
                    ('rejected','REJECTED'))
    seller = models.ForeignKey(SellerProfile, on_delete=models.CASCADE, related_name="products")
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField()
    brand = models.CharField(max_length=100)
    model_number = models.CharField(max_length=100)
    is_cancellable = models.BooleanField(default=True)
    is_returnable = models.BooleanField(default=True)
    return_days = models.IntegerField(default=7)
    approval_status = models.CharField(max_length=20,choices=product_choices,default='pending')
    admin_remarks = models.TextField(blank=True, null=True, help_text="Admin remarks for product approval/rejection")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        indexes = [
            models.Index(fields=['approval_status']),
            models.Index(fields=['seller', 'approval_status']),
            models.Index(fields=['subcategory', 'is_active']),
            models.Index(fields=['slug']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_active']),
        ]
        unique_together = [['slug', 'seller']]
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

    @property
    def min_variant_price(self):
        variant = self.variants.order_by('selling_price').first()
        return variant.selling_price if variant else 0

    @property
    def max_variant_price(self):
        variant = self.variants.order_by('-selling_price').first()
        return variant.selling_price if variant else 0

    @property
    def total_stock(self):
        return self.variants.aggregate(models.Sum('stock_quantity'))['stock_quantity__sum'] or 0

    @property
    def display_image(self):
        variant = self.variants.filter(images__is_primary=True).prefetch_related('images').first() or self.variants.prefetch_related('images').first()
        if variant and variant.images.first():
            return variant.images.first().image_url.url
        return None

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku_code = models.CharField(max_length=100, unique=True, blank=True)
    mrp = models.FloatField()
    selling_price = models.FloatField()
    cost_price = models.FloatField()
    stock_quantity = models.IntegerField()
    weight = models.FloatField()
    length = models.FloatField()
    width = models.FloatField()
    height = models.FloatField()
    tax_percentage = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_sku(self):

        product_slug = slugify(self.product.name).upper().replace("-", "")[:10]
        unique_id = uuid.uuid4().hex[:6].upper()
        return f"{product_slug}-{unique_id}"

    def save(self, *args, **kwargs):
        if not self.sku_code:
            sku = self.generate_sku()

            # handle duplicates
            while ProductVariant.objects.filter(sku_code=sku).exists():
                sku = self.generate_sku()

            self.sku_code = sku
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Product Variant"
        verbose_name_plural = "Product Variants"
        indexes = [
            models.Index(fields=['sku_code']),
            models.Index(fields=['product']),
            models.Index(fields=['created_at']),
            models.Index(fields=['stock_quantity']),
        ]
        ordering = ['product', '-created_at']

    def __str__(self):
        return f"{self.product.name} - {self.sku_code}"
    
class ProductImage(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="images")
    image_url = models.ImageField(upload_to='product_images/', blank=True, null=True)
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"
        indexes = [
            models.Index(fields=['variant']),
            models.Index(fields=['is_primary']),
        ]
        ordering = ['-is_primary', 'id']
    
    def __str__(self):
        return f"Image for {self.variant.product.name} ({'Primary' if self.is_primary else 'Secondary'})"

class Attribute(models.Model):
    name = models.CharField(max_length=100)
    subcategory = models.ForeignKey(SubCategory,on_delete=models.CASCADE,related_name="attributes",null=True,blank=True)
    
    class Meta:
        verbose_name = "Attribute"
        verbose_name_plural = "Attributes"
        indexes = [
            models.Index(fields=['subcategory']),
        ]
    
    def __str__(self):
        return self.name


class AttributeOption(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="options")
    value = models.CharField(max_length=100)
    
    class Meta:
        verbose_name = "Attribute Option"
        verbose_name_plural = "Attribute Options"
        indexes = [
            models.Index(fields=['attribute']),
        ]
        unique_together = [['attribute', 'value']]
    
    def __str__(self):
        return f"{self.attribute.name}: {self.value}"

class VariantAttributeBridge(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="attributes")
    option = models.ForeignKey(AttributeOption, on_delete=models.CASCADE, related_name="variants")
    
    class Meta:
        verbose_name = "Variant Attribute"
        verbose_name_plural = "Variant Attributes"
        unique_together = [['variant', 'option']]
        indexes = [
            models.Index(fields=['variant']),
            models.Index(fields=['option']),
        ]
    
    def __str__(self):
        return f"{self.variant} - {self.option}"


class InventoryLog(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="inventory_logs")
    change_amount = models.IntegerField()
    reason = models.CharField(max_length=50)
    performed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="inventory_changes")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Inventory Log"
        verbose_name_plural = "Inventory Logs"
        indexes = [
            models.Index(fields=['variant']),
            models.Index(fields=['created_at']),
            models.Index(fields=['performed_by']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Inventory change for {self.variant.sku_code}: {self.change_amount} ({self.reason})"
# Create your models here.
