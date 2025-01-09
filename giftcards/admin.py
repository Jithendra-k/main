from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import GiftCard, GiftCardTransaction

@admin.register(GiftCard)
class GiftCardAdmin(admin.ModelAdmin):
    list_display = ['card_number', 'card_id', 'amount', 'balance', 'status', 'purchase_date', 'actions_buttons']
    list_filter = ['status', 'purchase_date']
    search_fields = ['card_number', 'card_id', 'recipient_name', 'recipient_email']
    readonly_fields = ('card_number', 'card_id', 'purchase_date', 'expiry_date')

    def actions_buttons(self, obj):
        validate_url = reverse('giftcards:validate_redeem', args=[obj.card_number])
        return format_html(
            '<a class="button" href="{}">Validate/Redeem</a>',
            validate_url
        )
    actions_buttons.short_description = 'Actions'

@admin.register(GiftCardTransaction)
class GiftCardTransactionAdmin(admin.ModelAdmin):
    list_display = ['gift_card', 'transaction_type', 'amount', 'date', 'user']
    list_filter = ['transaction_type', 'date']
    search_fields = ['gift_card__card_number', 'gift_card__card_id']