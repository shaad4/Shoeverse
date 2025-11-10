from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import UserManager

# Create your models here.

def profile_upload_path(instance, filename):
    return f"profiles/user_{instance.id}/{filename}"

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


    

