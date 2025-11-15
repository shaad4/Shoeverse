from django.db import models
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

# Create your models here.

class Product(models.Model):
    CATEGORY_CHOICE = [
        ('MEN', 'Men'),
        ('WOMEN', 'Women'),
        ('KIDS', 'Kids'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10,  decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2,  null=True, blank=True)
    color  = models.CharField(max_length=50)
    category  = models.CharField(max_length=10, choices=CATEGORY_CHOICE)
    is_active = models.BooleanField(default=True)
    subcategory = models.ForeignKey("SubCategory", on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    highlights = models.TextField(blank=True, null=True)         # newline separated list
    specifications = models.TextField(blank=True, null=True)     # key:value list
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.category} - {self.color})"
    
    def total_stock(self):
        return sum(variant.stock for variant in self.variants.all())
    

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    size = models.CharField(max_length=10)
    stock =  models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return f"{self.product.name} - Size {self.size}"
    

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image =  models.ImageField(upload_to="products/")
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name}"
    
    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        img = Image.open(self.image.path)

        max_size = (1000, 1000)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img.save(self.image.path, format="JPEG", quality=85, optimize=True)



class SubCategory(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=10,
        choices=Product.CATEGORY_CHOICE
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('category', 'name')

    def __str__(self):
        return f"{self.category} - {self.name}"