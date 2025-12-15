import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden

from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils import timezone
from adminpanel.decorator import admin_required
from users.decorator import user_required
from .models import SupportTicket, SupportMessage


# -------------------------
# Helpers
# -------------------------
def get_ticket_safe(request, ticket_id):
    if request.user.is_staff:
        return get_object_or_404(SupportTicket, id=ticket_id)
    return get_object_or_404(SupportTicket, id=ticket_id, user=request.user)


# -------------------------
# USER SIDE
# -------------------------
@user_required
def create_ticket(request):
    if request.method == "POST":
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        if not subject or not message:
            return redirect("create_ticket")

        with transaction.atomic():
            ticket = SupportTicket.objects.create(
                user=request.user,
                subject=subject
            )
            SupportMessage.objects.create(
                ticket=ticket,
                user=request.user,
                message=message
            )

        return redirect("ticket_chat", ticket_id=ticket.id)

    return render(request, "support/create_ticket.html")


@user_required
def my_tickets(request):
    tickets = SupportTicket.objects.filter(user=request.user).order_by("-updated_at")

    return render(request, "support/my_tickets.html", {
        "tickets": tickets,
        "open_count": tickets.exclude(status="RESOLVED").count(),
        "resolved_count": tickets.filter(status="RESOLVED").count(),
    })


@user_required
def ticket_chat(request, ticket_id):
    ticket = get_ticket_safe(request, ticket_id)
    chat_messages = ticket.messages.select_related("user").order_by("created_at")

    return render(request, "support/chat.html", {
        "ticket": ticket,
        "chat_messages": chat_messages
    })


# -------------------------
# SHARED API
# -------------------------

@require_POST
def send_message(request, ticket_id):
    ticket = get_ticket_safe(request, ticket_id)

    if ticket.status == "RESOLVED" and not request.user.is_staff:
        return JsonResponse({"error": "Ticket is closed"}, status=403)

    data = json.loads(request.body)
    message_text = data.get("message", "").strip()

    if not message_text:
        return JsonResponse({"error": "Empty message"}, status=400)

    SupportMessage.objects.create(
        ticket=ticket,
        user=request.user,
        message=message_text
    )

    if request.user.is_staff and ticket.status == "OPEN":
        ticket.status = "IN_PROGRESS"
        ticket.save(update_fields=["status", "updated_at"])

    return JsonResponse({"status": "success"})



def get_messages(request, ticket_id):
    ticket = get_ticket_safe(request, ticket_id)

    data = [
        {
            "id": m.id,
            "sender": "ADMIN" if m.user and m.user.is_staff else "USER",
            "message": m.message,
            "created_at": timezone.localtime(m.created_at).strftime("%H:%M")
        }
        for m in ticket.messages.select_related("user").order_by("created_at")
    ]

    return JsonResponse({"messages": data})


# -------------------------
# ADMIN SIDE
# -------------------------
@admin_required
def staff_dashboard(request):
    tickets = SupportTicket.objects.all().order_by("status", "-updated_at")

    return render(request, "adminpanel/staff_dashboard.html", {
        "tickets": tickets,
        "active_page": "support"
    })


@admin_required
def admin_ticket_chat(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id)
    chat_messages = ticket.messages.select_related("user").order_by("created_at")

    if request.method == "POST":
        ticket.status = "RESOLVED"
        ticket.save(update_fields=["status", "updated_at"])
        return redirect("admin_ticket_chat", ticket_id=ticket.id)

    return render(request, "adminpanel/admin_chat.html", {
        "ticket": ticket,
        "chat_messages": chat_messages,
        "active_page": "support"
    })
