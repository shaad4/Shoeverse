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

    # ... [HEADER, LOGO, ADDRESS SECTIONS REMAIN SAME] ...
    # (Paste your existing Header/Address code here)
    
    # [Temporarily recreating context for the loop below]
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
    c.drawString(50, y, f"Order ID: {order.order_id if hasattr(order, 'order_id') else order.id}") # Safety check
    c.drawString(350, y, f"Order Date: {order.created_at.strftime('%d %b %Y')}")
    y -= 20
    c.drawString(50, y, f"Payment Method: {order.payment_method}")
    y -= 40

    # ===== BILLING ADDRESS =====
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Billing Address:")
    y -= 18

    c.setFont("Helvetica", 10)
    # Ensure address exists to prevent errors
    if order.address:
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

    # ===== ORDER ITEMS (UPDATED LOGIC) =====
    c.setFont("Helvetica", 10)
    
    for item in order.items.all():
        if y < 150: 
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

        # --- LOGIC CHANGE HERE ---
        is_cancelled = item.status == 'Cancelled'
        
        if is_cancelled:
            # 1. Grey out text
            c.setFillColorRGB(0.5, 0.5, 0.5) 
            # 2. Add marker to name
            item_name = f"{item.variant.product.name[:25]} (CANCELLED)"
            # 3. Set Total to 0.00 so columns sum up correctly
            line_total_str = "Rs. 0.00"
        else:
            # Normal Item
            c.setFillColorRGB(0, 0, 0)
            item_name = item.variant.product.name[:30]
            item_total = item.price * item.quantity
            line_total_str = f"Rs.{item_total}"

        # Draw the Row
        c.drawString(50, y, item_name)
        c.drawString(260, y, str(item.quantity))
        c.drawString(310, y, f"Rs.{item.price}")
        c.drawString(380, y, line_total_str)
        
        # Optional: Draw a strikethrough line for cancelled items
        if is_cancelled:
            c.setStrokeColorRGB(0.5, 0.5, 0.5)
            c.line(50, y + 4, 450, y + 4) # Draw line through text
            c.setStrokeColorRGB(0, 0, 0)   # Reset stroke color

        y -= 18
        
        # Reset fill color for next loop iteration
        c.setFillColorRGB(0, 0, 0) 

    # ===== SUMMARY SECTION =====
    y -= 10
    c.line(300, y, 550, y)
    y -= 20

    # 1. Calculations
    subtotal = order.subtotal
    discount = order.discount_amount if order.discount_amount else Decimal("0.00")
    gst = order.gst
    delivery_charge = order.delivery_charge
    total_payable = order.total_amount

    summary_data = [
        ("Subtotal", subtotal),
    ]

    if discount > 0:
        coupon_label = f"Discount ({order.coupon.code})" if order.coupon else "Discount"
        summary_data.append((coupon_label, -discount))

    summary_data.extend([
        ("GST (18%)", gst),
        ("Delivery", delivery_charge),
        ("Grand Total", total_payable),
    ])

    # 4. Render Summary
    c.setFont("Helvetica-Bold", 11)
    for label, value in summary_data:
        c.drawString(310, y, f"{label}:")
        
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
