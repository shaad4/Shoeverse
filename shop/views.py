from django.shortcuts import render,  get_object_or_404, redirect
from products.models import Product, SubCategory, ProductReview
from django.core.paginator import Paginator
from django.db.models import Count, Q, Avg
from django.views.decorators.csrf import csrf_exempt
from products.models import Product, ProductVariant
from django.contrib import messages
from .models import CartItem, Wishlist, Address
from decimal import Decimal
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import json
from .models import Order, OrderItem, ReturnRequest
from django.utils import timezone

from datetime import timedelta
from django.utils.timezone import now
from users.decorator import user_required
from wallet.models import Wallet, WalletTransaction
import razorpay
from django.conf import settings
from payments.models import Payment
from django.db import transaction

import logging

logger = logging.getLogger(__name__)

# Create your views here.



def product_list_view(request, category=None):

    logger.info("Product list view called with category: %s", category)

    products = (
        Product.objects.filter(is_active=True)
        .prefetch_related("images")
        .annotate(
            in_stock_count=Count('variants', filter=Q(variants__stock__gt=0)),
            avg_rating=Avg('reviews__rating'),  
            review_count=Count('reviews')       
        )
    )
    logger.debug("Initial product count: %s", products.count())

    category_param = request.GET.get("category")

    if category_param:
        category = category_param.lower()

    if category:
        normalized_category = category.upper()   # men -> MEN
        if normalized_category in ["MEN", "WOMEN", "KIDS"]:
            products = products.filter(category=normalized_category)

    active_category = category  # keep lowercase for UI

    

    


    q = request.GET.get("q","")
    if q:
        products = products.filter(name__icontains=q)

    #size
    active_size = request.GET.getlist("size")
    if active_size:
        products  = products.filter(variants__size__in=active_size).distinct()


    #price
    min_price = request.GET.get("min_price","")
    max_price = request.GET.get("max_price","")

    if min_price:
        products = products.filter(price__gte=min_price)

    if max_price:
        products = products.filter(price__lte=max_price)

    #sort
    sort = request.GET.get("sort","")
    if sort == "priceLow":
        products = products.order_by("price")
    elif sort == "priceHigh":
        products = products.order_by("-price")
    elif  sort == "new":
        products = products.order_by("-created_at")
    elif sort == "nameAsc":
        products = products.order_by("name")
    elif sort == "nameDesc":
        products = products.order_by("-name")
    else:
        products = products.order_by("-id")

    #color
    active_color = request.GET.get("color", "").strip()

    if active_color:
        products = products.filter(color__icontains=active_color)

    #subcategory 
    active_subcategory = request.GET.get("subcategory","")

    if active_subcategory:
        products = products.filter(subcategory_id= active_subcategory)

    if category:
        subcategories = SubCategory.objects.filter(
            category = category.upper(),
            is_active = True
        )
    else:
        subcategories = SubCategory.objects.none()

    filters = request.GET.copy()
    if 'page' in filters:
        filters.pop('page')
    querystring = filters.urlencode()

    paginator = Paginator(products, 6)
    page_number  = request.GET.get("page")
    page_obj  = paginator.get_page(page_number)

    categories = ["men", "women", "kids"]

    # Dynamic sizes based on category
    if category == "kids":
        sizes = ["1", "2", "3", "4", "5"]
    else:  # (default)
        sizes = ["6", "7", "8", "9", "10", "11"]


    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = request.user.wishlist.values_list('product_id', flat=True)


    

    context = {
        "products" : page_obj,
        "category" : category,
        "page_obj" : page_obj,
        "paginator" : paginator,
        "q":q,
        "sort": sort,
        "active_color" :  active_color,
        "min_price" : min_price,
        "max_price" : max_price,
        "active_category" : active_category,
        "active_sizes" : active_size,
        "sizes":sizes,
        "categories":categories,
        "page_query" : querystring,
        "subcategories":subcategories,
        "active_subcategory":active_subcategory,
        "wishlist_ids": wishlist_ids,
    }

    return render(request, "shop/product_list.html", context)
    


