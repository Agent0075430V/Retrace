"""
Test script to debug Report Found Item functionality
"""
import requests

def test_found_item_page():
    """Test if the found item page loads correctly"""
    
    try:
        # Test GET request to found item page
        response = requests.get('http://127.0.0.1:8000/ai/report-found/')
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Page loads successfully!")
            print(f"Content Length: {len(response.text)} characters")
            
            # Check if key elements are present
            if 'Report Found Product' in response.text:
                print("✅ Page title found")
            else:
                print("❌ Page title not found")
                
            if 'form method="POST"' in response.text:
                print("✅ Form found")
            else:
                print("❌ Form not found")
                
        else:
            print(f"❌ Error loading page: {response.status_code}")
            print(f"Error content: {response.text[:500]}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Django server. Make sure it's running on http://127.0.0.1:8000/")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    test_found_item_page()