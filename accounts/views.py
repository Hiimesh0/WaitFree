"""
Authentication views: unified login, OTP flow, org registration, logout.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.views import View
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from core.utils import generate_otp
from core.roles import CITIZEN, ORGANIZATION, PASSWORD_AUTH_ROLES
from .models import User


class UnifiedLoginView(View):
    """Unified login page with role selection."""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:router')
        return render(request, 'accounts/login.html')

    def post(self, request):
        login_type = request.POST.get('login_type', 'password')

        if login_type == 'otp':
            return redirect('accounts:citizen_otp_request')

        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return render(request, 'accounts/login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.role == CITIZEN:
                messages.error(request, 'Citizens must login using mobile OTP.')
                return render(request, 'accounts/login.html')
            login(request, user)
            return redirect('dashboard:router')
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'accounts/login.html')


class CitizenOTPRequestView(View):
    """Step 1: Citizen enters mobile number, OTP is generated and stored in Redis."""

    def get(self, request):
        return render(request, 'accounts/citizen_otp.html', {'step': 'request'})

    def post(self, request):
        mobile = request.POST.get('mobile_number', '').strip()
        if not mobile or len(mobile) < 10:
            messages.error(request, 'Enter a valid mobile number.')
            return render(request, 'accounts/citizen_otp.html', {'step': 'request'})

        otp = generate_otp()
        cache_key = f'otp:{mobile}'
        cache.set(cache_key, otp, timeout=settings.OTP_EXPIRY_SECONDS)

        # In production, send OTP via SMS. For MVP, display it.
        messages.success(request, f'OTP sent to {mobile}. Your OTP is: {otp}')

        request.session['otp_mobile'] = mobile
        return render(request, 'accounts/citizen_otp.html', {
            'step': 'verify',
            'mobile_number': mobile,
            'otp_display': otp,
        })


class CitizenOTPVerifyView(View):
    """Step 2: Citizen enters OTP, verified against Redis, JWT + session issued."""

    def post(self, request):
        mobile = request.session.get('otp_mobile') or request.POST.get('mobile_number', '').strip()
        otp_entered = request.POST.get('otp', '').strip()

        if not mobile or not otp_entered:
            messages.error(request, 'Mobile number and OTP are required.')
            return redirect('accounts:citizen_otp_request')

        cache_key = f'otp:{mobile}'
        stored_otp = cache.get(cache_key)

        if stored_otp is None:
            messages.error(request, 'OTP expired. Please request a new one.')
            return redirect('accounts:citizen_otp_request')

        if str(stored_otp) != str(otp_entered):
            messages.error(request, 'Invalid OTP. Please try again.')
            return render(request, 'accounts/citizen_otp.html', {
                'step': 'verify',
                'mobile_number': mobile,
            })

        # OTP verified - delete from cache
        cache.delete(cache_key)

        # Get or create citizen user
        user, created = User.objects.get_or_create(
            mobile_number=mobile,
            defaults={
                'username': f'citizen_{mobile}',
                'role': CITIZEN,
            }
        )

        if created:
            user.set_unusable_password()
            user.save()

        # Clean up session
        if 'otp_mobile' in request.session:
            del request.session['otp_mobile']

        login(request, user)
        messages.success(request, 'Login successful!')
        return redirect('dashboard:router')


class OrganizationRegisterView(View):
    """Organization self-registration."""

    def get(self, request):
        return render(request, 'accounts/org_register.html')

    def post(self, request):
        from organizations.models import Organization

        org_name = request.POST.get('org_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        phone = request.POST.get('phone', '').strip()

        errors = []
        if not org_name:
            errors.append('Organization name is required.')
        if not username:
            errors.append('Username is required.')
        if not password or len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != password2:
            errors.append('Passwords do not match.')
        if User.objects.filter(username=username).exists():
            errors.append('Username already taken.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'accounts/org_register.html', {
                'org_name': org_name,
                'username': username,
                'email': email,
                'phone': phone,
            })

        # Create organization
        org = Organization.objects.create(
            name=org_name,
            contact_email=email,
            phone=phone,
        )

        # Create org user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=ORGANIZATION,
            organization=org,
        )

        login(request, user)
        messages.success(request, f'Organization "{org_name}" registered successfully!')
        return redirect('dashboard:router')


class LogoutView(View):
    """Logout and redirect to landing page."""

    def get(self, request):
        logout(request)
        return redirect('landing')

    def post(self, request):
        logout(request)
        return redirect('landing')
