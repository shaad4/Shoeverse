from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import get_user_model
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_http_methods
from products.models import Product, ProductVariant, ProductImage, SubCategory
from products.forms import ProductForm, ProductVarientForm
from shop.models import  Order, ReturnRequest
from .decorator import admin_required
from django.utils.timezone import now

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



@admin_required
def admin_dashboard(request):

    product_count = Product.objects.count()
    user_count = User.objects.count()

    recent_customers = User.objects.filter(role="user").order_by("-date_joined")[:4]

    breadcrumbs = [
        {"label": "Dashboard", "url": "/adminpanel/dashboard/"},
    ]
    return render(request, "adminpanel/dashboard.html", {
        "breadcrumbs": breadcrumbs,
        "active_page": "dashboard",
        "product_count": product_count,
        "user_count" : user_count,
        "recent_customers":recent_customers,
    })


@admin_required
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

@admin_required
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


@admin_required
def unblock_user(request, user_id):
    user = get_object_or_404(User , id=user_id)

    user.is_active  = True
    user.save()

    messages.success(request, f"{user.fullName} has been unblocked")
    return redirect("admin_user_list")

@admin_required
def admin_add_user(request):
    if  request.method == "POST":
        fullName = clean_input(request.POST.get("fullName"))
        email = clean_input(request.POST.get("email"))
        phone = clean_input(request.POST.get("phoneNumber"))
        dob = clean_input(request.POST.get("dateOfBirth")) or None
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

@admin_required
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
    
    

