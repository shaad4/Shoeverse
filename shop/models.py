from django.db import models
from django.conf import settings
from products.models import ProductVariant, Product
from users.models import Address


import uuid

def generate_order_id():
    return f"SV-{uuid.uuid4().hex[:10].upper()}"


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


class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user','product')


class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered' , 'Delivered'),
        ('Cancelled' , 'Cancelled'),

    ]

    PAYMENT_METHOD_CHOICES = [
        ('COD','Cash on Delivery'),
        ('ONLINE', 'Online Payment'),

    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)

    order_id = models.CharField(max_length=20, unique=True, blank=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gst = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status  = models.CharField(max_length=20, choices=STATUS_CHOICES,  default='Pending')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='COD')

    cancel_reason = models.TextField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order  #{self.id} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = generate_order_id()
        super().save(*args, **kwargs)

    def calculate_total(self):
        total = sum(item.total_price for item in self.items.all())
        self.total_amount = total
        self.save()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE ,related_name = 'items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, default = 0)

    @property
    def total_price(self):
        return self.price * (self.quantity)
    
    def __str__(self):
        return f"{self.variant.product.name} - Qty: {self.quantity}"
    

