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
    bank_account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20)
    business_address = models.TextField()
    rating = models.FloatField(default=0)
    verification_status = models.CharField(max_length=10,choices=STATUS_CHOICES,default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    store_image=models.ImageField(upload_to='sellerprofile_image')
    def __str__(self):
        return self.store_name
    def save(self, *args, **kwargs):
        if not self.store_slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.store_slug = slug

        super().save(*args, **kwargs)
class Product(models.Model):
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
    approval_status = models.CharField(max_length=20, default='PENDING')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name
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
    mrp = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
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

    def __str__(self):
        return f"{self.product.name} - {self.sku_code}"
    
class ProductImage(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="images")
    image_url = models.ImageField(upload_to='product_images/', blank=True, null=True)
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    def __str__(self):
        return f"Image for {self.variant.product.name} ({'Primary' if self.is_primary else 'Secondary'})"

class Attribute(models.Model):
    name = models.CharField(max_length=100)
    subcategory = models.ForeignKey(SubCategory,on_delete=models.CASCADE,related_name="attributes",null=True,blank=True)
    
    

class AttributeOption(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="options")
    value = models.CharField(max_length=100)

class VariantAttributeBridge(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    option = models.ForeignKey(AttributeOption, on_delete=models.CASCADE)

class InventoryLog(models.Model):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    change_amount = models.IntegerField()
    reason = models.CharField(max_length=50)
    performed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
# Create your models here.
