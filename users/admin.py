from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User
# Register your models here.


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("email", "fullName", "role", "is_staff", "is_active", "createdAt")
    list_filter = ("role", "is_staff", "is_active")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("fullName", "phoneNumber", "profileImage", "dateOfBirth", "gender")}),
        ("Permissions", {"fields": ("role", "is_staff", "is_active", "is_superuser")}),
        ("Important Dates", {"fields": ("last_login", "createdAt", "updatedAt")}),
        ("Referral", {"fields": ("referralCode", "referredBy")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "fullName", "password1", "password2", "role", "is_staff", "is_active"),
        }),
    )

    search_fields = ("email", "fullName", "referralCode")
    ordering = ("-createdAt",)
    readonly_fields = ("createdAt", "updatedAt")











admin.site.register(User, CustomUserAdmin)
