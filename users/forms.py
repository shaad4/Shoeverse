# from django import forms
# from .models import User

# class ProfileForm(forms.ModelForm):
#     class Meta:
#         model = User
#         fields = ['fullName', 'phoneNumber', 'profileImage', 'dateOfBirth', 'gender']

#         widgets = {
#             'fullName': forms.TextInput(attrs={
#                 'class': 'w-full bg-input-bg border border-input-border p-2 rounded-lg text-gray-200 focus:ring-2 focus:ring-primary',
#                 'placeholder': 'Full Name'
#             }),

#             'phoneNumber': forms.TextInput(attrs={
#                 'class': 'w-full bg-input-bg border border-input-border p-2 rounded-lg text-gray-200 focus:ring-2 focus:ring-primary',
#                 'placeholder': 'Phone Number'
#             }),

#             # 👉 Hide file input completely (we will click the image instead)
#             'profileImage': forms.ClearableFileInput(attrs={
#                 'class': 'hidden',
#                 'accept': 'image/*'
#             }),

#             'dateOfBirth': forms.DateInput(attrs={
#                 'class': 'w-full bg-input-bg border border-input-border p-2 rounded-lg text-gray-200 focus:ring-2 focus:ring-primary',
#                 'type': 'date',
#             }),

#             'gender': forms.Select(attrs={
#                 'class': 'w-full bg-input-bg border border-input-border p-2 rounded-lg text-gray-200 focus:ring-2 focus:ring-primary'
#             }),
#         }
