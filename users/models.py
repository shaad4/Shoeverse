from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import UserManager
from django.conf import settings
from products.models import ProductVariant

# Create your models here.

def profile_upload_path(instance, filename):
    if instance.pk:
        return f"profiles/user_{instance.pk}/{filename}"
    return f"profiles/temp/{filename}"


class User(AbstractUser):
    #remove first_name and last_name
    first_name = None
    last_name = None
    username = None

    email = models.EmailField(unique=True)

    fullName = models.CharField(max_length=255)
    phoneNumber = models.CharField(max_length=20, null=True, blank=True)

    profileImage = models.ImageField(upload_to=profile_upload_path, null=True, blank=True)
    dateOfBirth = models.DateField(null=True, blank=True)

    gender = models.CharField(max_length=10, 
                              choices=[
                                  ("male","Male"),
                                  ("female","Female"),
                                  ("other", "Other")
                              ],
                              null=True,
                              blank=True
                              )
    role = models.CharField(max_length=20,
                            choices=[
                                ("user","User"),
                                ("admin","Admin"),
                            ],
                            default = "user"
                            )
    
    referralCode = models.CharField(max_length=20, unique=True, blank=True)
    referredBy = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)

    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    # Authentication config
    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["fullName"]

    #custom manager
    objects = UserManager()
    



class EmailOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="email_otp")
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)

    last_sent_at = models.DateTimeField(null=True, blank=True)


    
class Address(models.Model):
    ADDRESS_TYPE_CHOICE = [
        ('home',"Home"),
        ('work',"Work"),
        ('other',"Other"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True,  null=True)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length = 100)
    state = models.CharField(max_length = 100)
    pincode = models.CharField(max_length=10)
    address_type = models.CharField(max_length= 10, choices=ADDRESS_TYPE_CHOICE, default= "home")
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.address_line1}, {self.city}"
    





    

