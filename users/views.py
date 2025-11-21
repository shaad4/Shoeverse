from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, login, authenticate, logout
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from .utils import generate_otp, send_otp_email, password_reset_email
from django.conf import settings
from users.models import EmailOTP

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes


from .forms import AddressForm

from products.models import Product, ProductVariant
from .models import Address

import logging

logger = logging.getLogger('users')
User = get_user_model()

def clean_input(value: str) -> str:
    if not value:
        return ""
    return value.strip()

# Create your views here.

def signup_view(request):
    if request.method == "POST":
        email = clean_input(request.POST.get('email'))
        fullName  = clean_input(request.POST.get('fullName'))
        password = clean_input(request.POST.get('password'))
        confirm_password = clean_input(request.POST.get('confirm_password'))
        referral = clean_input(request.POST.get('referral'))

        logger.info(f"Signup attempt: email={email}, referral={referral}")

        #Validations

        if not email or not fullName or not password or not confirm_password:
            logger.warning("Signup failed: Missing required fields")
            messages.error(request, "All fields must be filled.", extra_tags="signup")
            return redirect("signup")
        
        try:
            validate_email(email)
        except ValidationError:
            logger.warning(f"Signup failed: Invalid email ({email})")
            messages.error(request, "Enter a valid email." , extra_tags="signup")
            return redirect("signup")
        
        if User.objects.filter(email=email).exists():
            logger.warning(f"Signup failed: Email already exists ({email})")
            messages.error(request, "Email already registered.", extra_tags="signup")
            return redirect("signup")
        
        if len(password) < 6:
            logger.warning(f"Signup failed: Weak password for {email}")
            messages.error(request, "Password must be at least 6 characters.", extra_tags="signup")
            return redirect("signup")

        if password.isnumeric():
            logger.warning(f"Signup failed: Numeric-only password ({email})")
            messages.error(request, "Password cannot be numeric only.", extra_tags="signup")
            return redirect("signup")

        if password != confirm_password:
            logger.warning(f"Signup failed: Password mismatch ({email})")
            messages.error(request, "Passwords do not match.", extra_tags="signup")
            return redirect("signup")
        
        referredBy = None
        if referral:
            try:
                referredBy = User.objects.get(referralCode=referral)
                logger.info(f"User {email} was referred by {referredBy.email}")
            except User.DoesNotExist:
                logger.warning(f"Invalid referral code used: {referral}")
                messages.error(request, "Invalid referral code.", extra_tags="signup")
                return redirect("signup")
        #user created - not verified  
        user = User.objects.create_user(
            email = email,
            fullName = fullName,
            password=password,
            referredBy = referredBy
        )

        logger.info(f"User created (not verified): {email}")

        #OTP generate
        otp = generate_otp()
        expires_at = timezone.now() + timedelta(minutes=5)

        #delete old otp if exists
        EmailOTP.objects.filter(user=user).delete()

        #store otp
        EmailOTP.objects.create(
            user=user,
            otp=otp,
            expires_at=expires_at,
            is_verified  = False
        )

        logger.info(f"OTP generated for {email}: {otp}")

        #send OTP EMAIL
        try:
            send_otp_email(email, otp)
            logger.info(f"OTP email sent to {email}")
        except Exception as e:
            logger.error(f"Email sending failed for {email}: {e}")
            messages.error(request, "Unable to send OTP right now. Please try again.", extra_tags="signup")
            user.delete()  # rollback user creation
            return redirect("signup")
        
        #save session for user to verify 
        request.session["pending_user_id"] = user.id

        messages.success(
            request,
            "OTP sent to your email. Please verify to continue.", extra_tags="signup"
        )

        return redirect("verify_otp")
    
    return render(request, "users/signup.html")


