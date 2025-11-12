from django.contrib import admin
from .models import Product, ProductVariant, ProductImage

# Register your models here.

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1   # shows one empty variant row by default
    fields = ("size", "stock", "is_active")
    readonly_fields = ("created_at", "updated_at")
    show_change_link = True

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1   # one empty image field by default
    fields = ("image", "is_primary")
    readonly_fields = ("created_at",)
    show_change_link = True


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "color", "price", "total_stock", "is_active", "created_at")
    list_filter = ("category", "is_active", "color")
    search_fields = ("name", "color", "category")
    inlines = [ProductVariantInline, ProductImageInline]
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


def total_stock(self, obj):
        return obj.total_stock()
total_stock.short_description = "Total Stock"


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "size", "stock", "is_active")
    list_filter = ("is_active",)
    search_fields = ("product__name", "size")


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "is_primary", "created_at")
    list_filter = ("is_primary",)