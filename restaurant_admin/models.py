# restaurant_admin/models.py
from django.db import models

# restaurant_admin/models.py
class StoreStatus(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('paused', 'Paused'),
        ('closed', 'Closed')
    ]

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Store Status: {self.get_status_display()}"

    @classmethod
    def get_current_status(cls):
        """Get or create the current store status"""
        #print("\n=== Getting Current Store Status -models===")
        status_obj, created = cls.objects.get_or_create(
            id=1,
            defaults={'status': 'open'}
        )
        #print(f"Status object retrieved/created: {status_obj.status} (Created: {created})")
        #print("=== Get Current Status Complete -models===\n")
        return status_obj.status

# restaurant_admin/models.py

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    image = models.ImageField(upload_to='announcements/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    frequency = models.CharField(max_length=20, choices=[
        ('once', 'Show Once'),
        ('daily', 'Show Daily'),
        ('hourly', 'Show Hourly')
    ], default='once')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title