def  product_detail_view(request, product_id):

    logger.info("Product detail view called for product_id=%s", product_id)

    #get the product
    product = get_object_or_404(
        Product.objects.prefetch_related("images","variants"),
        id=product_id
    )
    logger.debug("Loaded product: %s", product.name)

    if not product.is_active:
        logger.warning("Inactive product (ID=%s) accessed", product_id)
        return redirect("shop_products")
    
    #fetching all the product variantes
    variants = product.variants.filter(is_active=True).order_by("size")

    #fetch images
    images = product.images.all().order_by("-is_primary","id")

    #related_products
    related_products = Product.objects.filter(
        category=product.category,
        is_active = True,
    ).exclude(id=product.id)[:6]

    #stock check
    total_stock = sum(v.stock for v in variants)
    is_out_of_stock = total_stock == 0
    logger.debug("Stock check for product_id=%s | Total stock=%s", product_id, total_stock)

    #cart
    if request.GET.get("action") == "add_to_cart":
        logger.info("Add-to-cart request for product_id=%s", product_id)
        if is_out_of_stock:
            logger.warning("Attempt to add out-of-stock product_id=%s to cart", product_id)
            return redirect("shop_products")
        ##cart logics later##

    is_in_wishlist = False
    if request.user.is_authenticated:
        is_in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
        logger.debug("Wishlist status for product_id=%s | In wishlist=%s", product_id, is_in_wishlist)

    #review
    reviews = product.reviews.all().order_by('-created_at')
    review_count = reviews.count()
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    star_distribution = {
        5: reviews.filter(rating=5).count(),
        4: reviews.filter(rating=4).count(),
        3: reviews.filter(rating=3).count(),
        2: reviews.filter(rating=2).count(),
        1: reviews.filter(rating=1).count(),
    }

    # Check if user can review (Has bought + Delivered)
    can_review = False
    user_review = None

    if request.user.is_authenticated:
        has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            order__status='Delivered',
            variant__product=product
        ).exists()

        user_review = reviews.filter(user=request.user).first()

        if has_purchased:
            can_review = True
    
    context = {
        "product" : product,
        "variants" : variants,
        "images" : images,
        "related_products" : related_products,
        "is_out_of_stock" : is_out_of_stock,
        "is_in_wishlist": is_in_wishlist,
        'reviews': reviews,
        'review_count': review_count,
        'avg_rating': round(avg_rating, 1),
        'star_distribution': star_distribution,
        'can_review': can_review,
        'user_review': user_review, 
    }

    return render(request, "shop/product_detail.html", context)



#cart

@user_required
def add_to_cart(request, variant_id=None):
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to add items to cart.")
        return redirect("login")
    
    if request.method == "POST":
        variant_id = variant_id or request.POST.get("variant_id")

    if not variant_id:
        messages.error(request, "Invalid product selection")
        return redirect(request.META.get('HTTP_REFERER', 'shop_products'))
    
    variant = get_object_or_404(ProductVariant, id = variant_id)

    if not variant.product.is_active  or not variant.is_active:
        messages.error(request, "This product is not available")
        return redirect(request.META.get('HTTP_REFERER', 'shop_products'))

    if variant.stock <= 0:
        messages.error(request, "This product is out of stock")
        return redirect(request.META.get('HTTP_REFERER', 'shop_products'))
    
    quantity = int(request.POST.get('quantity',1))
    quantity = max(1, min(quantity, min(variant.stock, 4)))
    
    cart_item, created = CartItem.objects.get_or_create(
        user = request.user,
        variant=variant,
    )

    if created:
        cart_item.quantity = quantity     # FIXED
        cart_item.save()
        messages.success(request, "Item added to cart successfully!")
    else:
        if cart_item.quantity < min(variant.stock, 4):
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, "Quantity updated in cart")
        else:
            messages.warning(request, "Maximum quantity reached for this product")

    ####  Delete from  wishlist
    # from .models import Wishlist
    # Wishlist.objects.filter(user=request.user, variant=variant).delete()

    return redirect(request.META.get('HTTP_REFERER', 'shop_products'))

