from django import forms 
from .models import  Product, ProductVariant, SubCategory
from django.core.validators import MinValueValidator

class ProductForm(forms.ModelForm):
    price = forms.DecimalField(
        validators=[MinValueValidator(0)],
        widget=forms.NumberInput(attrs={
            'class': 'w-full p-2 rounded-md bg-[#121212] text-white border border-border focus:outline-none focus:ring-2 focus:ring-green-600',
            'min': '0', 
            'step': '0.01'
        })
    )

    class Meta:
        model = Product
        fields = [
            'name',
            'description',
            'price',
            'color',
            'category',
            'subcategory',
            'is_active',
            'highlights',
            'specifications',
        ]

        common_textarea_class = "w-full p-2 rounded-md bg-[#121212] text-white border border-border focus:outline-none focus:ring-2 focus:ring-green-600"

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full p-2 rounded-md bg-[#121212] text-white border border-border focus:outline-none focus:ring-2 focus:ring-green-600'
            }),
            'description': forms.Textarea(attrs={
                'class': common_textarea_class,
                'rows': 3,
                'placeholder': "Enter product description…"
            }),
            # Removed 'price' from widgets since we defined it explicitly above
            'color': forms.TextInput(attrs={
                'class': 'w-full p-2 rounded-md bg-[#121212] text-white border border-border focus:outline-none focus:ring-2 focus:ring-green-600'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full p-2 rounded-md bg-[#121212] text-white border border-border focus:outline-none focus:ring-2 focus:ring-green-600'
            }),
            'subcategory': forms.Select(attrs={
                'class': 'w-full p-2 rounded-md bg-[#121212] text-white border border-border focus:outline-none focus:ring-2 focus:ring-green-600'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'accent-green-600 scale-110'
            }),
            'highlights': forms.Textarea(attrs={
                'class': common_textarea_class,
                'rows': 3,
                'placeholder': "One highlight per line:\n• Breathable mesh\n• Lightweight foam\n• Water-resistant coating"
            }),
            'specifications': forms.Textarea(attrs={
                'class': common_textarea_class,
                'rows': 3,
                'placeholder': "One specification per line:\nWeight: 260 g\nSupport: Neutral\nHeel Drop: 8 mm"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subcategory'].queryset = SubCategory.objects.filter(is_active=True)
        if self.instance and self.instance.category:
            self.fields['subcategory'].queryset = SubCategory.objects.filter(
                category=self.instance.category,
                is_active=True
            )




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