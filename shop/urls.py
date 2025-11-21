from django.urls import path
from . import views

urlpatterns = [
   path("products/", views.product_list_view, name="shop_products"),
   path("products/category/<str:category>/",views.product_list_view, name="shop_category"),
   path("products/search/", views.product_list_view, name="shop_search"),

   path("product/<int:product_id>/", views.product_detail_view, name="product_detail"),


   path("cart/", views.cart_view, name="cart"),
   path("cart/add/<int:variant_id>/", views.add_to_cart, name="add_to_cart"),
   path("cart/remove/<int:item_id>/", views.remove_cart_item, name="remove_cart_item"),
   path('cart/update-size/<int:item_id>/', views.update_size, name='update_size'),
   path('cart/update/<int:item_id>/', views.update_cart_quantity, name='update_cart_quantity'),

   path("wishlist/", views.wishlist_view, name="wishlist"),
   path("wishlist/add/<int:product_id>/", views.add_to_wishlist, name="add_to_wishlist"),
   path("wishlist/remove/<int:item_id>/", views.remove_wishlist_item, name="remove_wishist_item"),
   path("wishlist/move-to-cart/<int:item_id>/",views.move_to_cart,  name="move_to_cart"),
   path("wishlist/move-all-to-cart/", views.move_all_to_cart, name="move_all_to_cart"),
   path("wishlist/clear-all/", views.clear_all_wishlist, name="wishlist_clear_all"),

   path('checkout/', views.checkout_view, name='checkout'),
   path('place-order/', views.place_order, name='place_order'),
   path('order-success/<int:order_id>/', views.order_success, name='order_success'),

   path('payment/<int:address_id>/', views.payment_view, name="payment"),
   path('place_order/<int:address_id>/',views.place_order, name="place_order"),

]


    
