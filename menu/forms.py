# menu/forms.py
from django import forms
from .models import MenuItem, ItemChoice, ItemAddon, Category
from decimal import Decimal


class ItemChoiceForm(forms.ModelForm):
    """Form for creating/editing menu item choices"""

    class Meta:
        model = ItemChoice
        fields = ['name', 'description', 'price_adjustment', 'is_available']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'price_adjustment': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def clean_price_adjustment(self):
        price_adjustment = self.cleaned_data['price_adjustment']
        if price_adjustment < Decimal('0'):
            raise forms.ValidationError("Price adjustment cannot be negative.")
        return price_adjustment


class ItemAddonForm(forms.ModelForm):
    """Form for creating/editing menu item add-ons"""

    class Meta:
        model = ItemAddon
        fields = ['name', 'description', 'price', 'is_available']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'price': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def clean_price(self):
        price = self.cleaned_data['price']
        if price < Decimal('0'):
            raise forms.ValidationError("Price cannot be negative.")
        return price


class MenuItemForm(forms.ModelForm):
    """Form for creating/editing menu items"""

    class Meta:
        model = MenuItem
        fields = [
            'category', 'name', 'description', 'price', 'image',
            'is_available', 'is_featured', 'is_vegetarian', 'is_vegan',
            'is_gluten_free', 'has_spice_customization', 'spice_level',
            'has_choices', 'requires_choice', 'available_choices',
            'available_addons', 'ingredients', 'allergens',
            'preparation_time', 'calories'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'ingredients': forms.Textarea(attrs={'rows': 3}),
            'allergens': forms.Textarea(attrs={'rows': 2}),
            'available_choices': forms.CheckboxSelectMultiple(),
            'available_addons': forms.CheckboxSelectMultiple(),
            'price': forms.NumberInput(attrs={'step': '0.01'}),
            'preparation_time': forms.NumberInput(attrs={'min': '1', 'max': '120'}),
            'calories': forms.NumberInput(attrs={'min': '0'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        has_choices = cleaned_data.get('has_choices')
        requires_choice = cleaned_data.get('requires_choice')
        available_choices = cleaned_data.get('available_choices')

        if has_choices and not available_choices:
            raise forms.ValidationError(
                "You must select at least one choice option if choices are enabled."
            )

        if requires_choice and not has_choices:
            raise forms.ValidationError(
                "You cannot require choices if choices are not enabled."
            )

        return cleaned_data

    def clean_price(self):
        price = self.cleaned_data['price']
        if price < Decimal('0'):
            raise forms.ValidationError("Price cannot be negative.")
        return price


class CategoryForm(forms.ModelForm):
    """Form for creating/editing menu categories"""

    class Meta:
        model = Category
        fields = ['name', 'description', 'image', 'is_active', 'display_order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'display_order': forms.NumberInput(attrs={'min': '0'}),
        }

    def clean_display_order(self):
        display_order = self.cleaned_data['display_order']
        if display_order < 0:
            raise forms.ValidationError("Display order cannot be negative.")
        return display_order


class CartItemForm(forms.Form):
    """Form for adding menu items to cart with customizations"""
    quantity = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm quantity-input',
            'onchange': 'updateTotalPrice(this)'
        })
    )

    choice = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select choice-select',
            'onchange': 'updateTotalPrice(this)'
        })
    )

    addons = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'addon-checkbox',
            'onchange': 'updateTotalPrice(this)'
        })
    )

    spice_level = forms.ChoiceField(
        choices=MenuItem.SPICE_LEVELS,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select spice-level-select'
        })
    )

    special_instructions = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'class': 'form-control',
            'placeholder': 'Any special instructions?'
        })
    )

    def __init__(self, menu_item, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set up choices field if applicable
        if menu_item.has_choices:
            self.fields['choice'].queryset = menu_item.get_available_choices()
            if menu_item.requires_choice:
                self.fields['choice'].required = True
                self.fields['choice'].empty_label = "Select an option (Required)"
            else:
                self.fields['choice'].empty_label = "Select an option (Optional)"
        else:
            self.fields['choice'].widget = forms.HiddenInput()

        # Set up add-ons field
        if menu_item.available_addons.exists():
            self.fields['addons'].queryset = menu_item.get_available_addons()
        else:
            self.fields['addons'].widget = forms.HiddenInput()

        # Set up spice level field
        if not menu_item.has_spice_customization:
            self.fields['spice_level'].widget = forms.HiddenInput()
            self.fields['spice_level'].initial = menu_item.spice_level
        else:
            self.fields['spice_level'].initial = menu_item.spice_level

    def get_total_price(self, base_price):
        """Calculate total price including choices and add-ons"""
        if not self.is_valid():
            return base_price

        total = base_price

        # Add choice price adjustment
        choice = self.cleaned_data.get('choice')
        if choice:
            total += choice.price_adjustment

        # Add selected add-ons
        addons = self.cleaned_data.get('addons', [])
        for addon in addons:
            total += addon.price

        # Multiply by quantity
        quantity = self.cleaned_data.get('quantity', 1)
        total *= quantity

        return total

    def get_item_summary(self):
        """Get a text summary of the customizations"""
        if not self.is_valid():
            return ""

        summary_parts = []

        # Add choice if selected
        choice = self.cleaned_data.get('choice')
        if choice:
            summary_parts.append(f"Choice: {choice.name}")

        # Add selected add-ons
        addons = self.cleaned_data.get('addons', [])
        if addons:
            addon_names = [addon.name for addon in addons]
            summary_parts.append(f"Add-ons: {', '.join(addon_names)}")

        # Add spice level if customized
        spice_level = self.cleaned_data.get('spice_level')
        if spice_level:
            summary_parts.append(f"Spice: {dict(MenuItem.SPICE_LEVELS)[spice_level]}")

        # Add special instructions if any
        special_instructions = self.cleaned_data.get('special_instructions')
        if special_instructions:
            summary_parts.append(f"Instructions: {special_instructions}")

        return " | ".join(summary_parts)