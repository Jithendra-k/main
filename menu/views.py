# menu/views.py
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Prefetch, Q
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
import json

from .models import Category, MenuItem, ItemChoice, ItemAddon
from .forms import MenuItemForm, CartItemForm, ItemChoiceForm, ItemAddonForm


def menu_list(request):
    """Display the main menu page with categories and items"""
    # Get active categories with prefetched available items
    categories = Category.objects.filter(is_active=True).prefetch_related(
        Prefetch(
            'items',
            queryset=MenuItem.objects.filter(is_available=True)
            .select_related('category')
            .prefetch_related('available_choices', 'available_addons')
        )
    ).order_by('display_order')

    # Get all menu items for search/filter
    menu_items = MenuItem.objects.filter(
        is_available=True,
        category__is_active=True
    ).select_related('category').prefetch_related(
        'available_choices',
        'available_addons'
    )

    # Get search and filter parameters
    search_query = request.GET.get('search', '').strip()
    category_filter = request.GET.get('category')
    spice_level = request.GET.get('spice_level')
    dietary_filters = request.GET.getlist('dietary')

    # Apply filters
    if search_query:
        menu_items = menu_items.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if category_filter:
        menu_items = menu_items.filter(category__slug=category_filter)

    if spice_level:
        menu_items = menu_items.filter(spice_level=spice_level)

    if 'vegetarian' in dietary_filters:
        menu_items = menu_items.filter(is_vegetarian=True)
    if 'vegan' in dietary_filters:
        menu_items = menu_items.filter(is_vegan=True)
    if 'gluten_free' in dietary_filters:
        menu_items = menu_items.filter(is_gluten_free=True)

    # Cart data
    cart = request.session.get('cart', {})

    context = {
        'categories': categories,
        'menu_items': menu_items,
        'spice_levels': MenuItem.SPICE_LEVELS,
        'cart': cart,
        'search_query': search_query,
        'category_filter': category_filter,
        'spice_level': spice_level,
        'dietary_filters': dietary_filters,
    }
    return render(request, 'menu/menu_list.html', context)


def category_detail(request, slug):
    """Display menu items for a specific category"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    menu_items = category.items.filter(is_available=True).select_related('category')

    context = {
        'category': category,
        'menu_items': menu_items,
    }
    return render(request, 'menu/category_detail.html', context)


@require_POST
def add_to_cart(request, item_id):
    try:
        menu_item = get_object_or_404(MenuItem, id=item_id, is_available=True)
        data = json.loads(request.body)

        # Get cart from session or create new one
        cart = request.session.get('cart', {})

        # Get customization details
        choice_id = data.get('choice')
        addon_ids = data.get('addons', [])
        quantity = int(data.get('quantity', 1))
        special_instructions = data.get('special_instructions', '')

        # Calculate item total price
        total_price = menu_item.price
        choice_name = None
        addon_names = []

        # Add choice price if selected
        if choice_id:
            try:
                choice = menu_item.available_choices.get(id=choice_id, is_available=True)
                total_price += choice.price_adjustment
                choice_name = choice.name
            except ObjectDoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Invalid choice selected'})

        # Add addon prices
        for addon_id in addon_ids:
            try:
                addon = menu_item.available_addons.get(id=addon_id, is_available=True)
                total_price += addon.price
                addon_names.append(addon.name)
            except ObjectDoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Invalid addon selected'})

        # Generate unique key for item with customizations
        cart_key = f"{item_id}_{choice_id}_{'-'.join(map(str, sorted(addon_ids)))}"

        # Create cart item
        cart_item = {
            'name': menu_item.name,
            'price': float(total_price),
            'quantity': quantity,
            'choice_id': choice_id,
            'choice_name': choice_name,
            'addon_ids': addon_ids,
            'addon_names': addon_names,
            'special_instructions': special_instructions
        }

        # Update or add to cart
        if cart_key in cart:
            cart[cart_key]['quantity'] += quantity
        else:
            cart[cart_key] = cart_item

        # Save cart to session
        request.session['cart'] = cart
        request.session.modified = True

        return JsonResponse({'status': 'success'})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def get_item_price(request, item_id):
    """Calculate total price based on selected options"""
    try:
        menu_item = get_object_or_404(MenuItem, id=item_id)
        data = json.loads(request.body)
        form = CartItemForm(menu_item, data)

        if form.is_valid():
            total_price = form.get_total_price(menu_item.price)
            return JsonResponse({
                'status': 'success',
                'total_price': float(total_price)
            })
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid options'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


def get_customization_options(request, item_id):
    """Get available customization options for a menu item"""
    try:
        menu_item = get_object_or_404(MenuItem, id=item_id)

        choices = []
        if menu_item.has_choices:
            choices = [{
                'id': choice.id,
                'name': choice.name,
                'price_adjustment': float(choice.price_adjustment)
            } for choice in menu_item.get_available_choices()]

        addons = []
        if menu_item.available_addons.exists():
            addons = [{
                'id': addon.id,
                'name': addon.name,
                'price': float(addon.price)
            } for addon in menu_item.get_available_addons()]

        return JsonResponse({
            'has_choices': menu_item.has_choices,
            'requires_choice': menu_item.requires_choice,
            'choices': choices,
            'addons': addons,
            'has_spice_customization': menu_item.has_spice_customization,
            'spice_level': menu_item.spice_level,
            'spice_levels': dict(MenuItem.SPICE_LEVELS)
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

# menu/views.py

def get_menu_items(request):
    """API endpoint to get menu items for dynamic loading"""
    try:
        category_id = request.GET.get('category')
        search_query = request.GET.get('search', '')

        # Get base queryset
        items = MenuItem.objects.filter(
            is_available=True
        ).select_related('category').prefetch_related(
            'available_choices',
            'available_addons'
        )

        # Apply category filter if specified
        if category_id:
            items = items.filter(category_id=category_id)

        # Apply search filter if provided
        if search_query:
            items = items.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        # Format the data for response
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
                'has_choices': item.has_choices,
                'has_addons': item.available_addons.exists(),
                'has_spice_customization': item.has_spice_customization,
                'is_available': item.is_available
            })

        return JsonResponse({'status': 'success', 'menu_items': menu_items})

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)