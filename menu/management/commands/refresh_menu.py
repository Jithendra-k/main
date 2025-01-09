# menu/management/commands/refresh_menu.py
from django.core.management.base import BaseCommand
from menu.models import Category, MenuItem
import json
import os
from django.conf import settings
from django.db import transaction, connection


class Command(BaseCommand):
    help = 'Refresh menu items from fixture data'

    def handle(self, *args, **kwargs):
        fixture_path = os.path.join(settings.BASE_DIR, 'menu', 'fixtures', 'initial_menu.json')

        try:
            with open(fixture_path, 'r') as file:
                fixture_data = json.load(file)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Fixture file not found at {fixture_path}'))
            return

        with transaction.atomic():
            # Check if OrderItem model exists and has any data
            from django.apps import apps
            if apps.is_installed('orders'):
                OrderItem = apps.get_model('orders', 'OrderItem')
                if OrderItem._meta.db_table in connection.introspection.table_names():
                    self.stdout.write('Clearing existing order items...')
                    OrderItem.objects.all().delete()

            # Clear existing menu data
            self.stdout.write('Clearing existing menu data...')
            MenuItem.objects.all().delete()
            Category.objects.all().delete()

            # Load new data
            self.stdout.write('Loading new menu data...')
            categories = {}
            category_index = 1  # Counter for categories

            # Create categories first
            category_items = [item for item in fixture_data if item['model'] == 'menu.category']
            for item in category_items:
                category = Category.objects.create(
                    name=item['fields']['name'],
                    slug=item['fields']['slug'],
                    description=item['fields'].get('description', ''),
                    is_active=item['fields'].get('is_active', True),
                    display_order=item['fields'].get('display_order', 0)
                )
                # Store category with its slug as key
                categories[item['fields']['slug']] = category
                self.stdout.write(f'Created category: {category.name}')

            # Create menu items
            menu_items = [item for item in fixture_data if item['model'] == 'menu.menuitem']
            for item in menu_items:
                fields = item['fields']
                # Find the category by matching the category index to the correct category
                category_slug = next(
                    cat['fields']['slug'] for cat in category_items
                    if cat['fields']['display_order'] == fields['category']
                )
                category = categories[category_slug]

                menu_item = MenuItem.objects.create(
                    category=category,
                    name=fields['name'],
                    slug=fields['slug'],
                    description=fields['description'],
                    price=fields['price'],
                    image=fields.get('image', ''),
                    is_available=fields.get('is_available', True),
                    is_featured=fields.get('is_featured', False),
                    spice_level=fields.get('spice_level', 'medium')
                )
                self.stdout.write(f'Created menu item: {menu_item.name}')

        self.stdout.write(self.style.SUCCESS('Successfully refreshed menu data'))