def verify_otp_view(request):

    user_id = request.session.get("pending_user_id")

    if not user_id:
        logger.warning("OTP verification failed: No pending user session.")
        messages.error(request, "Session expired. Please sign up again.")
        return redirect("signup")
    
    try:
        user = User.objects.get(id=user_id)
        logger.info(f"OTP verification for user: {user.email}")
    except User.DoesNotExist:
        logger.error(f"Pending user not found for ID: {user_id}")
        messages.error(request, "User not found. Please sign up again.")
        return redirect("signup")
    
    try:
        otp_obj = EmailOTP.objects.get(user=user)
    except EmailOTP.DoesNotExist:
        logger.error(f"OTP record missing for user: {user.email}")
        messages.error(request, "OTP not found. Please sign up again.")
        return redirect("signup")
    
    if otp_obj.is_verified:
        logger.info(f"User {user.email} already verified. Logging in.")
        login(request, user)
        return redirect("home")
    
    


    if request.method == "POST":
        entered_otp = clean_input(request.POST.get('otp'))

        if not entered_otp:
            logger.warning(f"Empty OTP submission by user: {user.email}")
            messages.error(request, "Please enter the OTP.")
            return redirect("verify_otp")
        
        
        if timezone.now() > otp_obj.expires_at:
                logger.warning(f"OTP expired for {user.email}. Deleting account.")
                otp_obj.delete()
                user.delete()
                request.session.pop("pending_user_id", None)
                messages.error(request, "OTP expired. Please sign up again.")
                return redirect("signup")
        
        if entered_otp != otp_obj.otp:
                logger.warning(f"Incorrect OTP attempt for {user.email}. Entered: {entered_otp}")
                messages.error(request, "Incorrect OTP. Please try again.")
                return redirect("verify_otp")
        

        #if otp is success
        otp_obj.is_verified=True
        otp_obj.save()

        logger.info(f"OTP verified successfully for {user.email}")

        login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])


        #Remove session
        request.session.pop("pending_user_id", None)

        messages.success(request, "Email verified successfully!")
        logger.info(f"User logged in after OTP verification: {user.email}")

        return redirect("home")

    return render(request, "users/verify_otp.html",{"email":user.email})







def resend_otp_view(request):

    user_id = request.session.get("pending_user_id")

    if not user_id:
        messages.error(request, "Session expired. Please sign up again.")
        return redirect("signup")
    
    try:
        user = User.objects.get(id=user_id)
        otp_obj = EmailOTP.objects.get(user=user)
        logger.info(f"Resend OTP requested by: {user.email}")
    except:
        messages.error(request, "User or OTP record not found.")
        return redirect("signup")
    

    if otp_obj.last_sent_at and (timezone.now() - otp_obj.last_sent_at).seconds < 120:
        wait_time = 120 - (timezone.now() - otp_obj.last_sent_at).seconds
        messages.warning(request, f"Wait {wait_time} seconds before requesting new OTP.")
        return redirect("verify_otp")
    
    new_otp = generate_otp()
    otp_obj.otp = new_otp
    otp_obj.expires_at = timezone.now() + timedelta(minutes=5)
    otp_obj.last_sent_at = timezone.now()
    otp_obj.save()

    logger.info(f"New OTP generated for {user.email}: {new_otp}")

    send_otp_email(user.email, new_otp)
    logger.info(f"Resent OTP to {user.email}")

    messages.success(request, "A new OTP has been sent to your email.")
    return redirect("verify_otp")






def login_view(request):

    storage = messages.get_messages(request)
    for _ in storage:
        pass 

    if request.method == "POST":
        email = clean_input(request.POST.get('email'))
        password = clean_input(request.POST.get('password'))

        logger.info(f"Login attempt for email: {email}")

        if not email and password:
            messages.error(request, "Please enter both email and password.")
            return redirect('login')
        
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return redirect("login")
        
        if not user_obj.is_active:
            messages.error(request, "Your account is blocked. For more info, conatct support.")
            return redirect("login")
        
        
        user = authenticate(request, email=email, password=password)

       

        if user is None:
            logger.warning(f"Login failed for email: {email}")
            messages.error(request, "Invalid email or password.")
            return redirect('login')
        
        login(request, user)
        logger.info(f"User logged in successfully: {email}")
       

        return redirect("home")
    
    return render(request, "users/login.html")


