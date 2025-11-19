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


]


    
