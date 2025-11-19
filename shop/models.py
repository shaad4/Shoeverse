from django.db import models
from django.conf import settings
from products.models import ProductVariant

# Create your models here.


class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart_items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.variant.product.name} - Size {self.variant.size} - Qty {self.quantity}"

    @property
    def total_price(self):
        quantity = min(self.quantity, 4)
        return self.variant.product.price * quantity
