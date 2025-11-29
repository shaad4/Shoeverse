from django.shortcuts import render, get_object_or_404
from users.decorator import user_required
from .models import Wallet, WalletTransaction
# Create your views here.


@user_required
def wallet_view(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions = wallet.transactions.all().order_by("-created_at")

    context = {
        'wallet': wallet,
        'transactions': transactions,
    }

    return render(request, 'wallet.html', context)

