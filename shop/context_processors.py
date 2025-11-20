from .models import CartItem

def cart_item_count(request):
    if request.user.is_authenticated:
       count = CartItem.objects.filter(
            user=request.user,
            variant__is_active=True,
            variant__product__is_active=True
        ).count()

    else:
        count = 0
    return {'cart_item_count' : count}