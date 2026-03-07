from django.db import models
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
class CustomUser(AbstractUser):
    ROLE_CHOICES=(('ADMIN','Admin'),
                ('SELLER','Seller'),
                ('CUSTOMER','Customer'))    
    phone_number=models.CharField(unique=True,max_length=11,null=True,blank=True)
    role=models.CharField(max_length=20,choices=ROLE_CHOICES,default='CUSTOMER')
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_admin=models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.username

class Address(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    pincode = models.CharField(max_length=10)
    locality = models.CharField(max_length=255)
    house_info = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    landmark = models.CharField(max_length=255, blank=True)
    address_type = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.user} - {self.full_name}, {self.address_type}"

class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    message = models.TextField()
    image_url = models.ImageField(upload_to='notification_images/', blank=True, null=True)
    redirect_url = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    image_url = models.ImageField(upload_to='category_images/', blank=True, null=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
            if not self.slug:
                base_slug = slugify(self.name)
                slug = base_slug
                counter = 1

                while SubCategory.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                self.slug = slug

            super().save(*args, **kwargs)
class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="subcategories")
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name
    def save(self, *args, **kwargs):
            if not self.slug:
                base_slug = slugify(self.name)
                slug = base_slug
                counter = 1

                while SubCategory.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                self.slug = slug

            super().save(*args, **kwargs)
class Banner(models.Model):
    title = models.CharField(max_length=255)
    image_url = models.ImageField(upload_to='banner_images/', blank=True, null=True)
    redirect_url = models.URLField(blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return self.title


# Create your models here.