@admin_required
def product_list_view(request):
    query = request.GET.get("q","")
    products = Product.objects.order_by("-created_at").prefetch_related("images")


    
    category_filter = request.GET.get("category", "")
    if category_filter:
        products = products.filter(category=category_filter)

    status_filter = request.GET.get("status", "")

    if status_filter == "listed":
        products = products.filter(is_active=True)

    elif status_filter == "unlisted":
        products = products.filter(is_active=False)


    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(color__icontains=query) |
            Q(category__icontains=query)
        )


    sort_by = request.GET.get("sort","")

    if sort_by == "nameAsc":
        products = products.order_by("name")
    elif sort_by == "nameDesc":
        products = products.order_by("-name")
    elif sort_by == "priceLow":
        products = products.order_by("price")
    elif sort_by == "priceHigh":
        products = products.order_by("-price")
    elif sort_by == "stockLow":
        products = sorted(products, key=lambda p : p.total_stock())
    elif sort_by == "stockHigh":
        products = sorted(products, key=lambda p : p.total_stock(), reverse=True)
    elif sort_by == "newest":
        products = products.order_by("-created_at")
    elif sort_by == "oldest":
        products = products.order_by("created_at")
    else:
        products = products.order_by("-id")


    paginator = Paginator(products, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    form = ProductForm()

    # context = {
    #     "page_obj" : page_obj,
    #     "query" : query,
    #     "breadcrumbs" : [
    #         {"name" : "Dashboard", "url": "admin_dashboard"},
    #         {"name" : "Product Management", "url": "admin_product_list"},

    #     ],
    #     "active_page": "products",
    #      "form": form, 
    # }
    context = {
        "page_obj": page_obj,
        "query": query,
        "breadcrumbs": [
            {"name": "Dashboard", "url": "admin_dashboard"},
            {"name": "Product Management", "url": "admin_product_list"},
        ],
        "active_page": "products",
        "form": form,
        "sort":sort_by,
        "category_filter":category_filter,
        "status_filter" : status_filter,
    }

    
    return  render(request, "adminpanel/products/product_list.html", context)
    

@admin_required
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
    
@admin_required
def product_variant_list_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    variants = product.variants.all().order_by("size")

    form = ProductVarientForm()

    
    context = {
        "product": product,
        "variants": variants,
        "form": form,
        "breadcrumbs": [
            {"name": "Dashboard", "url": "admin_dashboard"},
            {"name": "Products", "url": "admin_product_list"},
            {"name": f"Variants of {product.name}", "url": "admin_product_variants", "args": [product.id]},
        ],
    }



    return render(request, "adminpanel/products/product_variant_list.html", context)

@admin_required
def product_variant_add_view(request,  product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method  == "POST":
        form = ProductVarientForm(request.POST)
        if form.is_valid():
            variant = form.save(commit=False) #not saving to DB
            variant.product = product #adding the product id
            variant.save() #now saving to db
            messages.success(request, f"Variant '{variant.size}' added successfully!")
            return redirect("admin_product_variants", product_id = product.id)
        else:
            messages.error(request, "Please fix the errors below")
    return redirect("admin_product_variants", product_id=product.id)

@admin_required
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
                    img = ProductImage.objects.get(id=img_id, product=product) #image takes from perticular id
                    img.image.delete(save=False) # delete from media
                    img.delete() # delete url from db
                except ProductImage.DoesNotExist:
                    pass

            remaining = 3 - product.images.count() #take total number of images for a perticular product
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
        "form": form,
        "product": product,
        "existing_images": existing_images,
        "breadcrumbs": [
            {"name": "Dashboard", "url": "admin_dashboard"},
            {"name": "Product Management", "url": "admin_product_list"},
            {"name": f"Edit {product.name}", "url": "admin_product_edit", "args": [product.id]},
        ],
        "active_page": "products",
    }


    return render(request, "adminpanel/products/product_edit.html",  context)


@admin_required
def product_toggle_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    product.is_active = not product.is_active # toggle the is_active
    product.save()

    if product.is_active:
        messages.success(request, f"Product '{product.name}' is now listed.")
    else:
        messages.warning(request, f"Product '{product.name}' has been unlisted.")

    return redirect("admin_product_list")

@admin_required
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

@admin_required
def product_variant_delete_view(request, product_id, variant_id):
    product = get_object_or_404(Product, id=product_id)
    variant = get_object_or_404(ProductVariant, id=variant_id, product=product)

    # Delete the variant
    variant.delete()
    messages.success(request, f"Variant (Size {variant.size}) deleted successfully!")

    return redirect("admin_product_variants", product_id=product.id)


@admin_required
def admin_logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect("admin_login")


@admin_required
def admin_category_list(request):
    subcategories = SubCategory.objects.all().order_by("category","name")

    context = {
        "subcategories" : subcategories,
        "active_page" : "categories",
        "breadcrumbs" :[
            {"label": "Dashboard", "url": "admin_dashboard"},
            {"label": "Category Management", "url": "admin_category_list"},
        ]
    }
    
    return render(request, "adminpanel/category/admin_category_list.html", context)

@admin_required
def admin_category_add(request):
    if request.method == "POST":
        name = request.POST.get("name").strip()
        category = request.POST.get("category")
        is_active = request.POST.get("is_active") == "on"

        if SubCategory.objects.filter(category=category,name__iexact=name).exists():
                messages.error(request, "Subcategory with this name already exists.")
                return redirect("admin_category_list")
        
        SubCategory.objects.create(
                name=name,
                category=category,
                is_active=is_active
            )
        
        messages.success(request, f"Subcategory '{name}' created successfully.")
        return redirect("admin_category_list")
    
    return redirect("admin_category_list")

@admin_required
def admin_category_edit(request , id):
    subcategory = get_object_or_404(SubCategory, id=id)

    if request.method == "POST":
        subcategory.name = request.POST.get("name").strip()
        subcategory.category = request.POST.get("category")
        subcategory.is_active = request.POST.get("is_active") == "on"
        subcategory.save()

        messages.success(request, f"Subcategory '{subcategory.name}' updated successfully.")
        return redirect("admin_category_list")
    
    context = {
        "subcategory": subcategory,
        "active_page": "categories",
        "breadcrumbs": [
            {"label": "Dashboard", "url": "admin_dashboard"},
            {"label": "Category Management", "url": "admin_category_list"},
            {"label": "Edit Subcategory", "url": ""},
        ],
    }

    return render(request, "adminpanel/category/admin_category_edit.html", context)

@admin_required
def admin_category_delete(request, id):
    subcategory = get_object_or_404(SubCategory, id=id)

    subcategory.delete()
    messages.success(request, f"Subcategory '{subcategory.name}' deleted successfully.")

    return redirect("admin_category_list")


# order list
@admin_required
def admin_order_list(request):
    search_query = request.GET.get('search',"")
    status_filter = request.GET.get("status","")
    sort = request.GET.get('sort','')

    orders = Order.objects.all()

    if search_query:
        orders = orders.filter(
            Q(order_id__icontains=search_query)|
            Q(user__fullName__icontains=search_query)|
            Q(user__email__icontains = search_query)
        )


    if status_filter:
        orders = orders.filter(status = status_filter)

    if sort == 'date_desc':
        orders = orders.order_by('-created_at')
    elif sort == 'date_asc':
        orders = orders.order_by('created_at')
    elif sort ==  'amount_desc':
        orders = orders.order_by('-total_amount')
    elif sort == 'amount_asc':
        orders = orders.order_by('total_amount')
    else:
        orders = orders.order_by('-created_at')

    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj' : page_obj,
        'search_query' : search_query,
        'status_filter' : status_filter,
        'sort' : sort,
        'status_choices' : Order.STATUS_CHOICES,
        'active_page' : "orders",
    }

    return render(request, 'adminpanel/order_list.html', context)

