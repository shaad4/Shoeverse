from django.db import models
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from django.db.models import IntegerField
from django.db.models.functions import Cast


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
    
    def get_first_available_variant(self):
        """Returns the first active variant with stock > 0"""
        return self.variants.filter(stock__gt=0, is_active=True).first()
    
    #offer logics

    def get_product_offers(self):
        now = timezone.now()
        return  Offer.objects.filter(
            offer_type = "product",
            products=self,
            is_active = True,
            start_date__lte = now,
            end_date__gte = now
        )

    def get_category_offers(self):
        if not self.subcategory:
            return Offer.objects.none()
        
        now = timezone.now()
        return Offer.objects.filter(
            offer_type="category",
            subcategories=self.subcategory,
            is_active = True,
            start_date__lte = now,
            end_date__gte = now
            
        )
    
    def get_best_offer(self):
        offers = list(self.get_product_offers()) + list(self.get_category_offers())

        if not offers:
            return None
        
        return max(offers, key=lambda o:o.discount_percent)
    
    @property
    def offer_percentage(self):
        offer = self.get_best_offer()
        return offer.discount_percent if offer else 0
    
    @property
    def final_price(self):
        offer = self.get_best_offer()
        if not offer:
            return self.price
        
        discount = (self.price * Decimal(offer.discount_percent) / 100)
        return (self.price - discount).quantize(Decimal("0.01"))
           
    
    
    

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    size = models.CharField(max_length=10)
    stock =  models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        ordering = [Cast('size', IntegerField()).asc()]


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
    


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete= models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.product.name} ({self.rating} stars)"
    



class Offer(models.Model):
    OFFER_TYPES = [
        ("product", "Product Offer"),
        ("category", "Category Offer"),
    ]
    title = models.CharField(max_length=255)
    offer_type = models.CharField(max_length=20, choices=OFFER_TYPES)
    discount_percent = models.PositiveIntegerField()

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    products = models.ManyToManyField(Product, blank=True, related_name= "product_offers")
    
    subcategories = models.ManyToManyField(SubCategory, blank=True, related_name = "category_offers")

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    def is_valid(self):
        now = timezone.now()
        return (
            self.is_active and
            self.start_date <= now <= self.end_date
        )
    
    def __str__(self):
        return self.title
    
