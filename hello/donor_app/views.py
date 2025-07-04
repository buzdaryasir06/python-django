from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from .forms import BloodDonorRegistrationForm, UserProfileForm, DonorAvailabilityForm
from .models import User, LoginActivity, Notification
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from django.views.decorators.http import require_POST

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

def about(request):
    return render(request, 'about.html')

def register(request):
    if request.method == 'POST':
        form = BloodDonorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            verification_url = request.build_absolute_uri(
                reverse('verify-email', kwargs={'uidb64': uid, 'token': token})
            )
            send_mail(
                'Verify Your Blood Donor Account',
                f'Please click this link to verify your account: {verification_url}',
                'noreply@yourbloodapp.com',
                [user.email],
                fail_silently=False,
            )
            return redirect('registration-success')
    else:
        form = BloodDonorRegistrationForm()
    return render(request, 'register.html', {'form': form})

def verify_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user and default_token_generator.check_token(user, token):
        user.is_verified = True
        user.save()
        auth_login(request, user)
        return redirect('verification-success')
    return redirect('verification-failed')

def registration_success(request):
    return render(request, 'registration_success.html')

def verification_success(request):
    return render(request, 'verification_success.html')

def verification_failed(request):
    return render(request, 'verification_failed.html')

def find_donor(request):
    return render(request, 'find_donor.html')

class BloodDonorPasswordChangeView(PasswordChangeView):
    template_name = 'password_change.html'
    success_url = reverse_lazy('password_change_done')

class BloodDonor:
    template_name = 'password_change_done.html'

def resend_verification(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            if user.is_verified:
                messages.info(request, "Account is already verified")
                return redirect('login')
            
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            verification_url = request.build_absolute_uri(
                reverse('verify-email', kwargs={'uidb64': uid, 'token': token})
            )
            
            send_mail(
                'Verify Your Blood Donor Account',
                f'Please verify your account: {verification_url}',
                'noreply@yourbloodapp.com',
                [email],
            )
            messages.success(request, "Verification email resent successfully")
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, "No account found with this email")
    
    return render(request, 'resend_verification.html')

@login_required
def deactivate_account(request):
    if request.method == 'POST':
        request.user.is_active = False
        request.user.save()
        logout(request)
        messages.success(request, "Your account has been deactivated")
        return redirect('index')
    
    return render(request, 'deactivate_confirm.html')

@login_required
@role_required(roles=['donor'])
def donor_dashboard(request):
    # Donor-specific view
    pass

@login_required
@role_required(roles=['seeker'])
def seeker_dashboard(request):
    # Seeker-specific view
    pass

@login_required
def login_history(request):
    activities = LoginActivity.objects.filter(user=request.user).order_by('-login_time')
    return render(request, 'login_history.html', {'activities': activities})

@login_required
def profile_view(request):
    user = request.user
    availability_form = DonorAvailabilityForm(instance=user)
    
    context = {
        'user': user,
        'availability_form': availability_form,
        'is_donor': user.user_type == 'donor'
    }
    return render(request, 'profile.html', context)

@login_required
@csrf_protect
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(
            request.POST, 
            request.FILES, 
            instance=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'edit_profile.html', {'form': form})

@login_required
@require_POST
def toggle_availability(request):
    form = DonorAvailabilityForm(request.POST, instance=request.user)
    if form.is_valid():
        user = form.save()
        status = "available" if user.is_available else "unavailable"
        messages.success(request, f'You are now {status} for donation requests')
    else:
        messages.error(request, 'Failed to update availability')
    
    return redirect('profile.html')

# notifications/views.py
from django.http import JsonResponse

@login_required
def notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications.html', {'notifications': notifications})

@login_required
def mark_notification_read(request, id):
    notification = get_object_or_404(Notification, id=id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})

@login_required
def unread_notifications_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})

