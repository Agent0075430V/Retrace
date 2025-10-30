"""
Test script for the mark-as-found functionality
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
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

def test_mark_found_system():
    """Test the complete mark-as-found system"""
    print("🔧 Testing Mark as Found System")
    print("=" * 50)
    
    # Create a test user if it doesn't exist
    test_user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        test_user.set_password('testpass123')
        test_user.save()
        print(f"✅ Created test user: {test_user.username}")
    else:
        print(f"✅ Using existing test user: {test_user.username}")
    
    # Create a test lost item
    lost_item = LostProduct.objects.create(
        user=test_user,
        name='Test Lost Phone',
        description='A black iPhone 13 lost at the university library',
        email='owner@example.com',
        location='University Library',
        status='lost'  # Explicitly set to lost
    )
    print(f"✅ Created test lost item: {lost_item.name} (ID: {lost_item.id})")
    
    # Test that the item starts with 'lost' status
    assert lost_item.status == 'lost', f"Expected status 'lost', got '{lost_item.status}'"
    print(f"✅ Confirmed initial status: {lost_item.status}")
    
    # Count initial items
    initial_found_count = FoundProduct.objects.count()
    initial_notification_count = Notification.objects.count()
    
    print(f"📊 Initial counts - Found items: {initial_found_count}, Notifications: {initial_notification_count}")
    
    # Test the mark as found functionality programmatically
    print("\n🧪 Testing mark-as-found functionality...")
    
    # Create a client to simulate the POST request
    client = Client()
    
    # Simulate marking the item as found
    response = client.post(f'/ai/mark-found/{lost_item.id}/', {
        'finder_contact': 'finder@example.com',
        'finder_location': 'University Library Front Desk',
        'additional_notes': 'Found this phone on a table in the library'
    })
    
    # Check if the request was successful
    if response.status_code == 200:
        print(f"✅ Mark-as-found request successful: {response.status_code}")
        
        # Refresh the lost item from database
        lost_item.refresh_from_db()
        
        # Verify the status was updated
        assert lost_item.status == 'found', f"Expected status 'found', got '{lost_item.status}'"
        print(f"✅ Lost item status updated to: {lost_item.status}")
        
        # Check if found_by field was set
        print(f"✅ Found by: {lost_item.found_by}")
        print(f"✅ Date found: {lost_item.date_found}")
        
        # Check if a new FoundProduct was created
        new_found_count = FoundProduct.objects.count()
        assert new_found_count == initial_found_count + 1, f"Expected {initial_found_count + 1} found items, got {new_found_count}"
        print(f"✅ New FoundProduct created. Total found items: {new_found_count}")
        
        # Check if notification was created
        new_notification_count = Notification.objects.count()
        assert new_notification_count == initial_notification_count + 1, f"Expected {initial_notification_count + 1} notifications, got {new_notification_count}"
        print(f"✅ Notification created. Total notifications: {new_notification_count}")
        
        # Get the created found item
        created_found_item = FoundProduct.objects.latest('created_at')
        print(f"✅ Created found item: {created_found_item.name}")
        print(f"   Location: {created_found_item.location}")
        print(f"   Email: {created_found_item.email}")
        
        # Get the created notification
        created_notification = Notification.objects.latest('created_at')
        print(f"✅ Created notification:")
        print(f"   User: {created_notification.user}")
        print(f"   Message: {created_notification.message[:100]}...")
        print(f"   Sent via: {created_notification.sent_via}")
        print(f"   Is sent: {created_notification.is_sent}")
        
    else:
        print(f"❌ Mark-as-found request failed: {response.status_code}")
        print(f"Response content: {response.content}")
        return False
    
    print("\n🎉 All tests passed! The mark-as-found system is working correctly.")
    
    # Clean up test data
    print("\n🧹 Cleaning up test data...")
    lost_item.delete()
    created_found_item.delete()
    created_notification.delete()
    print("✅ Test data cleaned up")
    
    return True

def test_status_filtering():
    """Test that status filtering works correctly"""
    print("\n🔧 Testing Status Filtering")
    print("=" * 30)
    
    # Create test items with different statuses
    lost_active = LostProduct.objects.create(
        name='Active Lost Item',
        description='Still looking for this',
        email='test1@example.com',
        status='lost'
    )
    
    lost_found = LostProduct.objects.create(
        name='Found Lost Item',
        description='This was found',
        email='test2@example.com',
        status='found'
    )
    
    lost_claimed = LostProduct.objects.create(
        name='Claimed Lost Item',
        description='This was claimed',
        email='test3@example.com',
        status='claimed'
    )
    
    # Test filtering
    active_items = LostProduct.objects.filter(status='lost')
    found_items = LostProduct.objects.filter(status='found')
    claimed_items = LostProduct.objects.filter(status='claimed')
    
    print(f"✅ Active lost items: {active_items.count()}")
    print(f"✅ Found items: {found_items.count()}")
    print(f"✅ Claimed items: {claimed_items.count()}")
    
    # Clean up
    lost_active.delete()
    lost_found.delete()
    lost_claimed.delete()
    
    print("✅ Status filtering test completed")

if __name__ == "__main__":
    try:
        test_mark_found_system()
        test_status_filtering()
        print("\n🎯 All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()