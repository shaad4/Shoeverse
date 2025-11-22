from django.shortcuts import render,  get_object_or_404, redirect
from products.models import Product, SubCategory
from django.core.paginator import Paginator
from django.db.models import Count, Q

from products.models import Product, ProductVariant
from django.contrib import messages
from .models import CartItem, Wishlist, Address
from decimal import Decimal
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import json
from .models import Order, OrderItem

from datetime import timedelta
from django.utils.timezone import now
# Create your views here.



def product_list_view(request, category=None):
    products = (
        Product.objects.filter(is_active=True)
        .prefetch_related("images")
        .annotate(in_stock_count=Count('variants', filter=Q(variants__stock__gt=0)))
    )

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
    }

    return render(request, "shop/product_list.html", context)
    


def  product_detail_view(request, product_id):

    #get the product
    product = get_object_or_404(
        Product.objects.prefetch_related("images","variants"),
        id=product_id
    )

    if not product.is_active:
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

    #cart
    if request.GET.get("action") == "add_to_cart":
        if is_out_of_stock:
            return redirect("shop_products")
        ##cart logics later##

    is_in_wishlist = False
    if request.user.is_authenticated:
        is_in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()


    context = {
        "product" : product,
        "variants" : variants,
        "images" : images,
        "related_products" : related_products,
        "is_out_of_stock" : is_out_of_stock,
        "is_in_wishlist": is_in_wishlist,
    }

    return render(request, "shop/product_detail.html", context)



#cart

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


def remove_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id = item_id, user = request.user)
    item.delete()
    messages.success(request, "Item removed form cart")
    return redirect("cart")


@require_POST
def update_size(request, item_id):
    try:
        data = json.loads(request.body)
        variant_id = data.get("variant_id")

        cart_item = CartItem.objects.get(id = item_id, user=request.user)
        new_variant = ProductVariant.objects.get(id=variant_id)

        if new_variant.product != cart_item.variant.product:
            return JsonResponse({"error": "Invalid size selection"}, status=400)
        
        cart_item.variant = new_variant
        cart_item.save()

        return JsonResponse({"success": True})

    except CartItem.DoesNotExist:
        return JsonResponse({"error": "cart item not found"}, status=404)
    
    except ProductVariant.DoesNotExist:
        return JsonResponse({"error": "Variant not found"}, status=404)






@require_POST
def update_cart_quantity(request, item_id):
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Login required"}, status=401)

    try:
        data = json.loads(request.body)
        new_qty = int(data.get("quantity", 1))

        cart_item = CartItem.objects.get(id=item_id, user=request.user)

        # Max quantity limit: min(stock, 4)
        max_allowed = min(cart_item.variant.stock, 4)

        if new_qty < 1:
            cart_item.delete()
            return JsonResponse({"success": True, "removed": True})

        if new_qty > max_allowed:
            return JsonResponse({
                "success": False,
                "error": f"Max quantity allowed is {max_allowed}"
            }, status=400)

        cart_item.quantity = new_qty
        cart_item.save()

        return JsonResponse({
            "success": True,
            "quantity": cart_item.quantity,
            "total_price": float(cart_item.total_price)
        })

    except CartItem.DoesNotExist:
        return JsonResponse({"success": False, "error": "Item not found"}, status=404)

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


#wishlist

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


def wishlist_view(request):
    if not request.user.is_authenticated:
        return redirect("login")
    
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')

    wishlist_total = sum(item.product.price for item in  wishlist_items)

    return render(request, "shop/wishlist.html", {"wishlist_items":wishlist_items, "wishlist_total":wishlist_total})

def remove_wishlist_item(request, item_id):
    item = get_object_or_404(Wishlist, id=item_id, user=request.user)
    item.delete()
    messages.success(request, "Removed from wishlist")
    return redirect('wishlist')


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


def clear_all_wishlist(request):
    if not request.user.is_authenticated:
        return redirect("login")
    
    Wishlist.objects.filter(user=request.user).delete()
    messages.success(request, "All items cleared from wishlist.")
    return redirect('wishlist')

    
#checkout views

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

    context = {
        'address': address,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'gst': gst,
        'delivery_charge': delivery_charge,
        'grand_total': grand_total,
    }

    return render(request, 'shop/payment.html', context)

def place_order(request):
    if request.method != "POST":
        return redirect('checkout')
    
    address_id = request.POST.get('address_id')
    if not address_id:
        messages.error(request, "Please select a delivery address.")
        return redirect("checkout")
    
    address = get_object_or_404(Address, id=address_id, user=request.user)

    cart_items = CartItem.objects.filter(user=request.user)

    if not cart_items.exists():
        messages.error(request, "Your cart is empty")
        return redirect("cart")
    
    subtotal = sum(item.total_price for item in cart_items)
    gst = (subtotal * Decimal("0.18")).quantize(Decimal("0.01"))
    delivery_charge = Decimal("0") if subtotal >= Decimal("1000") else Decimal("100")
    grand_total = subtotal + gst + delivery_charge

    order = Order.objects.create(
        user = request.user,
        address = address,
        subtotal = subtotal,
        gst=gst,
        delivery_charge= delivery_charge,
        total_amount = grand_total,
        payment_method = 'COD',
        status = 'Pending',
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




def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    estimated_delivery_date = (now() + timedelta(days=5)).strftime("%d %b %Y")


    return render(request, 'shop/order_success.html',{'order': order, "estimated_delivery_date" : estimated_delivery_date })