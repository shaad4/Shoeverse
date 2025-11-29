from django.urls import path
from . import views

urlpatterns = [
    path('', views.wallet_view, name='wallet'),
    path('add-money/', views.wallet_add_money_view, name='wallet_add_money'),
    path('payment-success/', views.wallet_payment_success_view, name="wallet_payment_success"),
    path('payment-failed/', views.wallet_payment_failed_view, name="wallet_payment_failed"),
]
