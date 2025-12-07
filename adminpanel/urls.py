from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.admin_login_view, name="admin_login"),
    path("dashboard/" , views.admin_dashboard, name="admin_dashboard"),
    path("users/", views.user_list, name="admin_user_list"),
    path("users/block/<int:user_id>/", views.block_user, name="admin_block_user"),
    path("users/unblock/<int:user_id>/", views.unblock_user, name="admin_unblock_user"),
    path("users/add/", views.admin_add_user, name="admin_add_user"),
    path("users/edit/<int:user_id>/", views.admin_edit_user, name="admin_edit_user"),

    path("products/", views.product_list_view, name="admin_product_list"),
    path("products/add/", views.product_add_view, name="admin_product_add"),
    path("products_edit/<int:product_id>/", views.product_edit_view, name="admin_product_edit"),
    path("products_toggle/<int:product_id>/", views.product_toggle_view, name="admin_product_toggle"), 


    path("products/<int:product_id>/variants/", views.product_variant_list_view, name="admin_product_variants"),
    path("products/<int:product_id>/variants/add/", views.product_variant_add_view, name="admin_product_variant_add"),
    path("products/<int:product_id>/variants/<int:variant_id>/edit/", views.product_variant_edit_view, name="admin_product_variant_edit"),
    path("products/<int:product_id>/variants/<int:variant_id>/delete/", views.product_variant_delete_view, name="admin_product_variant_delete"),


    path("categories/", views.admin_category_list, name="admin_category_list"),
    path("categories/add/", views.admin_category_add, name="admin_category_add"),
    path("categories/edit/<int:id>/", views.admin_category_edit, name="admin_category_edit"),
    path("categories/delete/<int:id>/", views.admin_category_delete, name="admin_category_delete"),

    path("orders/", views.admin_order_list, name='admin_order_list'),
    path("orders/<str:order_id>/",views.admin_order_detail, name = "admin_order_detail"),
    path('order/<str:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('order/cancel-item/<int:item_id>/', views.admin_cancel_order_item, name='admin_cancel_order_item'),


    path('returns/',views.admin_return_list, name='admin_return_list'),
    path('returns/<int:return_id>/', views.admin_return_detail, name='admin_return_detail'),

    path('offers/',views.offer_list_view,  name="admin_offers"),
    path('offers/add/', views.admin_offer_add,name = "admin_offer_add"),
    path('offers/edit/<int:offer_id>/', views.admin_offer_edit, name='admin_offer_edit'),
    path("offers/toggle/<int:offer_id>/", views.admin_offer_toggle, name="admin_offer_toggle"),
    path("offers/delete/<int:offer_id>/", views.admin_offer_delete, name="admin_offer_delete"),

    path('coupons/', views.coupon_list_view , name="admin_coupon_list"),
    path('coupons/add/', views.coupon_add_view, name="admin_coupon_add"),
    path('coupon/toggle/<int:coupon_id>/', views.coupon_toggle_view, name="admin_coupon_toggle"),
    path('coupons/edit/<int:coupon_id>/', views.coupon_edit_view, name="admin_coupon_edit"),
    path('coupons/delete/<int:coupon_id>/', views.coupon_delete_view, name="admin_coupon_delete"),


    path('analytics/',  views.analytics_view, name="admin_analytics"),
    path('sales-report/',  views.sales_report_view,  name= 'admin_sales_report'),

    path('custom-admin/banners/', views.admin_banner_manager, name='admin_banner_manager'),
    path('custom-admin/banners/add/', views.admin_banner_add, name='admin_banner_add'),
    
    path("logout/", views.admin_logout_view, name="admin_logout"),



]

