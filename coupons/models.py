from django.db import models
from products.models import SubCategory
from datetime import timezone
from django.contrib.auth import get_user_model
User = get_user_model()
# Create your models here.

class Coupon(models.Model):
    DISCOUNT_TYPE  = [
        ('percent','Percentage'),
        ('flat', 'Flat Amount'),
    ]

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)

    discountType = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE
    )
    discountValue = models.DecimalField(max_digits=10, decimal_places=2)

    userLimit = models.PositiveIntegerField(default=1)
    minCartValue = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    category = models.ForeignKey(
        SubCategory,
        on_delete= models.SET_NULL,
        null=True,
        blank=True
    )

    validFrom = models.DateTimeField()
    validTill = models.DateTimeField()

    isActive = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return  f"{self.code}  - {self.discountType}"
    
    def is_valid(self):
        now = timezone.now()
        return  self.isActive and self.validFrom  <= now <= self.validTill
    

class CouponUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    used_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user} used {self.coupon.code} ({self.used_count} times)"
    
    
    