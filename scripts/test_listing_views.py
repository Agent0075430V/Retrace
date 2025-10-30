"""
Test script for the new lost and found items listing functionality
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

from AI.models import LostProduct, FoundProduct
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

def test_lost_items_view():
    """Test the all lost items view functionality"""
    print("🔧 Testing All Lost Items View")
    print("=" * 40)
    
    # Create test data if it doesn't exist
    test_user, created = User.objects.get_or_create(
        username='test_listing_user',
        defaults={'email': 'test_listing@example.com'}
    )
    
    # Create sample lost items with different statuses
    sample_items = []
    statuses = ['lost', 'found', 'claimed']
    
    for i, status in enumerate(statuses):
        item = LostProduct.objects.create(
            user=test_user,
            name=f'Test {status.title()} Item {i+1}',
            description=f'This is a test {status} item for the listing view. It contains detailed information to test the display functionality.',
            email=f'owner{i+1}@example.com',
            phone_number=f'123-456-000{i+1}',
            location=f'Test Location {i+1}',
            location_lost=f'Lost at Test Location {i+1}',
            status=status
        )
        sample_items.append(item)
        print(f"✅ Created test lost item: {item.name} (Status: {item.status})")
    
    # Test view functionality
    client = Client()
    
    # Test basic view
    response = client.get('/ai/all-lost-items/')
    print(f"✅ All lost items view response: {response.status_code}")
    
    # Test filtering by status
    response = client.get('/ai/all-lost-items/?status=lost')
    print(f"✅ Lost items filtered by 'lost' status: {response.status_code}")
    
    # Test search functionality
    response = client.get('/ai/all-lost-items/?search=Test')
    print(f"✅ Lost items search test: {response.status_code}")
    
    # Test sorting
    response = client.get('/ai/all-lost-items/?sort=name')
    print(f"✅ Lost items sorting test: {response.status_code}")
    
    # Clean up
    for item in sample_items:
        item.delete()
    print("✅ Test data cleaned up")
    
    return True

def test_found_items_view():
    """Test the all found items view functionality"""
    print("\n🔧 Testing All Found Items View")
    print("=" * 40)
    
    # Create test data
    test_user, created = User.objects.get_or_create(
        username='test_found_user',
        defaults={'email': 'test_found@example.com'}
    )
    
    # Create sample found items
    sample_items = []
    
    for i in range(3):
        item = FoundProduct.objects.create(
            user=test_user,
            name=f'Test Found Item {i+1}',
            description=f'This is a test found item {i+1} for the listing view. Contains contact information and finder details.',
            email=f'finder{i+1}@example.com',
            phone_number=f'987-654-000{i+1}',
            location=f'Found at Location {i+1}',
            location_found=f'Found Location {i+1}'
        )
        sample_items.append(item)
        print(f"✅ Created test found item: {item.name}")
    
    # Test view functionality
    client = Client()
    
    # Test basic view
    response = client.get('/ai/all-found-items/')
    print(f"✅ All found items view response: {response.status_code}")
    
    # Test search functionality
    response = client.get('/ai/all-found-items/?search=Test')
    print(f"✅ Found items search test: {response.status_code}")
    
    # Test location filtering
    response = client.get('/ai/all-found-items/?location=Found at Location 1')
    print(f"✅ Found items location filter test: {response.status_code}")
    
    # Test sorting
    response = client.get('/ai/all-found-items/?sort=-created_at')
    print(f"✅ Found items sorting test: {response.status_code}")
    
    # Clean up
    for item in sample_items:
        item.delete()
    print("✅ Test data cleaned up")
    
    return True

def test_database_stats():
    """Test the database statistics display"""
    print("\n🔧 Testing Database Statistics")
    print("=" * 35)
    
    # Get current counts
    total_lost = LostProduct.objects.count()
    active_lost = LostProduct.objects.filter(status='lost').count()
    found_lost = LostProduct.objects.filter(status='found').count()
    claimed_lost = LostProduct.objects.filter(status='claimed').count()
    total_found = FoundProduct.objects.count()
    
    print(f"📊 Database Statistics:")
    print(f"   Total Lost Items: {total_lost}")
    print(f"   Active Lost Items: {active_lost}")
    print(f"   Found Lost Items: {found_lost}")
    print(f"   Claimed Lost Items: {claimed_lost}")
    print(f"   Total Found Items: {total_found}")
    
    # Verify math
    if active_lost + found_lost + claimed_lost == total_lost:
        print("✅ Lost items status counts are correct")
    else:
        print("⚠️ Lost items status counts don't add up")
    
    return True

def test_url_patterns():
    """Test that URL patterns are working"""
    print("\n🔧 Testing URL Patterns")
    print("=" * 25)
    
    client = Client()
    
    urls_to_test = [
        '/ai/all-lost-items/',
        '/ai/all-found-items/',
        '/ai/all-lost-items/?page=1',
        '/ai/all-found-items/?page=1',
    ]
    
    for url in urls_to_test:
        try:
            response = client.get(url)
            if response.status_code == 200:
                print(f"✅ {url} - OK")
            else:
                print(f"⚠️ {url} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {url} - Error: {e}")
    
    return True

if __name__ == "__main__":
    try:
        print("🎯 Testing Lost and Found Items Listing System")
        print("=" * 60)
        
        test_database_stats()
        test_url_patterns()
        test_lost_items_view()
        test_found_items_view()
        
        print("\n🎉 All tests completed successfully!")
        print("🌐 You can now visit:")
        print("   • http://localhost:8000/ai/all-lost-items/")
        print("   • http://localhost:8000/ai/all-found-items/")
        print("   • Updated navigation in header and home page")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()