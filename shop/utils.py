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
from reportlab.lib.colors import HexColor


def generate_invoice(order):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Modern Color Palette
    PRIMARY = HexColor("#0F172A")    
    ACCENT = HexColor("#4F46E5")     
    TEXT_MAIN = HexColor("#1E293B")  
    TEXT_MUTE = HexColor("#64748B")  
    BG_SOFT = HexColor("#F8FAFC")    
    BORDER = HexColor("#E2E8F0")     

    # Strict Alignment Constants
    COL_DESC = 50
    COL_STATUS = 310
    COL_QTY = 380
    COL_PRICE = 440
    COL_TOTAL = 550  

    # 1. TOP ACCENT BAR
    c.setFillColor(ACCENT)
    c.rect(0, height - 4, width, 4, fill=1, stroke=0)

    # 2. HEADER
    y = height - 50
    # Update this path to your actual logo location
    logo_path = os.path.join(settings.BASE_DIR, "static", "images", "logo.png")
    if os.path.exists(logo_path):
        c.drawImage(logo_path, COL_DESC, y - 15, width=45, height=45, mask='auto')
    
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(PRIMARY)
    c.drawString(105, y, "SHOEVERSE")
    
    c.setFont("Helvetica", 9)
    c.setFillColor(TEXT_MUTE)
    c.drawString(105, y - 14, "PREMIUM FOOTWEAR CONCEPTS")

    # Invoice Meta
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(PRIMARY)
    c.drawRightString(COL_TOTAL, y, f"INVOICE #{order.order_id}")
    c.setFont("Helvetica", 9)
    c.setFillColor(TEXT_MUTE)
    c.drawRightString(COL_TOTAL, y - 14, f"Issued: {order.created_at.strftime('%d %b %Y')}")

    # 3. ADDRESS SECTION
    y -= 80
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(TEXT_MUTE)
    c.drawString(COL_DESC, y, "BILL TO")
    
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(TEXT_MAIN)
    y_addr = y - 18
    if order.address:
        c.drawString(COL_DESC, y_addr, order.address.full_name.upper())
        c.setFont("Helvetica", 9)
        c.setFillColor(TEXT_MUTE)
        addr_lines = [
            order.address.address_line1,
            f"{order.address.city}, {order.address.state} {order.address.pincode}",
            f"Phone: {order.address.phone_number}"
        ]
        for line in addr_lines:
            y_addr -= 13
            c.drawString(COL_DESC, y_addr, line)

    # Payment Status Box
    c.setFillColor(BG_SOFT)
    c.roundRect(400, y - 45, 150, 45, 5, fill=1, stroke=0)
    c.setFillColor(TEXT_MUTE)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(410, y - 15, "PAYMENT METHOD")
    c.setFillColor(TEXT_MAIN)
    c.setFont("Helvetica", 9)
    c.drawString(410, y - 30, str(order.payment_method).upper())

    # 4. TABLE HEADER
    y -= 100
    c.setStrokeColor(PRIMARY)
    c.setLineWidth(1)
    c.line(COL_DESC, y, COL_TOTAL, y)
    
    y -= 15
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(PRIMARY)
    c.drawString(COL_DESC, y, "DESCRIPTION")
    c.drawString(COL_STATUS, y, "STATUS")
    c.drawString(COL_QTY, y, "QTY")
    c.drawString(COL_PRICE, y, "UNIT PRICE")
    c.drawRightString(COL_TOTAL, y, "TOTAL (INR)") # Label updated
    
    y -= 8
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(COL_DESC, y, COL_TOTAL, y)

    # 5. ITEMS
    y -= 20
    active_subtotal = Decimal("0.00")
    
    for item in order.items.all():
        if y < 150:
            c.showPage()
            y = height - 50

        inactive = item.status in ["Cancelled", "Returned"]
        line_total = (item.price * item.quantity) if not inactive else Decimal("0.00")
        if not inactive: active_subtotal += line_total

        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(TEXT_MAIN if not inactive else TEXT_MUTE)
        c.drawString(COL_DESC, y, item.variant.product.name[:38])
        
        c.setFont("Helvetica", 8)
        c.setFillColor(TEXT_MUTE)
        c.drawString(COL_DESC, y - 11, f"SIZE: {item.variant.size}")
        
        c.setFont("Helvetica", 9)
        c.setFillColor(TEXT_MAIN if not inactive else TEXT_MUTE)
        c.drawString(COL_STATUS, y, item.status)
        c.drawString(COL_QTY, y, str(item.quantity))
        c.drawString(COL_PRICE, y, f"{item.price:,.2f}")
        c.drawRightString(COL_TOTAL, y, f"{line_total:,.2f}")
        
        if inactive:
            c.setStrokeColor(TEXT_MUTE)
            c.line(COL_DESC, y + 3, COL_TOTAL, y + 3)

        y -= 35

    # 6. CALCULATIONS
    if order.subtotal > 0:
        gst_ratio = order.gst / order.subtotal
        disc_ratio = order.discount_amount / order.subtotal
    else:
        gst_ratio = disc_ratio = Decimal("0.00")

    active_gst = (active_subtotal * gst_ratio).quantize(Decimal("0.01"))
    active_discount = (active_subtotal * disc_ratio).quantize(Decimal("0.01"))
    active_total = (active_subtotal + active_gst + order.delivery_charge - active_discount).max(0)

    # Summary Block
    y_sum = y - 20
    c.setStrokeColor(BORDER)
    c.line(350, y_sum + 10, COL_TOTAL, y_sum + 10)
    
    summary_items = [
        ("Subtotal", active_subtotal),
        ("GST Tax", active_gst),
        ("Shipping Charge", order.delivery_charge)
    ]
    if active_discount > 0:
        summary_items.insert(1, ("Discount Applied", -active_discount))

    c.setFont("Helvetica", 10)
    for label, val in summary_items:
        c.setFillColor(TEXT_MUTE)
        c.drawString(350, y_sum, label)
        c.setFillColor(TEXT_MAIN)
        c.drawRightString(COL_TOTAL, y_sum, f"{val:,.2f}") # Values here
        y_sum -= 20

    # Grand Total Box (FIXED LINE HERE)
    c.setFillColor(BG_SOFT)
    c.rect(345, y_sum - 10, 215, 30, fill=1, stroke=0)
    
    c.setFillColor(PRIMARY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(355, y_sum, "GRAND TOTAL")
    c.drawRightString(COL_TOTAL, y_sum, f"{active_total:,.2f} INR")

    # 7. FOOTER
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(TEXT_MUTE)
    c.drawCentredString(width/2, 40, "Thank you for choosing Shoeverse. This is a computer-generated invoice.")
    c.drawCentredString(width/2, 30, "Shoeverse India · support@shoeverse.com")

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
