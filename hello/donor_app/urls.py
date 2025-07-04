from django.contrib import admin
from django.urls import path, include
from donor_app import views
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login  # Add this import
from .decorators import role_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render, redirect
from django.contrib import messages
from donor_app.models import LoginActivity
from django.contrib.auth.views import PasswordChangeDoneView  # Add this import

urlpatterns = [
    path("", views.index, name='home'),
    path("login/", views.user_login, name='user_login'),
    path('about/', views.about, name='about'),
    path('register/', views.register, name='register'),
    path('verify-email/<str:uidb64>/<str:token>/', views.verify_email, name='verify-email'),
    path('registration-success/', views.registration_success, name='registration-success'),
    path('verification-success/', views.verification_success, name='verification-success'),
    path('password-change/done/', PasswordChangeDoneView.as_view(template_name='password_change_done.html'), name='password_change_done'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('deactivate-account/', views.deactivate_account, name='deactivate_account'),
    path('login-history/', views.login_history, name='login_history'),
    path('find-donor/', views.find_donor, name='find_donor'),
    # Add other URL patterns as needed
]

def index(request):
    return render(request, 'index.html')

@csrf_protect
def user_login(request):
    if request.user.is_authenticated:
        return redirect('donor_dashboard')  # <-- fix here
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        if not email or not password:
            messages.error(request, "Both email and password are required")
            return render(request, 'login.html')
        user = authenticate(request, username=email, password=password)

        # Log activity
        LoginActivity.objects.create(
            user=user if user else None,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            success=user is not None and user.is_verified
        )
        if user:
            if not user.is_verified:
                messages.warning(request, "Please verify your email before logging in")
                return redirect('resend-verification')
            if user.is_active:
                auth_login(request, user)
                return redirect('donor_dashboard')  # <-- fix here
            dashboard_redirects = {
                'donor': 'donor_dashboard',
                'seeker': 'seeker_dashboard',
            }
            return redirect(dashboard_redirects.get(user.user_type, 'admin-dashboard'))
        messages.error(request, "Invalid email or password")
        return render(request, 'login.html')
    return render(request, 'login.html')