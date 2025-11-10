import random
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger("users")



def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(email, otp):
    
    subject = "Your Shoeverse OTP Verification Code"
    message = f"""
Your OTP code is: {otp}

This code will expire in 5 minutes.
    
If you did not request this, please ignore the email.
"""

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False
        )
        logger.info(f"OTP email sent successfully to {email}")

    except Exception as e:
        logger.error(f"Error sending OTP email to {email}: {str(e)}")
        raise e
    

def password_reset_email(reset_link  , email):
    subject = "Shoeverse - Reset Your Password"
    message = f"Click the link to reset your password:\n{reset_link}"

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False
        )
        logger.info(f"Password reset link email sent successfully to {email}")

    except Exception as e:
        logger.error(f"Error sending password reset link email to {email}: {str(e)}")
        raise e