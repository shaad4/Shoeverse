from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string
from .models import User


#Referral Code Signal 
@receiver(post_save, sender=User)
def generate_refferal_code(sender, instance, created, **kwargs):
    if created and not instance.referralCode:
        instance.referralCode = get_random_string(10).upper()
        instance.save()