#order detail
@admin_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, order_id = order_id)

    return render(request, 'adminpanel/order_detail.html', {"order":order})

@admin_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)

    if request.method == "POST":
        new_status = request.POST.get('status')

    if new_status == order.status:
            messages.info(request, "No changes made.")
            return redirect('admin_order_detail', order_id=order.order_id)
    
    order.status = new_status

    if new_status == "Delivered":
        order.delivered_at = now()

    elif new_status != "Delivered":
        order.delivered_at = None

    order.save()

    messages.success(request, f"Order status updated to {new_status}.")
    return redirect('admin_order_detail', order_id=order.order_id)

#return 
@admin_required
def admin_return_list(request):
    returns = ReturnRequest.objects.select_related(
        'order_item__order',
        'order_item__variant__product',
        'user'
    )

    search_query = request.GET.get('search', '').strip()
    if search_query:
        returns = returns.filter(
            Q(order_item__order__order_id__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(order_item__variant__product__name__icontains=search_query)
        )

    status_filter = request.GET.get('status')
    if status_filter:
        returns = returns.filter(status=status_filter)

    sort = request.GET.get('sort', '')
    if sort == 'newest':
        returns = returns.order_by('-requested_at')
    elif sort == 'oldest':
        returns = returns.order_by('requested_at')
    elif sort == 'amount_desc':
        returns = returns.order_by('-refund_amount')
    elif sort == 'amount_asc':
        returns = returns.order_by('refund_amount')

    paginator = Paginator(returns, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'sort': sort,
        'return_status_choices': ReturnRequest.RETURN_STATUS_CHOICES,
        'active_page': 'returns',
    }

    return render(request, 'adminpanel/returns_list.html', context)


@admin_required
def admin_return_detail(request, return_id):
    return_request = get_object_or_404(
        ReturnRequest.objects.select_related(
            "order_item__order",
            "order_item__variant__product",
            "user",
            "pickup_address"
        ),
        id=return_id
    )

    if request.method == "POST":
        new_status = request.POST.get("status")
        admin_comments = request.POST.get("comments", "")
        refund_mode = request.POST.get("refund_mode", "")
        pickup_date = request.POST.get("pickup_date", "")

        return_request.status = new_status

        if pickup_date:
            return_request.pickup_date = pickup_date

        if refund_mode and new_status in ["REFUND_INITIATED", "REFUNDED"]:
            return_request.refund_mode = refund_mode

        if admin_comments:
            return_request.comments = admin_comments

        if new_status == "REFUND_INITIATED":
            return_request.refund_amount = return_request.calculate_refund_amount()
            messages.info(request, f"Refund Initiated for ₹{return_request.refund_amount}")

        return_request.save()

        messages.success(request, "Return request updated successfully.")
        return redirect("admin_return_detail", return_id=return_id)
    
    context = {
        "return_request": return_request,
        "status_choices": ReturnRequest.RETURN_STATUS_CHOICES,
        "active_page": "returns",
    }


    return render(request, 'adminpanel/return_detail.html', context)