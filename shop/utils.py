from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from  django.conf import settings
import os
from reportlab.lib import colors
from io import BytesIO
from django.http import HttpResponse
from decimal import Decimal
from shop.models import CartItem


def generate_invoice(order):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    # ===== HEADER & LOGO =====
    logo_path = os.path.join(settings.BASE_DIR, "static", "images", "logo.png")
    if os.path.exists(logo_path):
        c.drawImage(logo_path, 50, y - 60, width=70, height=70, preserveAspectRatio=True, mask='auto')

    c.setFont("Helvetica-Bold", 24)
    c.drawString(140, y - 20, "Shoeverse")
    c.setFont("Helvetica", 11)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawString(140, y - 40, "Premium Footwear, Delivered With Care")
    c.setFillColorRGB(0, 0, 0)
    y -= 100

    # ===== INVOICE & ORDER STATUS =====
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "INVOICE")
    
    status_text = f"Order Status: {order.status.upper()}"
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(550, y, status_text)
    y -= 30

    # ===== ORDER DETAILS & ADDRESS =====
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Order ID: {order.order_id}")
    c.drawString(350, y, f"Order Date: {order.created_at.strftime('%d %b %Y')}")
    y -= 20
    c.drawString(50, y, f"Payment Method: {order.payment_method}")
    y -= 40

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Billing Address:")
    y -= 18
    c.setFont("Helvetica", 10)
    if order.address:
        for line in [order.address.full_name, order.address.address_line1, order.address.address_line2, 
                     f"{order.address.city}, {order.address.state} - {order.address.pincode}", f"Phone: {order.address.phone_number}"]:
            if line:
                c.drawString(50, y, line)
                y -= 15
    y -= 25

    # ===== TABLE HEADER =====
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Item Description")
    c.drawString(240, y, "Status")
    c.drawString(320, y, "Qty")
    c.drawString(380, y, "Unit Price")
    c.drawString(480, y, "Total")
    y -= 8
    c.line(50, y, 550, y)
    y -= 18

    # ===== NEW CALCULATION LOGIC FOR ACTIVE SUMMARY =====
    active_subtotal = Decimal('0.00')

    # ===== ORDER ITEMS LOOP =====
    c.setFont("Helvetica", 9)
    for item in order.items.all():
        if y < 100:
            c.showPage()
            y = height - 50

        is_inactive = item.status in ['Cancelled', 'Returned']
        
        if is_inactive:
            c.setFillColorRGB(0.5, 0.5, 0.5)
            line_total = Decimal('0.00')
        else:
            c.setFillColorRGB(0, 0, 0)
            line_total = item.price * item.quantity
            # Add to our dynamic subtotal for the summary section
            active_subtotal += line_total

        item_name = f"{item.variant.product.name[:30]} (Size: {item.variant.size})"
        
        c.drawString(50, y, item_name)
        c.drawString(240, y, item.status) 
        c.drawString(320, y, str(item.quantity))
        c.drawString(380, y, f"Rs. {item.price:,.2f}")
        c.drawRightString(530, y, f"Rs. {line_total:,.2f}")

        if is_inactive:
            c.setStrokeColorRGB(0.5, 0.5, 0.5)
            c.line(50, y + 3, 530, y + 3)
            c.setStrokeColorRGB(0, 0, 0)

        y -= 18

    # ===== DYNAMIC SUMMARY CALCULATION =====
    # Calculate tax based only on the active subtotal
    active_gst = (active_subtotal * Decimal('0.18')).quantize(Decimal('0.01'))
    
    # We maintain the delivery charge and subtract the original coupon discount
    # but ensure the final total doesn't drop below zero.
    active_total = (active_subtotal + active_gst + order.delivery_charge - order.discount_amount).max(Decimal('0.00'))

    # ===== SUMMARY SECTION =====
    c.setFillColorRGB(0, 0, 0)
    y -= 10
    c.line(300, y, 550, y)
    y -= 20
    
    summary_data = [
        ("Active Subtotal", active_subtotal),
        ("GST (18%)", active_gst),
        ("Delivery", order.delivery_charge),
    ]
    
    if order.discount_amount > 0:
        summary_data.insert(1, (f"Discount ({order.coupon.code if order.coupon else 'Coupon'})", -order.discount_amount))

    c.setFont("Helvetica", 11)
    for label, value in summary_data:
        c.drawString(320, y, f"{label}:")
        if value < 0: c.setFillColorRGB(0.8, 0, 0)
        c.drawRightString(530, y, f"Rs. {abs(value):,.2f}")
        c.setFillColorRGB(0, 0, 0)
        y -= 18

    c.line(300, y, 550, y)
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(320, y, "Grand Total:")
    c.drawRightString(530, y, f"Rs. {active_total:,.2f}")

    # Footer
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(width/2, 50, "Thank you for shopping with Shoeverse!")
    c.save()
    buffer.seek(0)
    return buffer


# def get_cart_totals(user):
#     cart_items = CartItem.objects.filter(user=user, variant__is_active = True, variant__product__is_active=True)

#     if not cart_items.exists():
#         return None
    
#     subtotal = sum(item.total_price for item in cart_items)
#     gst = (subtotal * Decimal("0.18")).quantize(Decimal("0.01"))
#     delivery_charge = Decimal("0")

#     discount_amount = Decimal("0")
#     coupon_code = None

#     applied_coupon = None

#     return{
#         "cart_items" : cart_items,
#         "subtotal" : subtotal,
#         "gst" : gst,
#         "delivery_charge" : delivery_charge,
#         "base_total" : subtotal+gst+delivery_charge
#     }


from decimal import Decimal

GST_RATE = Decimal("0.18")

def get_cart_totals(user):
    cart_items = CartItem.objects.filter(
        user=user,
        variant__is_active=True,
        variant__product__is_active=True,
        variant__stock__gt=0
    )

    if not cart_items.exists():
        return None

    # 1. Subtotal
    subtotal = sum(item.total_price for item in cart_items)
    subtotal = subtotal.quantize(Decimal("0.01"))

    # 2. No discount here (handled in checkout/place_order)
    discount_amount = Decimal("0.00")

    # 3. Taxable amount = subtotal
    taxable_amount = subtotal

    # 4. GST (display only, NOT final)
    gst = (taxable_amount * GST_RATE).quantize(Decimal("0.01"))

    # 5. Delivery
    delivery_charge = Decimal("0.00") if subtotal >= Decimal("1000") else Decimal("100.00")

    # 6. Total (pre-discount)
    grand_total = (taxable_amount + gst + delivery_charge).quantize(Decimal("0.01"))

    return {
        "cart_items": cart_items,
        "subtotal": subtotal,
        "discount_amount": discount_amount,   
        "taxable_amount": taxable_amount,
        "gst": gst,
        "delivery_charge": delivery_charge,
        "base_total": grand_total,
    }
