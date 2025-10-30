"""
Test email configuration for Retrace application
"""
import os
import django
from django.conf import settings

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Retrace.settings')
django.setup()

from django.core.mail import send_mail

def test_email_configuration():
    """Test if email configuration is working"""
    
    print("🔧 Testing Email Configuration")
    print("=" * 50)
    
    # Check environment variables
    use_real_email = os.getenv('USE_REAL_EMAIL', 'False').lower() == 'true'
    email_user = os.getenv('EMAIL_HOST_USER', 'Not set')
    email_password = os.getenv('EMAIL_HOST_PASSWORD', 'Not set')
    
    print(f"USE_REAL_EMAIL: {use_real_email}")
    print(f"EMAIL_HOST_USER: {email_user}")
    print(f"EMAIL_HOST_PASSWORD: {'*' * len(email_password) if email_password != 'Not set' else 'Not set'}")
    print()
    
    # Check Django settings
    print("📧 Django Email Settings:")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    if hasattr(settings, 'EMAIL_HOST'):
        print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
        print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print()
    
    if use_real_email:
        print("✅ Real email sending is ENABLED")
        print("📤 Testing email sending...")
        
        try:
            # Test email sending
            send_mail(
                'Test Email from Retrace',
                'This is a test email to verify email configuration.',
                settings.DEFAULT_FROM_EMAIL,
                [email_user],
                fail_silently=False,
            )
            print("✅ Test email sent successfully!")
            print(f"📧 Check your inbox: {email_user}")
            
        except Exception as e:
            print(f"❌ Email sending failed: {str(e)}")
            print()
            print("🔧 Possible issues:")
            print("1. Check your Gmail App Password")
            print("2. Ensure 2-Factor Authentication is enabled")
            print("3. Verify the email address is correct")
            
    else:
        print("📺 Console email backend is active")
        print("📧 Emails will appear in terminal console")

if __name__ == "__main__":
    test_email_configuration()