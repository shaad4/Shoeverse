from django.urls import path
from .views import wallet_view

urlpatterns = [
    path('', wallet_view, name='wallet'),
]
