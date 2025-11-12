from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import get_user_model
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_http_methods
from products.models import Product, ProductVariant, ProductImage
from products.forms import ProductForm, ProductVarientForm

logger = logging.getLogger("users")
User = get_user_model()

# Create your views here.

def clean_input(value: str) -> str:
    if not value:
        return ""
    return value.strip()


def admin_login_view(request):

    if request.user.is_authenticated and  request.user.role == "admin":
        return redirect("admin_dashboard")
    
    if request.method == "POST":
        email = clean_input(request.POST.get("email"))
        password = clean_input(request.POST.get("password"))

        logger.info(f"Admin login attempt: {email}")

        if not email and password:
            messages.error(request, "Email and password are required")
            return redirect("admin_login")
        
        user = authenticate(email = email , password = password)

        if user is None:
            logger.warning(f"Admin login failed: invalid credentials {email}")
            messages.error(request, "Invalid email or password.")
            return redirect("admin_login")

        if user.role != "admin":
            logger.warning(f"Unauthorized access attempt bt {email}")
            messages.error(request, "Access denied. Admins only.")
            return  redirect("admin_login")
        
        login(request, user)
        logger.info(f"Admin logged in: {email}")
        messages.success(request, "Logged successfuly")
        return redirect("admin_dashboard")
    
    return render(request, "adminpanel/admin_login.html")



@login_required(login_url="admin_login")
def admin_dashboard(request):
    breadcrumbs = [
        {"label": "Dashboard", "url": "/adminpanel/dashboard/"},
    ]
    return render(request, "adminpanel/dashboard.html", {
        "breadcrumbs": breadcrumbs,
        "active_page": "dashboard"
    })



