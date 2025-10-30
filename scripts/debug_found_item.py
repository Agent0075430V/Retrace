"""
Manual test for Report Found Item functionality
"""
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Retrace.settings')
django.setup()

from AI.models import FoundProduct, LostProduct, MatchResult
from django.contrib.auth.models import User

def test_found_item_creation():
    """Test creating a found item manually"""
    
    print("🔧 Testing Found Item Creation")
    print("=" * 50)
    
    # Test data
    test_data = {
        'name': 'Test Found Item',
        'description': 'This is a test found item for debugging',
        'location': 'Test Location',
        'email': 'test@example.com',
        'phone_number': '1234567890',
    }
    
    try:
        # Create found item
        found_item = FoundProduct.objects.create(**test_data)
        print(f"✅ Successfully created found item: {found_item.name}")
        print(f"   ID: {found_item.id}")
        print(f"   Location: {found_item.location}")
        print(f"   Email: {found_item.email}")
        print(f"   Created at: {found_item.created_at}")
        
        # Test retrieving the item
        retrieved_item = FoundProduct.objects.get(id=found_item.id)
        print(f"✅ Successfully retrieved item: {retrieved_item.name}")
        
        # Clean up
        found_item.delete()
        print("✅ Test item cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating found item: {str(e)}")
        return False

def test_view_import():
    """Test if the view function can be imported and called"""
    
    print("\n🔧 Testing View Function")
    print("=" * 50)
    
    try:
        from AI.views import report_found_product
        print("✅ Successfully imported report_found_product view")
        
        # Test if the function exists and is callable
        if callable(report_found_product):
            print("✅ View function is callable")
        else:
            print("❌ View function is not callable")
            
        return True
        
    except ImportError as e:
        print(f"❌ Error importing view: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_template_exists():
    """Test if the template file exists"""
    
    print("\n🔧 Testing Template File")
    print("=" * 50)
    
    import os
    from django.conf import settings
    
    template_path = os.path.join(settings.BASE_DIR, 'Templates', 'Found_product.html')
    
    if os.path.exists(template_path):
        print(f"✅ Template exists: {template_path}")
        
        # Check file size
        file_size = os.path.getsize(template_path)
        print(f"   File size: {file_size} bytes")
        
        if file_size > 0:
            print("✅ Template file is not empty")
        else:
            print("❌ Template file is empty")
            
        return True
    else:
        print(f"❌ Template not found: {template_path}")
        return False

def run_all_tests():
    """Run all tests"""
    
    print("🧪 REPORT FOUND ITEM - DEBUG TESTS")
    print("=" * 70)
    
    results = []
    
    # Test 1: Model creation
    results.append(test_found_item_creation())
    
    # Test 2: View import
    results.append(test_view_import())
    
    # Test 3: Template exists
    results.append(test_template_exists())
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The Report Found Item functionality should work.")
    else:
        print("⚠️ Some tests failed. Check the issues above.")
        
    print("\n💡 Next steps:")
    print("1. Make sure Django server is running: python manage.py runserver")
    print("2. Test the URL: http://127.0.0.1:8000/ai/report-found/")
    print("3. Check browser developer tools for any JavaScript errors")

if __name__ == "__main__":
    run_all_tests()