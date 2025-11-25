import random
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger("users")



def generate_otp():
    return str(random.randint(100000, 999999))


from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_otp_email(email, otp):
    subject = "Your Shoeverse OTP Verification Code"

    html_content = f"""
    <html>
    <body style="font-family: 'Inter', sans-serif; background-color: #121714; margin: 0; padding: 0;">
        <div style="max-width: 600px; margin: 40px auto; background-color: #1B221D; 
                    padding: 30px; border-radius: 12px; color: white; 
                    border: 1px solid #2d3a34; box-shadow: 0px 5px 25px rgba(0,0,0,0.4);">

            <!-- Logo Section -->
            <div style="text-align: center; margin-bottom: 20px;">
                <img src="https://res.cloudinary.com/dltvyhamc/image/upload/v1763635469/logo_tsgqnk.svg" 
                     alt="Shoeverse Logo" 
                     style="height: 60px; width: auto;">
                     <p>Shoeverse</p>
            </div>

            <h2 style="text-align: center; color: #38E078; margin-bottom: 10px;">
                Email Verification
            </h2>
            <p style="text-align: center; color: #9EB8A8; margin-top: 0; font-size: 14px;">
                Secure login verification
            </p>

            <p style="font-size: 16px; color: #D1D5DB; margin-top: 28px;">
                Hi there,<br><br>
                Use the verification code below to complete your login or account verification.
            </p>

            <div style="background-color: #29382E; color: #38E078; 
                        text-align: center; font-size: 28px; 
                        font-weight: bold; padding: 15px 0; 
                        margin: 20px auto; border-radius: 10px; 
                        letter-spacing: 6px; max-width: 300px;">
                {otp}
            </div>

            <p style="font-size: 14px; color: #9EB8A8;">
                ⏳ This code will expire in <strong>5 minutes</strong>.
            </p>

            <p style="font-size: 13px; color: #6B7280; margin-top: 25px;">
                If you didn’t request this code, you can safely ignore this email.
            </p>

            <p style="text-align: center; margin-top: 35px; color: #9EB8A8; font-size: 13px;">
                © Shoeverse — Step into the future of footwear
            </p>
        </div>
    </body>
    </html>
    """

    try:
        msg = EmailMultiAlternatives(
            subject,
            f"Your OTP is {otp}. It expires in 5 minutes.",  # Plain text fallback
            settings.DEFAULT_FROM_EMAIL,
            [email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        logger.info(f"OTP email sent successfully to {email}")

    except Exception as e:
        logger.error(f"Error sending OTP email to {email}: {str(e)}")
        raise e

    

def password_reset_email(reset_link, email):
    subject = "Shoeverse - Reset Your Password"

    html_content = f"""
    <html>
    <body style="font-family: 'Inter', sans-serif; background-color: #121714; margin: 0; padding: 0;">
        <div style="max-width: 600px; margin: 40px auto; background-color: #1B221D; 
                    padding: 30px; border-radius: 12px; color: white; 
                    border: 1px solid #2d3a34; box-shadow: 0px 5px 25px rgba(0,0,0,0.4);">

            <!-- Logo -->
            <div style="text-align: center; margin-bottom: 25px;">
                <img src="https://res.cloudinary.com/dltvyhamc/image/upload/v1763635469/logo_tsgqnk.svg"
                     alt="Shoeverse Logo" style="height: 60px; width: auto;">
                     <p>Shoeverse</p>
            </div>

            <h2 style="text-align: center; color: #38E078; margin-bottom: 10px;">
                Reset Your Password
            </h2>
            <p style="text-align: center; color: #9EB8A8; margin-top: 0; font-size: 14px;">
                We received a request to reset your password.
            </p>

            <!-- Message -->
            <p style="font-size: 15px; color: #D1D5DB; margin-top: 28px;">
                No worries — it happens! Click the button below to securely reset your password
                and regain access to your Shoeverse account.
            </p>

            <!-- Reset Button -->
            <div style="text-align: center; margin-top: 30px; margin-bottom: 30px;">
                <a href="{reset_link}" target="_blank"
                   style="background-color: #38E078; color: #121714; padding: 12px 28px; 
                          font-size: 16px; font-weight: bold; text-decoration: none; 
                          border-radius: 8px; display: inline-block;">
                    Reset Password
                </a>
            </div>

            <!-- Fallback Link -->
            <p style="font-size: 13px; color: #9EB8A8; margin-top: 10px;">
                If the button doesn't work, copy and paste this link into your browser:<br>
                <a href="{reset_link}" style="color: #38E078;">{reset_link}</a>
            </p>

            <p style="font-size: 13px; color: #6B7280; margin-top: 25px;">
                If you didn't request this, you can safely ignore this email. 
                Your password will remain unchanged.
            </p>

            <p style="text-align: center; margin-top: 35px; color: #9EB8A8; font-size: 12px;">
                © Shoeverse — Step into the future of footwear
            </p>
        </div>
    </body>
    </html>
    """

    try:
        msg = EmailMultiAlternatives(
            subject,
            f"Use the link to reset your password: {reset_link}",  # Plain text fallback
            settings.DEFAULT_FROM_EMAIL,
            [email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        logger.info(f"Password reset email sent successfully to {email}")

    except Exception as e:
        logger.error(f"Error sending password reset email to {email}: {str(e)}")
        raise e
    

def email_change_confirmation(confirm_link, email):
    subject = "Shoeverse - Confirm Your Email Change"

    html_content = f"""
    <html>
    <body style="font-family: 'Inter', sans-serif; background-color: #121714; margin: 0; padding: 0;">
        <div style="max-width: 600px; margin: 40px auto; background-color: #1B221D;
                    padding: 30px; border-radius: 12px; color: white;
                    border: 1px solid #2d3a34; box-shadow: 0px 5px 25px rgba(0,0,0,0.4);">

            <!-- Logo -->
            <div style="text-align: center; margin-bottom: 25px;">
                <img src="https://res.cloudinary.com/dltvyhamc/image/upload/v1763635469/logo_tsgqnk.svg"
                     alt="Shoeverse Logo" style="height: 60px; width: auto;">
                <p style="color: #9EB8A8; margin-top: 5px;">Shoeverse</p>
            </div>

            <!-- Title -->
            <h2 style="text-align: center; color: #38E078; margin-bottom: 10px;">
                Confirm Your Email Change
            </h2>
            <p style="text-align: center; color: #9EB8A8; margin-top: 0; font-size: 14px;">
                You're just one step away from updating your email address.
            </p>

            <!-- Message -->
            <p style="font-size: 15px; color: #D1D5DB; margin-top: 28px;">
                We received a request to change your email for your Shoeverse account.
                To confirm this change, please click the button below.  
                <br><br>
                <strong>If you didn't request this, please ignore this email.</strong>
            </p>

            <!-- Confirm Button -->
            <div style="text-align: center; margin-top: 30px; margin-bottom: 30px;">
                <a href="{confirm_link}" target="_blank"
                   style="background-color: #38E078; color: #121714; padding: 12px 28px;
                          font-size: 16px; font-weight: bold; text-decoration: none;
                          border-radius: 8px; display: inline-block;">
                    Confirm Email Change
                </a>
            </div>

            <!-- Fallback Link -->
            <p style="font-size: 13px; color: #9EB8A8; margin-top: 10px;">
                If the button doesn't work, copy and paste this link into your browser:<br>
                <a href="{confirm_link}" style="color: #38E078;">{confirm_link}</a>
            </p>

            <!-- Footer -->
            <p style="text-align: center; margin-top: 35px; color: #9EB8A8; font-size: 12px;">
                © Shoeverse — Step into the future of footwear
            </p>
        </div>
    </body>
    </html>
    """

    try:
        msg = EmailMultiAlternatives(
            subject,
            f"Confirm your email change: {confirm_link}",  # Text version
            settings.DEFAULT_FROM_EMAIL,
            [email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        logger.info(f"Email change confirmation sent successfully to {email}")

    except Exception as e:
        logger.error(f"Error sending email change confirmation to {email}: {str(e)}")
        raise e