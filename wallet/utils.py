from decimal import Decimal
from .models import WalletTransaction

def credit_wallet(wallet, amount, description=""):
    amount = Decimal(amount)
    balance_before = wallet.balance
    wallet.balance += amount
    wallet.save()
    
    WalletTransaction.objects.create(
        wallet=wallet,
        amount=amount,
        transaction_type='credit',
        description=description,
        balance_before=balance_before,
        balance_after=wallet.balance
    )
    return wallet.balance


def debit_wallet(wallet, amount, description=""):
    amount = Decimal(amount)

    if wallet.balance < amount:
        raise ValueError("Insufficient wallet balance")
    
    balance_before = wallet.balance
    wallet.balance -= amount
    wallet.save()

    WalletTransaction.objects.create(
        wallet=wallet,
        amount=amount,
        transaction_type='debit',
        description=description,
        balance_before=balance_before,
        balance_after=wallet.balance
    )
    return wallet.balance
