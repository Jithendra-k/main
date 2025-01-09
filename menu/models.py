# menu/models.py
from django.db import models
from django.urls import reverse

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)  # For ordering categories in the menu

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('menu:category_detail', args=[self.slug])

class MenuItem(models.Model):
    category = models.ForeignKey(Category, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    ingredients = models.TextField(blank=True, help_text="Enter the ingredients used in this dish")
    spice_level = models.CharField(max_length=20, choices=[
        ('mild', 'Mild'),
        ('medium', 'Medium'),
        ('spicy', 'Spicy'),
        ('very_spicy', 'Very Spicy')
    ], default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('menu:menu_item_detail', args=[self.slug])