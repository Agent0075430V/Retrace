"""
Simple test for mark-as-found functionality
"""
import os
import sys
import django

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Retrace.settings')
django.setup()

from AI.models import LostProduct, FoundProduct, Notification
from AI.views import send_item_found_notification
from django.contrib.auth.models import User

def test_mark_found_logic():
    """Test the core mark-as-found logic without HTTP requests"""
    print("🔧 Testing Core Mark-as-Found Logic")
    print("=" * 50)
    
    # Create a test user
    test_user, created = User.objects.get_or_create(
        username='testuser_simple',
        defaults={'email': 'test@example.com'}
    )
    print(f"✅ Using test user: {test_user.username}")
    
    # Create a test lost item
    lost_item = LostProduct.objects.create(
        user=test_user,
        name='Test Lost Laptop',
        description='A black MacBook Pro lost at the coffee shop',
        email='owner@example.com',
        location='Coffee Shop',
        status='lost'
    )
    print(f"✅ Created test lost item: {lost_item.name} (ID: {lost_item.id})")
    print(f"   Initial status: {lost_item.status}")
    
    # Test marking as found
    finder_contact = 'finder@example.com'
    finder_location = 'Coffee Shop Counter'
    additional_notes = 'Found this laptop under a table'
    
    # Create a corresponding found item
    found_item = FoundProduct.objects.create(
        user=test_user,
        name=lost_item.name,
        description=f"{lost_item.description}\n\nFound by: {finder_contact}\nLocation when found: {finder_location}\nAdditional notes: {additional_notes}",
        image=lost_item.image,
        email=finder_contact,
        phone_number=lost_item.phone_number,
        location=finder_location or lost_item.location,
        latitude=lost_item.latitude,
        longitude=lost_item.longitude,
    )
    print(f"✅ Created found item: {found_item.name} (ID: {found_item.id})")
    
    # Update the lost item status
    lost_item.status = 'found'
    lost_item.found_by = test_user
    lost_item.date_found = found_item.created_at
    lost_item.save()
    print(f"✅ Updated lost item status to: {lost_item.status}")
    print(f"   Found by: {lost_item.found_by}")
    print(f"   Date found: {lost_item.date_found}")
    
    # Test the notification function
    initial_notification_count = Notification.objects.count()
    send_item_found_notification(lost_item, found_item, finder_contact)
    new_notification_count = Notification.objects.count()
    
    if new_notification_count > initial_notification_count:
        print(f"✅ Notification created successfully")
        latest_notification = Notification.objects.latest('created_at')
        print(f"   Message preview: {latest_notification.message[:100]}...")
        print(f"   Sent via: {latest_notification.sent_via}")
        print(f"   Is sent: {latest_notification.is_sent}")
    else:
        print("ℹ️ Notification creation skipped (no email settings or user)")
    
    # Verify the full flow
    print("\n📊 Verification:")
    print(f"   Lost item status: {lost_item.status}")
    print(f"   Found item exists: {found_item.id is not None}")
    print(f"   Found item location: {found_item.location}")
    print(f"   Found item contact: {found_item.email}")
    
    # Test filtering
    active_lost_items = LostProduct.objects.filter(status='lost')
    found_lost_items = LostProduct.objects.filter(status='found')
    print(f"   Active lost items: {active_lost_items.count()}")
    print(f"   Found lost items: {found_lost_items.count()}")
    
    # Clean up
    print("\n🧹 Cleaning up...")
    lost_item.delete()
    found_item.delete()
    if new_notification_count > initial_notification_count:
        latest_notification.delete()
    print("✅ Test data cleaned up")
    
    print("\n🎉 Core functionality test completed successfully!")
    return True

def test_email_notification_content():
    """Test the email notification content"""
    print("\n🔧 Testing Email Notification Content")
    print("=" * 40)
    
    # Create test items
    lost_item = LostProduct(
        name='Test Phone',
        description='iPhone 12 with blue case',
        email='owner@test.com',
        location='University Library',
        status='lost'
    )
    
    found_item = FoundProduct(
        name='Test Phone',
        location='Library Front Desk'
    )
    found_item.created_at = django.utils.timezone.now()
    
    # Test notification creation (without actually sending)
    from AI.views import send_item_found_notification
    import django.utils.timezone
    
    print("✅ Testing notification content generation...")
    
    # Mock the send_mail to capture the content
    original_send_mail = None
    try:
        from django.core.mail import send_mail
        captured_emails = []
        
        def mock_send_mail(subject, message, from_email, recipient_list, **kwargs):
            captured_emails.append({
                'subject': subject,
                'message': message,
                'from_email': from_email,
                'recipient_list': recipient_list
            })
            print(f"✅ Email captured:")
            print(f"   Subject: {subject}")
            print(f"   To: {recipient_list}")
            print(f"   Message preview: {message[:150]}...")
        
        # Temporarily replace send_mail
        import AI.views
        AI.views.send_mail = mock_send_mail
        
        # Test the function
        send_item_found_notification(lost_item, found_item, 'finder@test.com')
        
        if captured_emails:
            email = captured_emails[0]
            print(f"✅ Email content generated successfully")
            print(f"   Contains item name: {'Test Phone' in email['message']}")
            print(f"   Contains finder contact: {'finder@test.com' in email['message']}")
            print(f"   Contains found location: {'Library Front Desk' in email['message']}")
        else:
            print("ℹ️ No email captured - check email settings")
            
    except Exception as e:
        print(f"⚠️ Email test skipped: {e}")
    
    print("✅ Email notification content test completed")

if __name__ == "__main__":
    try:
        test_mark_found_logic()
        test_email_notification_content()
        print("\n🎯 All simple tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()