@user_required
def cart_view(request):
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to view your cart.")
        return redirect("login")
    

    cart_items = CartItem.objects.filter(user=request.user).select_related("variant", "variant__product")

    valid_items = cart_items.filter(
        variant__is_active=True,
        variant__product__is_active=True,
    )

    out_of_stock_items = valid_items.filter(variant__stock__lte=0)
    in_stock_items = valid_items.filter(variant__stock__gt=0)

    if not valid_items.exists():
        context = {
            "cart_items": [],
            "subtotal": Decimal('0'),
            "gst": Decimal('0'),
            "delivery_charge": Decimal('0'),
            "grand_total": Decimal('0'),
            "total_items": 0,
            
        }
        return render(request, "shop/cart.html", context)

    if in_stock_items.exists():
        subtotal = sum(item.total_price for item in in_stock_items)
        total_items = sum(item.quantity for item in in_stock_items)
    else:
        subtotal = Decimal('0')
        total_items = 0
        
    gst = (subtotal * Decimal('0.18')).quantize(Decimal('0.01'))

    delivery_charge = Decimal('0') if subtotal >= Decimal('1000') else Decimal('100')

    grand_total  = subtotal + gst + delivery_charge

   

    context = {
        "cart_items" : in_stock_items,
        "subtotal" : subtotal,
        "gst" :  gst,
        "delivery_charge" : delivery_charge,
        "grand_total" : grand_total,
        "total_items" : total_items,
        "out_of_stock_items": out_of_stock_items,

    }

    return render(request,  "shop/cart.html", context)

@user_required
def remove_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id = item_id, user = request.user)
    item.delete()
    messages.success(request, "Item removed form cart")
    return redirect("cart")

@user_required
@require_POST
def update_size(request, item_id):
    try:
        data = json.loads(request.body)
        variant_id = data.get("variant_id")

        cart_item = CartItem.objects.get(id = item_id, user=request.user)
        new_variant = ProductVariant.objects.get(id=variant_id)

        if new_variant.product != cart_item.variant.product:
            return JsonResponse({"error": "Invalid size selection"}, status=400)
        
        if new_variant.stock <= 0:
            return JsonResponse({"success":False, "error": "Selected size is out of stock"}, status=400)
        
        cart_item.variant = new_variant
        # Reset quantity to 1 if new size has less stock than current quantity
        if cart_item.quantity > new_variant.stock:
            cart_item.quantity = new_variant.stock
        cart_item.save()

        cart_data = get_cart_data(request.user)

        return JsonResponse({
            "success": True,
            "item_total": cart_item.total_price,
            "cart_data": cart_data       
        })

    except CartItem.DoesNotExist:
        return JsonResponse({"error": "cart item not found"}, status=404)
    
    except ProductVariant.DoesNotExist:
        return JsonResponse({"error": "Variant not found"}, status=404)


def get_cart_data(user):
    cart_items = CartItem.objects.filter(user=user, variant__stock__gt=0, variant__is_active=True)

    if cart_items.exists():
        subtotal = sum(item.total_price for item in cart_items)
        gst = (subtotal * Decimal('0.18')).quantize(Decimal('0.01'))
        delivery_charge = Decimal('0') if subtotal >= Decimal('1000') else Decimal('100')
        grand_total = subtotal + gst + delivery_charge
        total_items = sum(item.quantity for item in cart_items)
    else:
        subtotal = gst = delivery_charge = grand_total = Decimal('0')
        total_items = 0

    return {
        "subtotal": subtotal,
        "gst": gst,
        "delivery_charge": delivery_charge,
        "grand_total": grand_total,
        "total_items": total_items
    }

