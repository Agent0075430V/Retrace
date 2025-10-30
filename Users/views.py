from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from AI.models import LostProduct, FoundProduct, Notification
from .models import PasswordResetOTP

# Create your views here.
def Login(request):
    if request.method == 'POST':
        username = request.POST.get("Username")  # Match template field name
        password = request.POST.get("Password")  # Match template field name
        if username and password:
            # Authenticate user
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')  # Redirect to dashboard instead of home
            else:
                messages.error(request, 'Invalid credentials')
                return render(request, 'Login.html')
        else:
            messages.error(request, 'Please provide both username and password')
            return render(request, 'Login.html')
    return render(request, 'Login.html')

def Register(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        
        # Validate required fields
        if not all([username, email, password1, password2]):
            messages.error(request, 'Please fill in all fields')
            return render(request, 'Register.html')
        
        # Check password match
        if password1 != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'Register.html')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'Register.html')
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'Register.html')
        
        try:
            # Create new user
            user = User.objects.create_user(username=username, email=email, password=password1)
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')  # Redirect to dashboard instead of home
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
            return render(request, 'Register.html')
    
    return render(request, 'Register.html')

@login_required
def Dashboard(request):
    """
    User dashboard showing overview of lost/found items and notifications
    """
    user = request.user
    
    # Get user's lost items with status breakdown
    lost_items = LostProduct.objects.filter(user=user)
    lost_items_count = lost_items.count()
    active_lost_items = lost_items.filter(status='lost')
    active_lost_count = active_lost_items.count()
    found_items_count_from_lost = lost_items.filter(status='found').count()
    claimed_items_count = lost_items.filter(status='claimed').count()
    
    # Get user's found items  
    found_items = FoundProduct.objects.filter(user=user)
    found_items_count = found_items.count()
    
    # Get user's notifications
    notifications = Notification.objects.filter(user=user).order_by('-created_at')
    notifications_count = notifications.count()
    unread_notifications = notifications.filter(is_sent=False).count()
    
    # Get recent activity (last 5 items) - prioritize active lost items
    recent_lost_items = active_lost_items.order_by('-created_at')[:3]
    recent_found_items = found_items.order_by('-created_at')[:3]
    recent_notifications = notifications[:5]
    
    context = {
        'user': user,
        'lost_items_count': lost_items_count,
        'active_lost_count': active_lost_count,
        'found_items_count_from_lost': found_items_count_from_lost,
        'claimed_items_count': claimed_items_count,
        'found_items_count': found_items_count,
        'notifications_count': notifications_count,
        'unread_notifications': unread_notifications,
        'recent_lost_items': recent_lost_items,
        'recent_found_items': recent_found_items,
        'recent_notifications': recent_notifications,
    }
    
    return render(request, 'Dashboard.html', context)

def UserProfile(request):
    if request.user.is_authenticated:
        return render(request, 'Profile.html')
    return redirect('Login')

def About(request):
    return render(request, 'About.html')

def Contact(request):
    return render(request, 'Contact.html')

def Logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def UserSettings(request):
    """
    User settings page for managing account preferences
    """
    if request.method == 'POST':
        # Handle settings updates
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        if email:
            # Check if email is already taken by another user
            if User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
                messages.error(request, 'This email is already in use by another account.')
            else:
                request.user.email = email
                request.user.first_name = first_name or ''
                request.user.last_name = last_name or ''
                request.user.save()
                messages.success(request, 'Your settings have been updated successfully.')
        
        return redirect('user_settings')
    
    return render(request, 'User_settings.html', {'user': request.user})

@login_required  
def UserLocationSettings(request):
    """
    User location preferences and settings
    """
    if request.method == 'POST':
        # Handle location preferences updates
        default_location = request.POST.get('default_location')
        location_notifications = request.POST.get('location_notifications') == 'on'
        
        # For now, we'll store this in session or user profile
        # In a full implementation, you might want to create a UserLocationPreferences model
        request.session['default_location'] = default_location
        request.session['location_notifications'] = location_notifications
        
        messages.success(request, 'Your location settings have been updated successfully.')
        return redirect('user_location_settings')
    
    # Get current settings from session (or default values)
    current_settings = {
        'default_location': request.session.get('default_location', ''),
        'location_notifications': request.session.get('location_notifications', True),
    }
    
    # Get available locations for the dropdown
    from Location.models import Location
    locations = Location.objects.all()
    
    context = {
        'user': request.user,
        'current_settings': current_settings,
        'locations': locations,
    }
    
    return render(request, 'User_location_settings.html', context)

