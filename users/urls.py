from django.urls import path
from . import views


urlpatterns = [
    path("", views.home_view, name="home"),
    path('signup/', views.signup_view, name='signup'),
    path("verify-otp/", views.verify_otp_view, name="verify_otp"),
    path("resend-otp/", views.resend_otp_view, name="resend_otp"),

    path("login/", views.login_view, name="login"),
    path("forgot-password/", views.forget_password_view, name="forgot_password"),
    path("reset-password/<uidb64>/<token>/", views.reset_password_view, name="reset_password"),
    path("logout/", views.logout_view, name="logout"),

    path("profile/",  views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit_view, name="profile_edit"),
    path("password-change-request/", views.change_password_request, name="password_change_request"),

    path("address/", views.address_list, name="address"),
    path("address/add/", views.address_add_view, name="add_address"),
    path("address/edit/<int:pk>/", views.address_edit_view, name="edit_address"),
    path("address/delete/<int:pk>/", views.address_delete_view, name="delete_address"),
    
    path("my-orders/", views.order_list_view, name="order_list"),
    path("order/<str:order_id>/", views.order_detail_view, name="order_detail"),
    path("invoice/<str:order_id>/", views.download_invoice, name="download_invoice"),
    path('return/request/<int:return_id>/', views.return_request_detail, name='return_detail'),

    path('send-email-change-link/', views.send_email_change_link, name='send_email_change_link'),
    path('confirm-email-change/<uidb64>/<token>/', views.confirm_email_change, name='confirm_email_change'),
]

    

    