def forget_password_view(request):
    if  request.method  == "POST":
        email  = clean_input(request.POST.get("email"))

        try:
            user =  User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "No account found with this email.")
            return redirect("forgot_password")
        

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        reset_link = request.build_absolute_uri(
            f"/reset-password/{uid}/{token}/"
        )

        try:
            password_reset_email(reset_link,  email)
            logger.info(f"reset email sent to {email}")
            messages.success(request, "Password reset link sent to your email.")
        except Exception as e:
            logger.error(f"Reset Email sending failed for {email}: {e}")
            messages.error(request, "Unable to send resend email right now. Please try again.")

        return redirect("forgot_password")
    return render(request, "users/forget_password.html")


def reset_password_view(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    if user is None or not default_token_generator.check_token(user,  token):
        messages.error(request, "Invalid or expired reset link.")
        return redirect("forgot_password")
    

    if request.method == "POST":
        password = clean_input(request.POST.get("password"))
        confirm = clean_input(request.POST.get("confirm_password"))

        if password != confirm:
            messages.error(request, "Password do not match.")
            return redirect(request.path)
        
        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
            return redirect(request.path)
        
        user.set_password(password)
        user.save()

        messages.success(request, "Password reset successfull. You can login in.")
        return redirect('login')
    
    return render(request, "users/reset_password.html")


    



def home_view(request):

    p1 = Product.objects.get(id=9)
    p2 = Product.objects.get(id=15)
    p3 = Product.objects.get(id=11)
    p4 = Product.objects.get(id=18)
    return render(request, "users/home.html", {"p1":p1,"p2":p2,"p3":p3,"p4":p4})


def logout_view(request):
    logout(request)
    messages.success(request,"logout of successfully")
    
    return redirect("home")  # Change to your landing page

#profile  


def profile_view(request):

    user = request.user

    context = {
        "user" : user,
    }

    return render(request, "users/profile_view.html", context)

def profile_edit_view(request):
    user = request.user

    if request.method == "POST":

        if request.POST.get("remove_image") == "1" and user.profileImage:
            user.profileImage.delete(save=False)
            user.profileImage = None


        user.fullName = request.POST.get("fullName")
        user.phoneNumber = request.POST.get("phoneNumber")
        user.gender = request.POST.get("gender")
        date_of_birth = request.POST.get("dateOfBirth")
        user.dateOfBirth = date_of_birth if date_of_birth else None

        if request.FILES.get("profileImage"):
            user.profileImage = request.FILES.get("profileImage")

        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("profile")
    
    return render(request, "users/profile_edit.html", {"user":user})

def change_password_request(request):
    user = request.user 

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    reset_link = request.build_absolute_uri(
        f"/reset-password/{uid}/{token}/"
    )

    try:
        password_reset_email(reset_link , user.email)
        messages.success(request, f"password reset link sent to your email {user.email}")
        logger.info(f"Password reset link sent to {user.email}")
    except Exception as e:
        messages.error(request, "Something went wrong. Please try again later.")
        logger.error(f"Password reset failed for {user.email}: {e}")

    return redirect("profile_edit")


#address

def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'users/address_list.html', {'addresses': addresses})

def address_add_view(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Address saved successfully!")

            if request.GET.get('next') == 'checkout':
                return redirect("checkout")
            
            return redirect("address")
    else:
        form = AddressForm()

    return render(request, 'users/address_add.html', {"form":form}) 
    

def address_edit_view(request, pk):
    address = get_object_or_404(Address, id=pk, user=request.user)

    if request.method == "POST":

        address.full_name = request.POST.get("full_name")
        address.phone_number = request.POST.get("phone_number")
        address.email = request.POST.get("email")
        address.address_type = request.POST.get("address_type")
        address.address_line1 = request.POST.get("address_line1")
        address.address_line2 = request.POST.get("address_line2")
        address.city = request.POST.get("city")
        address.state = request.POST.get("state")
        address.pincode = request.POST.get("pincode")
        address.save()

        messages.success(request, "Address updated successfully!")
        return redirect("address")
    
    return render(request,  "users/address_edit.html", {"address":address})


def address_delete_view(request, pk):
    address = get_object_or_404(Address, id = pk , user = request.user)

    if request.method == "POST":
        address.delete()
        messages.success(request, "Address deleted successfully")
        return redirect("address")
    
    

