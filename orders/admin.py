# orders/admin.py
from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['menu_item']
    extra = 1
    readonly_fields = ['price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'name', 'email', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ('created_at', 'updated_at')  # Changed to tuple
    inlines = [OrderItemInline]
    fieldsets = (
        ('Customer Information', {
            'fields': ('user', 'name', 'email', 'phone', 'address')
        }),
        ('Order Information', {
            'fields': ('status', 'total_amount', 'special_instructions')
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