#!/usr/bin/env python
"""
Script to create test lost items for testing the mark as found feature.
"""

import os
import sys
import django
from datetime import date, timedelta

# Add the project directory to the path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Retrace.settings')
django.setup()

from AI.models import LostProduct
from django.contrib.auth.models import User

def create_test_items():
    """Create test lost items for testing mark as found feature."""
    
    print("🧪 Creating Test Lost Items")
    print("=" * 40)
    
    # Get or create a test user
    test_user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    if created:
        test_user.set_password('testpass123')
        test_user.save()
        print(f"✅ Created test user: {test_user.username}")
    else:
        print(f"ℹ️  Using existing test user: {test_user.username}")
    
    # Test items data
    test_items = [
        {
            'name': 'iPhone 14 Pro',
            'description': 'Space Black iPhone 14 Pro with a clear case. Has a small scratch on the back.',
            'email': 'john.doe@email.com',
            'phone_number': '+1234567890',
            'location': 'Central Library',
            'date_lost': date.today() - timedelta(days=2),
        },
        {
            'name': 'Red Backpack',
            'description': 'Large red Nike backpack with laptop compartment. Contains some textbooks and a water bottle.',
            'email': 'sarah.smith@email.com',
            'phone_number': '+9876543210',
            'location': 'Student Center',
            'date_lost': date.today() - timedelta(days=1),
        },
        {
            'name': 'Car Keys',
            'description': 'Toyota car keys with a blue keychain that says "Best Dad Ever".',
            'email': 'mike.johnson@email.com',
            'phone_number': '+5555551234',
            'location': 'Parking Lot A',
            'date_lost': date.today(),
        },
        {
            'name': 'Silver Watch',
            'description': 'Stainless steel Casio watch with digital display. Has a few scratches on the band.',
            'email': 'emma.wilson@email.com',
            'phone_number': '+1111112222',
            'location': 'Gym',
            'date_lost': date.today() - timedelta(days=3),
        },
        {
            'name': 'Blue Wallet',
            'description': 'Navy blue leather wallet with multiple card slots. Contains driver license and some cash.',
            'email': 'david.brown@email.com',
            'phone_number': '+3333334444',
            'location': 'Cafeteria',
            'date_lost': date.today() - timedelta(days=1),
        }
    ]
    
    created_count = 0
    
    for item_data in test_items:
        # Check if similar item already exists
        existing = LostProduct.objects.filter(
            name=item_data['name'],
            email=item_data['email']
        ).first()
        
        if not existing:
            lost_item = LostProduct.objects.create(
                user=test_user,
                status='lost',
                **item_data
            )
            print(f"✅ Created: {lost_item.name} - #{lost_item.id}")
            created_count += 1
        else:
            print(f"ℹ️  Skipped: {item_data['name']} - already exists")
    
    print(f"\n📊 Summary:")
    print(f"   Created: {created_count} new test items")
    print(f"   Total lost items in database: {LostProduct.objects.filter(status='lost').count()}")
    
    print(f"\n🌐 You can now test the mark as found feature at:")
    print(f"   • http://localhost:8000/ai/all-lost-items/")
    print(f"   • http://localhost:8000/ai/search/")

if __name__ == "__main__":
    create_test_items()