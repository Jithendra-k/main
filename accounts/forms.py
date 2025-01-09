from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        required=True
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class UserProfileUpdateForm(forms.ModelForm):
    birthday = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        required=False
    )

    class Meta:
        model = UserProfile
        fields = ['phone_number', 'birthday', 'address']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Basic phone number validation
            import re
            if not re.match(r'^\+?1?\d{9,15}$', phone):
                raise forms.ValidationError("Enter a valid phone number.")
        return phone