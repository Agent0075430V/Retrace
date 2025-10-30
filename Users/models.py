from django.db import models
from django.contrib.auth.models import User as Users
from django.utils import timezone
import random
import string

# Create your models here.
class User(models.Model):
    LIVE=1
    INACTIVE=0
    STATUS_CHOICES = [
        (LIVE, 'Live'),
        (INACTIVE, 'Inactive'),
    ]
    username = models.OneToOneField(Users, on_delete=models.CASCADE, related_name='user_profile')
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=100)
    password = models.CharField(max_length=128)
    phone_number = models.CharField(max_length=10)
    deleted_status = models.IntegerField(choices=STATUS_CHOICES, default=LIVE)
    role = models.CharField(choices=[('User', 'User'), ('Admin', 'Admin')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username
    class Meta:
        ordering = ['-created_at']  
        verbose_name = 'User'
        verbose_name_plural = 'Users'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
    
    class Meta:
        ordering = ['-created_at']  
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

class UserActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"Activity by {self.user.username} at {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']  
        verbose_name = 'User Activity Log'
        verbose_name_plural = 'User Activity Logs'


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    receive_newsletters = models.BooleanField(default=True)
    dark_mode = models.BooleanField(default=False)
    notification_preferences = models.JSONField(default=dict)  # e.g., {"email": True, "sms": False}
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings for {self.user.username}"
    
    class Meta:
        ordering = ['-created_at']  
        verbose_name = 'User Setting'
        verbose_name_plural = 'User Settings'


class PasswordResetOTP(models.Model):
    """
    Model to store OTP for password reset functionality
    """
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.otp_code:
            self.otp_code = self.generate_otp()
        if not self.expires_at:
            # OTP expires in 10 minutes
            self.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_otp():
        """Generate a 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))
    
    def is_expired(self):
        """Check if OTP has expired"""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if OTP is valid (not used and not expired)"""
        return not self.is_used and not self.is_expired()
    
    def __str__(self):
        return f"OTP for {self.email} - {self.otp_code}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Password Reset OTP'
        verbose_name_plural = 'Password Reset OTPs'
