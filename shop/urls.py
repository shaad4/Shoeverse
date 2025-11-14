from django.urls import path
from . import views

urlpatterns = [
   path("products/", views.product_list_view, name="shop_products"),
   path("products/category/<str:category>/",views.product_list_view, name="shop_category"),
   path("products/search/", views.product_list_view, name="shop_search"),

   path("product/<int:product_id>/", views.product_detail_view, name="product_detail"),
]


    