@user_required
@require_POST
def update_cart_quantity(request, item_id):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Login required"}, status=401)

    try:
        data = json.loads(request.body)

        # Handle null/undefined quantity
        qty_param = data.get("quantity")
        if qty_param is None:
            new_qty = 1 
        else:
            new_qty = int(qty_param)

        cart_item = CartItem.objects.get(id=item_id, user=request.user)
        max_allowed = min(cart_item.variant.stock, 4)

        # --- REMOVE ITEM LOGIC ---
        if new_qty < 1:
            cart_item.delete()
            cart_data = get_cart_data(request.user) # Ensure this helper exists
            
            return JsonResponse({
                "success": True, 
                "removed": True, 
                "cart_totals": cart_data  # CHANGED: "cart_data" -> "cart_totals"
            })

        # --- MAX LIMIT LOGIC ---
        if new_qty > max_allowed:
            return JsonResponse({
                "success": False,
                "error": f"Max quantity allowed is {max_allowed}"
            }, status=400)

        # --- UPDATE LOGIC ---
        cart_item.quantity = new_qty
        cart_item.save()
        
        cart_data = get_cart_data(request.user)

        return JsonResponse({
            "success": True,
            "removed": False,
            # Keys now match JavaScript expectations
            "item_qty": cart_item.quantity,          # was "quantity"
            "item_total": float(cart_item.total_price), # was "total_price"
            "cart_totals": cart_data,                # was "cart_data"
        })

    except CartItem.DoesNotExist:
        return JsonResponse({"success": False, "error": "Item not found"}, status=404)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

#wishlist
@user_required
def add_to_wishlist(request,  product_id):
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to save items")
        return redirect("login")
    
    product = get_object_or_404(Product, id=product_id)

    wishlist_item,  created = Wishlist.objects.get_or_create(
        user=request.user,
          product=product
    )
    if created:
        messages.success(request,  "Added to wishlist")
    else:
        messages.warning(request, "This product is already in your wishlist")

    return redirect(request.META.get('HTTP_REFERER', 'shop_products'))

@user_required
def wishlist_view(request):
    if not request.user.is_authenticated:
        return redirect("login")
    
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')

    wishlist_total = sum(item.product.price for item in  wishlist_items)

    return render(request, "shop/wishlist.html", {"wishlist_items":wishlist_items, "wishlist_total":wishlist_total})

@user_required
def remove_wishlist_item(request, item_id):
    item = get_object_or_404(Wishlist, id=item_id, user=request.user)
    item.delete()
    messages.success(request, "Removed from wishlist")
    return redirect('wishlist')


@user_required
def move_to_cart(request, item_id):
    wishlist_item = get_object_or_404(Wishlist, id=item_id, user=request.user)
    
    variant = wishlist_item.product.variants.filter(is_active=True, stock__gt=0).first()

    if not variant:
        messages.error(request, "No valid variant available")
        return redirect("wishlist")
    
    CartItem.objects.get_or_create(user=request.user, variant=variant)
    wishlist_item.delete()
    messages.success(request, "Moved to cart")

    return redirect("cart")
    
@user_required
def move_all_to_cart(request):
    if not request.user.is_authenticated:
        return redirect("login")
    
    wishlist_items = Wishlist.objects.filter(user=request.user)

    if not wishlist_items.exists():
        messages.warning(request, "Your wishlist is empty.")
        return redirect("wishlist")
    
    for item in wishlist_items:
        product = item.product
        variant = product.variants.filter(is_active=True, stock__gt=0).first()

        if variant:
            CartItem.objects.get_or_create(user=request.user, variant=variant)

        item.delete()

    messages.success(request, "All items moved to cart successfully")
    return redirect("cart")


@user_required
def clear_all_wishlist(request):
    if not request.user.is_authenticated:
        return redirect("login")
    
    Wishlist.objects.filter(user=request.user).delete()
    messages.success(request, "All items cleared from wishlist.")
    return redirect('wishlist')

    
#checkout views

