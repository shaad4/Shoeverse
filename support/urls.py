from django.urls import path
from . import views

urlpatterns = [

    # User
    path("create/", views.create_ticket, name="create_ticket"),
    path("my-tickets/", views.my_tickets, name="my_tickets"),
    path("chat/<int:ticket_id>/", views.ticket_chat, name="ticket_chat"),

    # API
    path("api/send/<int:ticket_id>/", views.send_message, name="send_message"),
    path("api/get/<int:ticket_id>/", views.get_messages, name="get_messages"),

    # Admin
    path("support-dashboard/", views.staff_dashboard, name="staff_dashboard"),
    path("admin-chat/<int:ticket_id>/", views.admin_ticket_chat, name="admin_ticket_chat"),
]
