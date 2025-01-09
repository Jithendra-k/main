# menu/utils.py
import json
import os
from django.conf import settings

def load_menu_data():
    """Load menu data from JSON file"""
    json_file_path = os.path.join(settings.BASE_DIR, 'menu', 'fixtures', 'menu_data.json')
    try:
        with open(json_file_path, 'r') as file:
            menu_data = json.load(file)
            return menu_data
    except FileNotFoundError:
        return {"categories": []}

def get_menu_categories():
    """Get all menu categories with their items"""
    menu_data = load_menu_data()
    return menu_data.get('categories', [])

def get_category_items(category_slug):
    """Get items for a specific category"""
    menu_data = load_menu_data()
    for category in menu_data.get('categories', []):
        if category['slug'] == category_slug:
            return category.get('items', [])
    return []