@user_required
def checkout_view(request):

    if not request.user.is_authenticated:
        messages.error(request, "Please log in to proceed to checkout")
        return  redirect("login")
    
    cart_items = CartItem.objects.filter(
        user=request.user,
        variant__is_active=True,
        variant__product__is_active=True,
    ).select_related('variant', 'variant__product')

    if not cart_items.exists():
        messages.error(request, "Your cart is empty!")
        return redirect("cart")
    
    addresses = Address.objects.filter(user=request.user)

    
    subtotal = sum(item.total_price for item in cart_items)
    gst = (subtotal * Decimal('0.18')).quantize(Decimal('0.01'))
    delivery_charge = Decimal('0') if subtotal >= Decimal('1000') else Decimal('100')
    grand_total = subtotal + gst + delivery_charge
    total_items = sum(item.quantity for item in cart_items)

    is_free_delivery = (delivery_charge == Decimal('0'))

    estimated_delivery_date = (now() + timedelta(days=5)).strftime("%d %b %Y")


    context = {
        'addresses' : addresses,
        'cart_items' : cart_items,
        'subtotal' : subtotal,
        'grand_total' : grand_total,
        'gst' : gst,
        'total_items': total_items,
        'estimated_delivery_date': estimated_delivery_date,
        'is_free_delivery': is_free_delivery,


    }
    return render(request, 'shop/checkout.html', context)


@user_required
def payment_view(request, address_id):
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to continue payment.")
        return redirect("login")
    
    address = get_object_or_404(Address, id=address_id, user=request.user)
    cart_items = CartItem.objects.filter(user=request.user)

    if not cart_items.exists():
        messages.error(request, "Your cart is empty")
        return redirect("cart")

    subtotal = sum(item.total_price for item in cart_items)
    gst = (subtotal * Decimal("0.18")).quantize(Decimal("0.01"))
    delivery_charge = Decimal("0") if subtotal >= Decimal("1000") else Decimal("100")
    grand_total = subtotal + gst + delivery_charge

    # wallet
    wallet,_ = Wallet.objects.get_or_create(user=request.user)
    wallet_balance = wallet.balance

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    razorpay_order = client.order.create({
        "amount":int(grand_total * 100),
        "currency" :"INR",
        "payment_capture":1,
    })

    context = {
        'address': address,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'gst': gst,
        'delivery_charge': delivery_charge,
        'grand_total': grand_total,
        'wallet_balance' : wallet_balance,

        "rzp_key_id": settings.RAZORPAY_KEY_ID,
        "rzp_order_id": razorpay_order["id"],
        "rzp_amount": int(grand_total * 100),
        "order_number": razorpay_order["id"],
    }

    return render(request, 'shop/payment.html', context)

@user_required
def place_order(request):
    if request.method != "POST":
        return redirect('checkout')
    
    address_id = request.POST.get('address_id')
    payment_method = request.POST.get("payment_method")

    if not address_id:
        messages.error(request, "Please select a delivery address.")
        return redirect("checkout")
    
    address = get_object_or_404(Address, id=address_id, user=request.user)

    cart_items = CartItem.objects.filter(user=request.user)

    if not cart_items.exists():
        messages.error(request, "Your cart is empty")
        return redirect("cart")
    
    for item in cart_items:
        if item.quantity > item.variant.stock:
            messages.error(request, f"{item.variant.product.name} is out of stock")
            return redirect('checkout')
    
    subtotal = sum(item.total_price for item in cart_items)
    gst = (subtotal * Decimal("0.18")).quantize(Decimal("0.01"))
    delivery_charge = Decimal("0") if subtotal >= Decimal("1000") else Decimal("100")
    grand_total = subtotal + gst + delivery_charge

    #razorpay 
    if payment_method == "razorpay":
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create({
            "amount":int(grand_total * 100),
            "currency" : "INR",
            "payment_capture" : 1,
        })

        payment = Payment.objects.create(
            user=request.user,
            amount=grand_total,
            purpose="order_payment",
            razorpay_order_id = razorpay_order['id'],
            status="pending",
        )


        return render(request, "shop/razorpay_payment.html",{
            "razorpay_order": razorpay_order,
            "razorpay_key": settings.RAZORPAY_KEY_ID,
            "payment": payment,
            "amount": grand_total,
            "address": address,
        })
    
    try:
        with transaction.atomic():
            payment_status = "PENDING"

            if payment_method == "wallet":
                wallet, _ = Wallet.objects.get_or_create(user=request.user)
                #lock the wallet row
                wallet = Wallet.objects.select_for_update().get(user=request.user)

                if wallet.balance >= grand_total:
                    balance_before = wallet.balance

                    wallet.balance -= grand_total
                    wallet.save()

                    balance_after = wallet.balance

                    WalletTransaction.objects.create(
                        wallet=wallet,
                        amount=grand_total,
                        transaction_type="debit",
                        description="Order Payment from Wallet",
                        balance_before = balance_before,
                        balance_after = balance_after
                    )
                    payment_status = "SUCCESS"
                else:
                    messages.error(request, "Insufficent wallet balance")
                    return redirect("payment", address_id=address_id)
            elif payment_method == "cod":
                payment_status = "PENDING"
            else:
                messages.error(request, "Invalid payment option")
                return redirect("payment", address_id=address_id)


            order = Order.objects.create(
                user = request.user,
                address = address,
                subtotal = subtotal,
                gst=gst,
                delivery_charge= delivery_charge,
                total_amount = grand_total,
                payment_method = payment_method,
                status = 'Processing' if payment_status == "SUCCESS" else "Pending",
            )

            for item in cart_items:
                if item.quantity > item.variant.stock:
                    messages.error(request, f"{item.variant.product.name} is out of stock")
                    return redirect('checkout')
                
                OrderItem.objects.create(
                    order=order,
                    variant=item.variant,
                    quantity = item.quantity,
                    price = item.variant.product.price,
                )
                item.variant.stock -= item.quantity
                item.variant.save()

            cart_items.delete()

            return redirect('order_success',order_id=order.id)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('cart')

