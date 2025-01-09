# reservations/admin.py
from django.contrib import admin
from .models import Reservation
from .models import EventType, EventBooking


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'name', 'date', 'time', 'guests', 'status']
    list_filter = ['status', 'date', 'time']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ('created_at', 'updated_at')  # Changed to tuple
    fieldsets = (
        ('Guest Information', {
            'fields': ('user', 'name', 'email', 'phone')
        }),
        ('Reservation Details', {
            'fields': ('date', 'time', 'guests', 'status', 'special_request')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('user',)  # This now concatenates two tuples
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        if not change:  # if creating a new object
            if not obj.user:  # if user is not set
                obj.user = request.user
        super().save_model(request, obj, form, change)


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_price', 'max_capacity']
    search_fields = ['name', 'description']

@admin.register(EventBooking)
class EventBookingAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'name', 'date', 'time', 'guests', 'status']
    list_filter = ['status', 'event_type', 'date']
    search_fields = ['name', 'email', 'phone']