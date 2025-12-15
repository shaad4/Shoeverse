from django.db import models
from django.conf import settings 
import uuid
# Create your models here.


class SupportTicket(models.Model):
    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
    )

    ticket_id = models.CharField(max_length=10, unique= True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tickets")
    subject = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="OPEN")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-generate a unique ticket ID if it doesn't exist
        if not self.ticket_id:
            self.ticket_id = str(uuid.uuid4()).split('-')[0].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"#{self.ticket_id} - {self.subject}"
    

class SupportMessage(models.Model):
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete = models.CASCADE,
        related_name = "messages"
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message on {self.ticket.ticket_id}"
    