@csrf_exempt
@user_required
def razorpay_payment_verify(request):
    payment_id = request.GET.get("payment_id")
    order_id = request.GET.get("order_id")
    signature = request.GET.get("signature")
    address_id = request.GET.get("address_id")

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        })

        with transaction.atomic():

            #upafte payment table
            payment = get_object_or_404(Payment, razorpay_order_id=order_id)
            payment.status = "SUCCESS"
            payment.razorpay_payment_id = payment_id
            payment.save()

            address = get_object_or_404(Address, id=address_id, user=request.user)

            # Cart items
            cart_items = CartItem.objects.filter(user=request.user)

       
            if not cart_items.exists():
                messages.error(request, "Your cart is empty")
                return redirect("cart")
        
            # Price calculation
            subtotal = sum(item.total_price for item in cart_items)
            gst = (subtotal * Decimal("0.18")).quantize(Decimal("0.01"))
            delivery_charge = Decimal("0") if subtotal >= Decimal("1000") else Decimal("100")
            grand_total = subtotal + gst + delivery_charge

            order = Order.objects.create(
                user=request.user,
                address=address,
                subtotal=subtotal,
                gst = gst,
                delivery_charge = delivery_charge,
                total_amount = grand_total,
                payment_method="Razorpay",
                status='Processing'
            )

            # Create Order Items & reduce stock
            for item in cart_items:
                
                OrderItem.objects.create(
                    order=order,
                    variant=item.variant,
                    quantity=item.quantity,
                    price=item.variant.product.price,
                )
                item.variant.stock -= item.quantity
                item.variant.save()

            # Clear cart after ordering
            cart_items.delete()

        return redirect('order_success', order_id=order.id)


    except razorpay.errors.SignatureVerificationError:
        payment = Payment.objects.filter(razorpay_order_id=order_id).first()
        messages.error(request, "Payment verification failed.")
        return redirect('payment_failed', order_id=payment.id if payment else 0)
    except Exception as e:
        messages.error(request, "An error occurred during order creation.")
        print(e)
        return redirect("cart")

@user_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    estimated_delivery_date = (now() + timedelta(days=5)).strftime("%d %b %Y")


    return render(request, 'shop/order_success.html',{'order': order, "estimated_delivery_date" : estimated_delivery_date })

@user_required
def order_failed_view(request, order_id):
    order = None
    address_id = None

    try:
        order = Order.objects.get(id =order_id, user=request.user)
        address_id = order.address.id
    except Order.DoesNotExist:
        order = None

        address_id = request.GET.get('address_id')

    error_description = request.GET.get('description', 'Transaction failed')
        

    return render(request, "shop/order_failed.html",{
        "order":order,
        "order_id_display": order_id,
        "address_id": address_id,
        "error_description": error_description,
    })

