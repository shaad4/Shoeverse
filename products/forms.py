from django import forms 
from .models import  Product, ProductVariant


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'old_price', 'color', 'category', 'is_active' ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full p-2 rounded-md bg-[#121212] text-white border border-border focus:outline-none focus:ring-2 focus:ring-green-600'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full p-2 rounded-md bg-[#121212] text-white border border-border focus:outline-none focus:ring-2 focus:ring-green-600',
                'rows': 3
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full p-2 rounded-md bg-[#121212] text-white border border-border focus:outline-none focus:ring-2 focus:ring-green-600'
            }),
            'old_price': forms.NumberInput(attrs={
                'class': 'w-full p-2 rounded-md bg-[#121212] text-white border border-border focus:outline-none focus:ring-2 focus:ring-green-600'
            }),
            'color': forms.TextInput(attrs={
                'class': 'w-full p-2 rounded-md bg-[#121212] text-white border border-border focus:outline-none focus:ring-2 focus:ring-green-600'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full p-2 rounded-md bg-[#121212] text-white border border-border focus:outline-none focus:ring-2 focus:ring-green-600'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'accent-green-600 scale-110'
            }),
        }


class  ProductVarientForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['size','stock','is_active']
        widgets = {
            'size': forms.TextInput(attrs={
                'class': 'w-full p-2 rounded bg-[#1F1F1F] text-white border border-border'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'w-full p-2 rounded bg-[#1F1F1F] text-white border border-border'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'accent-green-500 scale-110'
            }),
        }