def user_list(request):

    breadcrumbs = [
        {"label": "Dashboard", "url": "/adminpanel/dashboard/"},
        {"label": "Customers", "url":  "/adminpanel/users/"},

    ]



    search_query = request.GET.get("search", "").strip()
    role_filter = request.GET.get("role","").strip()
    status_filter = request.GET.get("status","").strip()
    joined_sort = request.GET.get("joined","").strip()

    users = User.objects.all().order_by("-date_joined")

    if search_query:
        users = users.filter(
            Q(fullName__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    if role_filter == "user":
        users = users.filter(role="user")
    elif role_filter == "admin":
        users = users.filter(role="admin")

    if status_filter == "active":
        users = users.filter(is_active=True)      
    elif status_filter == "blocked":
        users = users.filter(is_active=False)

    if joined_sort == "newest":
        users = users.order_by("-createdAt")
    elif joined_sort == "oldest":
        users = users.order_by("createdAt")

    paginator = Paginator(users, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "breadcrumbs" : breadcrumbs,
        "page_obj" : page_obj,
        "search_query":  search_query,
        "active_page": "customers", 

    }

    return render(request, "adminpanel/user_list.html", context)


@require_http_methods(["POST"])
def block_user(request, user_id):
    


    user = get_object_or_404(User, id=user_id)

    if request.user.id == user.id:
        messages.error(request, "You cannot block yourself.")
        return redirect("admin_user_list")
    
    if user.role == "admin":
        messages.error(request,  "You cannot block admin.")
        return redirect("admin_user_list")
    
    user.is_active = False
    user.save()

    messages.success(request, f"{user.fullName} has been blocked")
    return redirect("admin_user_list")

def unblock_user(request, user_id):
    user = get_object_or_404(User , id=user_id)

    user.is_active  = True
    user.save()

    messages.success(request, f"{user.fullName} has been unblocked")
    return redirect("admin_user_list")


def admin_add_user(request):
    if  request.method == "POST":
        fullName = clean_input(request.POST.get("fullName"))
        email = clean_input(request.POST.get("email"))
        phone = clean_input(request.POST.get("phoneNumber"))
        dob = clean_input(request.POST.get("dateOfBirth"))
        gender = clean_input(request.POST.get("gender"))
        role  = clean_input(request.POST.get("role"))
        profileImage = request.FILES.get("profileImage")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect("admin_user_list")
        
        password = get_random_string(12)

        user = User.objects.create(
            fullName=fullName,
            email=email,
            phoneNumber=phone,
            dateOfBirth=dob,
            gender=gender,
            role=role,
            is_active=True,
        )

        if profileImage:
            user.profileImage = profileImage

        user.set_password(password)
        user.save()

        messages.success(request, f"User '{fullName}' created successfully.")
        return  redirect("admin_user_list")
    
    return redirect("admin_user_list")



def admin_edit_user(request, user_id):

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        user.fullName = clean_input(request.POST.get("fullName"))
        user.email = clean_input(request.POST.get("email"))
        user.phoneNumber = clean_input(request.POST.get("phoneNumber"))
        dob = clean_input(request.POST.get("dateOfBirth")) 
        user.dateOfBirth = dob if dob else None
        user.gender = clean_input(request.POST.get("gender"))
        user.role = clean_input(request.POST.get("role"))

        if "profileImage" in  request.FILES:
            user.profileImage = request.FILES["profileImage"]

        if request.POST.get("removeImage") == "on":
            user.profileImage.delete(save=False)
            user.profileImage = None

        user.save()

        messages.success(request, "User updated successfully!")
        return redirect("admin_user_list")
    
    


def product_list_view(request):
    query = request.GET.get("q","")
    products = Product.objects.order_by("-created_at").prefetch_related("images")

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(color__icontains=query) |
            Q(category__icontains=query)
        )

    paginator = Paginator(products, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    form = ProductForm()

    context = {
        "page_obj" : page_obj,
        "query" : query,
        "breadcrumb" : [
            {"name" : "Dashboard", "url": "admin_dashboard"},
            {"name" : "Product Management", "url": "admin_product_list"},

        ],
        "active_page": "products",
         "form": form, 
    }
    
    return  render(request, "adminpanel/products/product_list.html", context)
    


def product_add_view(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        images = request.FILES.getlist("images")
        if form.is_valid():
            product = form.save()

            for index, image  in enumerate(images[:3]):
                ProductImage.objects.create(
                    product=product,
                    image=image,
                    is_primary=(index==0)
                )
            messages.success(request, "Product added successfully with images!")
            return redirect("admin_product_list")
        else:
            messages.error(request, "Please fix the errors below.")
            return redirect("admin_product_list")
 
    return redirect("admin_product_list")
    

def product_variant_list_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    variants = product.variants.all().order_by("size")

    form = ProductVarientForm()

    context = {
        "product" : product,
        "variants":  variants,
        "form" : form,
        "breadcrumb" : [
            {"name":"Dashboard", "url":"admin_dashboard"},
            {"name":"Products", "url" :"admin_product_list"},
            {"name":f"Variants of {product.name}", "url":"admin_product_variants"},
        ],
    }

    return render(request, "adminpanel/products/product_variant_list.html", context)


def product_variant_add_view(request,  product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method  == "POST":
        form = ProductVarientForm(request.POST)
        if form.is_valid():
            variant = form.save(commit=False)
            variant.product = product
            variant.save()
            messages.success(request, f"Variant '{variant.size}' added successfully!")
            return redirect("admin_product_variants", product_id = product.id)
        else:
            messages.error(request, "Please fix the errors below")
    return redirect("admin_product_variants", product_id=product.id)


def product_edit_view(request, product_id):
    product  = get_object_or_404(Product, id=product_id)
    existing_images = product.images.all()


    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        new_images = request.FILES.getlist("images")  
        remove_images = request.POST.getlist("remove_images") 


        if form.is_valid():
            form.save()
            
            for img_id in remove_images:
                try:
                    img = ProductImage.objects.get(id=img_id, product=product)
                    img.image.delete(save=False)
                    img.delete()
                except ProductImage.DoesNotExist:
                    pass

            remaining = 3 - product.images.count()
            for index, img in enumerate(new_images[:remaining]):
                ProductImage.objects.create(
                    product=product,
                    image=img,
                    is_primary=(product.images.count() == 0 and index == 0)
                )

            messages.success(request, f"Product '{product.name}' updated successfully!")
            return redirect("admin_product_list")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = ProductForm(instance=product)

    context = {
        "form" : form,
        "product" : product,
        "existing_images":existing_images,
        "breadcrumb": [
            {"name": "Dashboard", "url": "admin_dashboard"},
            {"name": "Product Management", "url": "admin_product_list"},
            {"name": f"Edit {product.name}", "url": "admin_product_edit"},
        ],
        "active_page":"products",
    }

    return render(request, "adminpanel/products/product_edit.html",  context)



def product_toggle_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    product.is_active = not product.is_active
    product.save()

    if product.is_active:
        messages.success(request, f"Product '{product.name}' is now listed.")
    else:
        messages.warning(request, f"Product '{product.name}' has been unlisted.")

    return redirect("admin_product_list")


def product_variant_edit_view(request, product_id, variant_id):
    product = get_object_or_404(Product, id=product_id)
    variant = get_object_or_404(ProductVariant, id=variant_id)

    if request.method == "POST":
        form = ProductVarientForm(request.POST, instance=variant)
        if form.is_valid():
            form.save()
            messages.success(request, f"Variant '{variant.size}' updated successfully!")
            return redirect("admin_product_variants", product_id=product.id)
        else:
            messages.error(request, "Please fix the errors below.")
    return redirect("admin_product_variants", product_id=product.id)

def product_variant_delete_view(request, product_id, variant_id):
    product = get_object_or_404(Product, id=product_id)
    variant = get_object_or_404(ProductVariant, id=variant_id, product=product)

    # Delete the variant
    variant.delete()
    messages.success(request, f"Variant (Size {variant.size}) deleted successfully!")

    return redirect("admin_product_variants", product_id=product.id)