def ForgotPassword(request):
    """
    Handle forgot password - send OTP to email
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'Forgot_password.html')
        
        # Check if user exists with this email
        if not User.objects.filter(email=email).exists():
            messages.error(request, 'No account found with this email address.')
            return render(request, 'Forgot_password.html')
        
        # Delete any existing unused OTPs for this email
        PasswordResetOTP.objects.filter(email=email, is_used=False).delete()
        
        # Create new OTP
        otp = PasswordResetOTP.objects.create(
            email=email,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Send OTP email
        try:
            subject = 'Password Reset OTP - Retrace'
            message = f"""
Hello,

You have requested to reset your password for your Retrace account.

Your OTP (One-Time Password) is: {otp.otp_code}

This OTP is valid for 10 minutes only.

If you did not request this password reset, please ignore this email.

Best regards,
Retrace Team
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            messages.success(request, f'OTP has been sent to {email}. Please check your email.')
            # Store email in session for OTP verification
            request.session['reset_email'] = email
            return redirect('verify_otp')
            
        except Exception as e:
            messages.error(request, 'Failed to send OTP. Please try again.')
            print(f"Email sending error: {e}")
            return render(request, 'Forgot_password.html')
    
    return render(request, 'Forgot_password.html')

def VerifyOTP(request):
    """
    Verify OTP and allow password reset
    """
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, 'Session expired. Please start the password reset process again.')
        return redirect('forgot_password')
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '').strip()
        
        if not otp_code:
            messages.error(request, 'Please enter the OTP.')
            return render(request, 'Verify_otp.html', {'email': email})
        
        # Find valid OTP
        try:
            otp = PasswordResetOTP.objects.get(
                email=email,
                otp_code=otp_code,
                is_used=False
            )
            
            if otp.is_expired():
                messages.error(request, 'OTP has expired. Please request a new one.')
                return redirect('forgot_password')
            
            # Mark OTP as used
            otp.is_used = True
            otp.save()
            
            # Store verification in session
            request.session['otp_verified'] = True
            request.session['verified_email'] = email
            
            messages.success(request, 'OTP verified successfully. You can now reset your password.')
            return redirect('reset_password')
            
        except PasswordResetOTP.DoesNotExist:
            messages.error(request, 'Invalid OTP. Please check and try again.')
            return render(request, 'Verify_otp.html', {'email': email})
    
    return render(request, 'Verify_otp.html', {'email': email})

def ResendOTP(request):
    """
    Resend OTP to email
    """
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, 'Session expired. Please start the password reset process again.')
        return redirect('forgot_password')
    
    # Delete any existing unused OTPs
    PasswordResetOTP.objects.filter(email=email, is_used=False).delete()
    
    # Create new OTP
    otp = PasswordResetOTP.objects.create(
        email=email,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Send OTP email
    try:
        subject = 'Password Reset OTP - Retrace (Resent)'
        message = f"""
Hello,

You have requested to resend the password reset OTP for your Retrace account.

Your new OTP (One-Time Password) is: {otp.otp_code}

This OTP is valid for 10 minutes only.

If you did not request this password reset, please ignore this email.

Best regards,
Retrace Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        
        messages.success(request, f'New OTP has been sent to {email}.')
        
    except Exception as e:
        messages.error(request, 'Failed to resend OTP. Please try again.')
        print(f"Email sending error: {e}")
    
    return redirect('verify_otp')

def ResetPassword(request):
    """
    Reset password after OTP verification
    """
    if not request.session.get('otp_verified') or not request.session.get('verified_email'):
        messages.error(request, 'Unauthorized access. Please complete the OTP verification first.')
        return redirect('forgot_password')
    
    email = request.session.get('verified_email')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if not new_password or not confirm_password:
            messages.error(request, 'Please fill in both password fields.')
            return render(request, 'Reset_password.html', {'email': email})
        
        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'Reset_password.html', {'email': email})
        
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'Reset_password.html', {'email': email})
        
        # Update user password
        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            
            # Clear session data
            if 'reset_email' in request.session:
                del request.session['reset_email']
            if 'otp_verified' in request.session:
                del request.session['otp_verified']
            if 'verified_email' in request.session:
                del request.session['verified_email']
            
            messages.success(request, 'Password reset successful! You can now log in with your new password.')
            return redirect('login')
            
        except User.DoesNotExist:
            messages.error(request, 'User not found. Please try again.')
            return redirect('forgot_password')
        except Exception as e:
            messages.error(request, 'Failed to reset password. Please try again.')
            print(f"Password reset error: {e}")
            return render(request, 'Reset_password.html', {'email': email})
    
    return render(request, 'Reset_password.html', {'email': email})
