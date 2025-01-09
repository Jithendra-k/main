from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .models import UserProfile, get_or_create_profile, Transaction
from .forms import UserUpdateForm, UserProfileUpdateForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


@login_required
def account_settings(request):
    # Ensure profile exists
    global user_form, profile_form, password_form
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # Check which form was submitted
        if 'update_profile' in request.POST:
            user_form = UserUpdateForm(request.POST, instance=request.user)
            profile_form = UserProfileUpdateForm(request.POST, instance=profile)

            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, 'Your profile has been updated successfully!')
                return redirect('accounts:account_settings')

        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Important!
                messages.success(request, 'Your password was successfully updated!')
                return redirect('accounts:account_settings')
    else:
        # This part ensures the form is pre-filled
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileUpdateForm(instance=profile)
        password_form = PasswordChangeForm(request.user)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'password_form': password_form
    }
    return render(request, 'accounts/account_settings.html', context)

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create profile immediately after user creation
            get_or_create_profile(user)
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('core:home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


# accounts/views.py

@login_required
def transactions(request):
    transactions_list = Transaction.objects.filter(user=request.user).order_by('-created_at')

    paginator = Paginator(transactions_list, 10)  # Show 10 transactions per page
    page = request.GET.get('page')

    try:
        transactions = paginator.page(page)
    except PageNotAnInteger:
        transactions = paginator.page(1)
    except EmptyPage:
        transactions = paginator.page(paginator.num_pages)

    return render(request, 'accounts/transactions.html', {
        'transactions': transactions
    })