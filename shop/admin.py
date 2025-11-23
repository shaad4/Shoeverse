from django.contrib import admin
from .models import ReturnRequest
from django.utils.html import format_html


# Register your models here.
@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'get_product_name',
        'get_user',
        
        'status',
        'refund_amount',
        
        'pickup_date',
        'requested_at',
    )

    list_filter = (
        
        'status',
        
        'requested_at',
    )

    search_fields = (
        'order_item__variant__product__name',
        'user__email',
        'user__username',
        'reason',
    )

    readonly_fields = (
        'requested_at',
        'updated_at',
        'refund_amount',
        'image_preview1',
        'image_preview2',
        'image_preview3',
    )

    fieldsets = (
        ('Order & User Info', {
            'fields': ('order_item', 'user', 'pickup_address')
        }),
        ('Return Details', {
            'fields': ('reason', 'comments', 'status')
        }),
        ('Images', {
            'fields': ('image1', 'image_preview1', 'image2', 'image_preview2', 'image3', 'image_preview3'),
            'classes': ('collapse',)
        }),
        ('Refund Information', {
            'fields': ('refund_amount', 'pickup_date')
        }),
        ('Timestamps', {
            'fields': ('requested_at', 'updated_at')
        }),
    )


    def get_product_name(self, obj):
        return obj.order_item.variant.product.name
    get_product_name.short_description = 'Product'

    def get_user(self, obj):
        return obj.user.email
    get_user.short_description = 'Customer'

    # Image Previews
    def image_preview1(self, obj):
        if obj.image1:
            return format_html('<img src="{}" width="120" style="border-radius:5px" />', obj.image1.url)
        return "-"
    
    def image_preview2(self, obj):
        if obj.image2:
            return format_html('<img src="{}" width="120" style="border-radius:5px" />', obj.image2.url)
        return "-"

    def image_preview3(self, obj):
        if obj.image3:
            return format_html('<img src="{}" width="120" style="border-radius:5px" />', obj.image3.url)
        return "-"

    # Allow editing in list view
    list_editable = ('status',  'pickup_date')

    # Pagination
    list_per_page = 15