@user_required
def razorpay_payment_failed(request):
    order_id = request.GET.get('order_id')
    error_description = request.GET.get('description')
    address_id = request.GET.get('address_id')

    payment = Payment.objects.filter(razorpay_order_id=order_id).first()
    
    if payment:
        payment.status = "FAILED"
        payment.save()

    return render(request, "shop/order_failed.html", {
        "payment": payment,
        "order_id_display": order_id,
        "error_description": error_description,
        "address_id": address_id
    })



@user_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)

    if order.status in ["Shipped", "Delivered", "Cancelled"]:
        messages.error(request, "Cannot cancel this order. Please contact support.")
        return redirect('order_detail', order_id=order_id)

    # if request.method == "POST":
    #     reason = request.POST.get("cancel_reason")
    #     order.status = "Cancelled"
    #     order.cancel_reason = reason
    #     order.save()

    # order_items = OrderItem.objects.filter(order=order)
    # for item in order_items:
    #     item.variant.stock += item.quantity
    #     item.variant.save()

    # messages.success(request, "Order cancelled successfully")
    # return redirect('order_detail', order_id=order_id)

    if request.method == "POST":
        reason = request.POST.get("cancel_reason")

        try:
            with transaction.atomic():
                order_items = OrderItem.objects.filter(order=order)
                for item in order_items:
                    item.variant.stock += item.quantity
                    item.variant.save()

                if order.payment_method in ["wallet","razorpay","Razorpay"]:
                    wallet,_ = Wallet.objects.get_or_create(user=request.user)
                    refund_amount = order.total_amount

                    balance_before = wallet.balance
                    wallet.balance += refund_amount
                    wallet.save()
                    balance_after = wallet.balance

                    WalletTransaction.objects.create(
                        wallet=wallet,
                        amount=refund_amount,
                        transaction_type="credit",
                        description = f"Refund for Order #{order.order_id}",
                        balance_before =balance_before,
                        balance_after = balance_after
                    )
                    messages.success(request, f"Order cancelled. ₹{refund_amount} refunded to wallet.")
                else:
                    messages.success(request, "Order cancelled successfully.")

                    order.status = "Cancelled"
                    order.cancel_reason = reason
                    order.save()
        except Exception as e:
            messages.error(request, f"Error cancelling order: {e}")

    return redirect('order_detail', order_id=order_id)

@user_required
def cancel_order_item(request, item_id):
    item = get_object_or_404(OrderItem , id = item_id, order__user=request.user)
    order = item.order

    if order.status in ["Shipped", "Delivered", "Cancelled"]:
        messages.error(request, "Cannot cancel items at this stage.")
        return redirect('order_detail', order_id=order.order_id)
    

    if request.method == "POST":
        try:
            with transaction.atomic():
                old_grand_total = order.total_amount

                item.status = "Cancelled"
                item.save()

                item.variant.stock += item.quantity
                item.variant.save()
                
                active_items = order.items.exclude(status='Cancelled')

                if not active_items.exists():

                    order.status = "Cancelled"
                    order.cancel_reason = "All items were cancelled individually"
                    order.subtotal = Decimal(0)
                    order.gst = Decimal(0)
                    order.delivery_charge = Decimal(0)
                    order.total_amount = Decimal(0)
                else:
                    new_subtotal = sum(i.total_price for i in active_items)
                    order.subtotal = new_subtotal
                    order.gst = (new_subtotal * Decimal('0.18')).quantize(Decimal('0.01')) 
                    
                    if order.subtotal >= 1000:
                        order.delivery_charge = Decimal(0)
                    else:
                        order.delivery_charge = Decimal(100)

                    order.total_amount = order.subtotal + order.gst + order.delivery_charge

                order.save()

                refund_amount = old_grand_total - order.total_amount

                if refund_amount > 0 and order.payment_method in ["wallet", "razorpay", "Razorpay"]:
                    wallet,_ = Wallet.objects.get_or_create(user=request.user)

                    balance_before = wallet.balance
                    wallet.balance += refund_amount
                    wallet.save()
                    balance_after = wallet.balance

                    WalletTransaction.objects.create(
                        wallet=wallet,
                        amount=refund_amount,
                        transaction_type="credit",
                        description=f"Refund for Item: {item.variant.product.name}",
                        balance_before=balance_before,
                        balance_after=balance_after
                    )
                    messages.success(request, f"Item cancelled. ₹{refund_amount} refunded to wallet.")
                else:
                    messages.success(request, "Item cancelled and order updated.")

        except Exception as e:
            messages.error(request, f"Error cancelling item: {e}")

    return redirect('order_detail', order_id=order.order_id)



