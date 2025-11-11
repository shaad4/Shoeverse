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

]
