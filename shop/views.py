from django.shortcuts import render,  get_object_or_404, redirect
from products.models import Product, SubCategory
from django.core.paginator import Paginator
from django.db.models import Count, Q

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

    context = {
        "product" : product,
        "variants" : variants,
        "images" : images,
        "related_products" : related_products,
        "is_out_of_stock" : is_out_of_stock,
    }

    return render(request, "shop/product_detail.html", context)
