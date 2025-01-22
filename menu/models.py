# menu/models.py


from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('menu:category_detail', args=[self.slug])

    def get_active_items(self):
        return self.items.filter(is_available=True)


class ItemChoice(models.Model):
    """Model for menu item choices (e.g., meat type, size)"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price_adjustment = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        adjustment = f" (+${self.price_adjustment})" if self.price_adjustment > 0 else ""
        return f"{self.name}{adjustment}"


class ItemAddon(models.Model):
    """Model for menu item add-ons (e.g., extra sauce, toppings)"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (${self.price})"


class MenuItem(models.Model):
    SPICE_LEVELS = [
        ('none', 'No Spice'),
        ('mild', 'Mild'),
        ('medium', 'Medium'),
        ('spicy', 'Spicy'),
        ('very_spicy', 'Very Spicy')
    ]

    # Basic Information
    category = models.ForeignKey(Category, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)

    # Status and Features
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_vegetarian = models.BooleanField(default=False)
    is_vegan = models.BooleanField(default=False)
    is_gluten_free = models.BooleanField(default=False)

    # Customization Options
    has_spice_customization = models.BooleanField(
        default=False,
        help_text="Allow customers to customize spice level"
    )
    spice_level = models.CharField(
        max_length=20,
        choices=SPICE_LEVELS,
        default='medium'
    )

    # Choices and Add-ons
    has_choices = models.BooleanField(
        default=False,
        help_text="Item has different choices (e.g., meat type, size)"
    )
    requires_choice = models.BooleanField(
        default=False,
        help_text="Customer must select a choice"
    )
    available_choices = models.ManyToManyField(
        ItemChoice,
        blank=True,
        related_name='menu_items'
    )
    available_addons = models.ManyToManyField(
        ItemAddon,
        blank=True,
        related_name='menu_items'
    )

    # Additional Information
    ingredients = models.TextField(
        blank=True,
        help_text="List main ingredients"
    )
    allergens = models.TextField(
        blank=True,
        help_text="List potential allergens"
    )
    preparation_time = models.PositiveIntegerField(
        default=15,
        help_text="Average preparation time in minutes"
    )
    calories = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Calories per serving"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category', 'is_available']),
            models.Index(fields=['is_featured', 'is_available']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('menu:menu_item_detail', args=[self.slug])

    def get_base_price(self):
        """Get the base price without any choices or add-ons"""
        return self.price

    def get_min_price(self):
        """Get minimum possible price including required choices"""
        if not self.has_choices or not self.requires_choice:
            return self.price

        min_choice_adjustment = self.available_choices.filter(
            is_available=True
        ).aggregate(
            models.Min('price_adjustment')
        )['price_adjustment__min'] or 0

        return self.price + min_choice_adjustment

    def get_max_price(self):
        """Get maximum possible price with all add-ons"""
        max_price = self.price

        if self.has_choices:
            max_choice_adjustment = self.available_choices.filter(
                is_available=True
            ).aggregate(
                models.Max('price_adjustment')
            )['price_adjustment__max'] or 0
            max_price += max_choice_adjustment

        max_addons = self.available_addons.filter(
            is_available=True
        ).aggregate(
            models.Sum('price')
        )['price__sum'] or 0

        return max_price + max_addons

    def get_available_choices(self):
        """Get all available choices for this item"""
        return self.available_choices.filter(is_available=True)

    def get_available_addons(self):
        """Get all available add-ons for this item"""
        return self.available_addons.filter(is_available=True)

    def has_customizations(self):
        """Check if item has any customization options"""
        return (
                self.has_spice_customization or
                self.has_choices or
                self.available_addons.exists()
        )

    def has_dietary_info(self):
        """Check if item has any dietary preference markers"""
        return (
                self.is_vegetarian or
                self.is_vegan or
                self.is_gluten_free
        )