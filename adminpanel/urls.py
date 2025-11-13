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

    path("logout/", views.admin_logout_view, name="admin_logout"),



]

