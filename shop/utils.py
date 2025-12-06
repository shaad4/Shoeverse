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

    # ===== HEADER (Logo + Title) =====
    logo_path = os.path.join(settings.BASE_DIR, "static", "images", "logo.png")
    if os.path.exists(logo_path):
        c.drawImage(logo_path, 50, y - 60, width=70, height=70, preserveAspectRatio=True, mask='auto')

    c.setFont("Helvetica-Bold", 20)
    c.drawString(140, y - 20, "Shoeverse")

    c.setFont("Helvetica", 11)
    c.drawString(140, y - 40, "Premium Footwear, Delivered With Care")
    y -= 90

    # ===== ORDER DETAILS =====
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "INVOICE")
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Order ID: {order.order_id}")
    c.drawString(350, y, f"Order Date: {order.created_at.strftime('%d %b %Y')}")
    y -= 20
    c.drawString(50, y, f"Payment Method: {order.payment_method}")
    y -= 40

    # ===== BILLING ADDRESS =====
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Billing Address:")
    y -= 18

    c.setFont("Helvetica", 10)
    address_lines = [
        order.address.full_name,
        order.address.address_line1,
        order.address.address_line2,
        f"{order.address.city}, {order.address.state} - {order.address.pincode}",
        f"Phone: {order.address.phone_number}",
    ]
    for line in address_lines:
        if line:
            c.drawString(50, y, line)
            y -= 15

    y -= 15

    # ===== TABLE HEADER =====
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Item")
    c.drawString(260, y, "Qty")
    c.drawString(310, y, "Price")
    c.drawString(380, y, "Total")
    y -= 10
    c.line(50, y, 550, y)
    y -= 15

    # ===== ORDER ITEMS =====
    c.setFont("Helvetica", 10)
    for item in order.items.all():
        if y < 150: # Increased margin to ensure summary fits or new page triggers
            c.showPage()
            y = height - 100
            
            # Reprint header
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y, "Item")
            c.drawString(260, y, "Qty")
            c.drawString(310, y, "Price")
            c.drawString(380, y, "Total")
            y -= 15
            c.line(50, y, 550, y)
            y -= 15

        item_total = item.price * item.quantity
        c.drawString(50, y, item.variant.product.name[:30])
        c.drawString(260, y, str(item.quantity))
        c.drawString(310, y, f"Rs.{item.price}")
        c.drawString(380, y, f"Rs.{item_total}")
        y -= 18

    # ===== SUMMARY SECTION (UPDATED) =====
    y -= 10
    c.line(300, y, 550, y)
    y -= 20

    # 1. Calculations
    subtotal = sum(item.price * item.quantity for item in order.items.all())
    gst = (subtotal * Decimal("0.18")).quantize(Decimal("0.01"))
    delivery_charge = Decimal("0") if subtotal >= Decimal("1000") else Decimal("100")
    
    # Get discount from model
    discount = order.discount_amount if order.discount_amount else Decimal("0.00")
    
    # Final Total Formula
    total_payable = subtotal + gst + delivery_charge - discount

    # 2. Build Summary List
    summary_data = [
        ("Subtotal", subtotal),
        ("GST (18%)", gst),
        ("Delivery", delivery_charge),
    ]

    # 3. Add Discount Row if applicable
    if discount > 0:
        # Show coupon code if available
        coupon_label = f"Discount ({order.coupon.code})" if order.coupon else "Discount"
        summary_data.append((coupon_label, -discount)) # Negative value for clarity

    summary_data.append(("Grand Total", total_payable))

    # 4. Render Summary
    c.setFont("Helvetica-Bold", 11)
    for label, value in summary_data:
        c.drawString(310, y, f"{label}:")
        
        # Color Handling: Red for Discount, Black for others
        if "Discount" in label:
            c.setFillColorRGB(0.8, 0, 0) 
            c.drawString(450, y, f"Rs. {value}")
            c.setFillColorRGB(0, 0, 0)  
        else:
            c.drawString(450, y, f"Rs. {value}")
            
        y -= 18

    y -= 30

    # ===== FOOTER =====
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, y, "Thank you for shopping with Shoeverse! Visit us again at shoeverse.com.")

    c.save()
    buffer.seek(0)
    return buffer


def get_cart_totals(user):
    cart_items = CartItem.objects.filter(user=user, variant__is_active = True, variant__product__is_active=True)

    if not cart_items.exists():
        return None
    
    subtotal = sum(item.total_price for item in cart_items)
    gst = (subtotal * Decimal("0.18")).quantize(Decimal("0.01"))
    delivery_charge = Decimal("0")

    discount_amount = Decimal("0")
    coupon_code = None

    applied_coupon = None

    return{
        "cart_items" : cart_items,
        "subtotal" : subtotal,
        "gst" : gst,
        "delivery_charge" : delivery_charge,
        "base_total" : subtotal+gst+delivery_charge
    }
