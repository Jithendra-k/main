# menu/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Category, MenuItem
from django.db.models import Prefetch


def menu_list(request):
    # """Display all menu items grouped by category"""
    # # Debug prints
    # print("\n=== Debug Information ===")
    #
    # categories = Category.objects.filter(is_active=True).order_by('display_order')
    # print("Categories:", [f"{c.name} (Order: {c.display_order})" for c in categories])
    #
    # menu_items = MenuItem.objects.filter(is_available=True).select_related('category')
    # print("Menu Items:", [f"{item.name} (Category: {item.category.name})" for item in menu_items])
    #
    # print("=== End Debug Info ===\n")
    # ...

    """Display all menu items grouped by category"""
    # Get categories ordered by display_order with prefetched items
    categories = Category.objects.filter(is_active=True).order_by('display_order').prefetch_related(
        Prefetch(
            'items',
            queryset=MenuItem.objects.filter(is_available=True)
        )
    )

    # Get all available menu items
    menu_items = MenuItem.objects.filter(is_available=True).select_related('category')

    # Get cart from session
    cart = request.session.get('cart', {})

    context = {
        'categories': categories,
        'menu_items': menu_items,
        'cart': cart,
    }
    return render(request, 'menu/menu_list.html', context)


def category_detail(request, slug):
    """Display menu items for a specific category"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    menu_items = category.items.filter(is_available=True)

    context = {
        'category': category,
        'menu_items': menu_items,
    }
    return render(request, 'menu/category_detail.html', context)


def get_menu_items(request):
    """API endpoint to get menu items for dynamic loading"""
    category_id = request.GET.get('category')
    search_query = request.GET.get('search', '')

    items = MenuItem.objects.filter(is_available=True)

    if category_id:
        items = items.filter(category_id=category_id)

    if search_query:
        items = items.filter(name__icontains=search_query)

    menu_items = []
    for item in items:
        menu_items.append({
            'id': item.id,
            'name': item.name,
            'description': item.description,
            'price': str(item.price),
            'image_url': item.image.url if item.image else None,
            'category': item.category.name,
            'spice_level': item.get_spice_level_display(),
        })

    return JsonResponse({'menu_items': menu_items})