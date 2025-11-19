
from django import forms
from .models import Address

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            'full_name', 'phone_number', 'email', 'address_line1', 'address_line2',
            'city', 'state', 'pincode', 'address_type'
        ]

        widgets = {
            'full_name': forms.TextInput(attrs={'placeholder': 'Enter your full name'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Enter your phone number'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email address (Optional)'}),
            'address_line1': forms.TextInput(attrs={'placeholder': 'Enter your address line 1'}),
            'address_line2': forms.TextInput(attrs={'placeholder': 'Enter your address line 2 (Optional)'}),
            'city': forms.TextInput(attrs={'placeholder': 'Enter your city'}),
            'state': forms.TextInput(attrs={'placeholder': 'Enter your state'}),
            'pincode': forms.TextInput(attrs={'placeholder': 'Enter zip code'}),
            'address_type': forms.Select(attrs={'class': 'input-field'}),
        }