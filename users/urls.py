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


]