#return 
@user_required
def return_order_items(request, order_id):
    order = get_object_or_404(Order, order_id = order_id, user=request.user)


    if order.status != "Delivered" or not order.delivered_at:
        messages.error(request, "Return request is only allowed after delivery.")
        return redirect('order_detail', order_id=order_id)
    
    expiry_date = (order.delivered_at + timedelta(days=10)).date()
    today = now().date()

    if today > expiry_date:
        messages.error(request, "Return window has expired for this order.")
        return redirect('order_detail', order_id=order_id)
    
    already_requested_ids = ReturnRequest.objects.filter(
        order_item__order=order
    ).values_list('order_item_id', flat=True)

    eligible_items = order.items.exclude(id__in=already_requested_ids)

    if not eligible_items.exists():
        messages.info(request, "All eligible items in this order have already been requested for return.")
        return redirect('order_detail', order_id=order_id)

    context = {
        "order": order,
        "items": eligible_items,
        "addresses": request.user.addresses.all(),
        "expiry_date": expiry_date,
    }

    return render(request, "shop/returns.html", context)

@user_required
def submit_return_request(request, order_id):
    if request.method == "POST":
        order = get_object_or_404(Order, order_id=order_id, user=request.user)

        selected_item_ids = request.POST.getlist('item_id')

        if not selected_item_ids:
            messages.error(request, "Please select at least one item to return.")
            return redirect('return_order_items', order_id=order_id)


        
        reason = request.POST.get('reason')
        pickup_address_id = request.POST.get('pickup_address')

        uploaded_images = request.FILES.getlist('images')


        for item_id in selected_item_ids:
            order_item = get_object_or_404(OrderItem, id=item_id, order=order)

            if not order_item.is_return_eligible():
                messages.error(
                    request,
                    f"Return window expired for {order_item.variant.product.name}. "
                    f"Returns are allowed only within 10 days of delivery."
                )
                return redirect('order_detail', order_id=order_id)
            
            if ReturnRequest.objects.filter(order_item=order_item).exists():
                continue

            return_request = ReturnRequest.objects.create(
                order_item = order_item,
                user=request.user,
                reason = reason,
                pickup_address_id = pickup_address_id,
            )

            if uploaded_images:
                if len(uploaded_images) > 0:
                    return_request.image1 = uploaded_images[0]
                if len(uploaded_images) > 1:
                    return_request.image2 = uploaded_images[1]
                if len(uploaded_images) > 2:
                    return_request.image3 = uploaded_images[2]
                return_request.save()

        messages.success(request, "Return request submitted successfully")
        return redirect('order_detail', order_id = order.order_id)
    
    return redirect('return_order_items', order_id=order_id)


#reviews
@user_required
def submit_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    has_purchased  = OrderItem.objects.filter(
        order__user = request.user,
        order__status = 'Delivered',
        variant__product = product
    ).exists()

    if  not has_purchased:
        messages.error(request,  "You can only review products you have purchased")
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    existing_review = ProductReview.objects.filter(user=request.user, product=product).first()

    if request.method == "POST":
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        if not rating:
            messages.error(request, "Please select a star rating")
            return redirect(request.path)
        
        if existing_review:
            existing_review.rating = rating
            existing_review.comment = comment
            existing_review.save()
            messages.success(request, "Your review has been updated!")
        else:
            ProductReview.objects.create(
                product=product,
                user = request.user,
                rating = rating,
                comment =  comment,

            )
            messages.success(request, "Thank you for your review!")

        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    context = {
        'product' : product,
        'review' : existing_review
    }

    return render(request, 'shop/submit_review.html', context)

