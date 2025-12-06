from django.shortcuts import render
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.http import HttpResponse
from django.utils import timezone
import openpyxl
import io

def render_pdf_view(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    response = HttpResponse(content_type="application/pdf")

    filename = f"sales_report_{timezone.now().strftime('%Y-%m-%d')}.pdf"
    response['Content-Disposition'] = f"attachment; filename={filename}"
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors<pre>' + html +  '</pre>')
    
    return response


def render_excel_view(orders):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Sales Report"

    headers =  ["Order ID", "Date", "Customer", "Payment Method", "subtotal", "Tax", "Delivery", "Discount", "Grand Total", "Status", "Coupon Code"]
    sheet.append(headers)

    for order in orders:
        created_at = order.created_at.replace(tzinfo=None) if order.created_at else ""
        coupon_code = order.coupon.code if order.coupon else "N/A"

        row = [
            order.order_id,
            created_at,
            order.user.fullName,
            order.payment_method,
            float(order.subtotal),
            float(order.gst),
            float(order.delivery_charge),
            float(order.discount_amount),
            float(order.total_amount),
            order.status,
            coupon_code

        ]
        sheet.append(row)

        

    response = HttpResponse(content_type  = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"sales_report_{timezone.now().strftime('%Y-%m-%d')}.xlsx"
    response['Content-Disposition'] = f"attachment; filename={filename}"
    workbook.save(response)
    return response
    

