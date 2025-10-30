#!/usr/bin/env python
"""
Script to clear all lost and found items from the database.
This will remove all data from LostProduct, FoundProduct, MatchResult, and Notification tables.
"""

import os
import sys
import django

# Add the project directory to the path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Retrace.settings')
django.setup()

from AI.models import LostProduct, FoundProduct, MatchResult, Notification, RouteMap, PendingClaim

def clear_database():
    """Clear all lost and found items from the database."""
    
    print("🗑️  Clearing Database - Lost and Found Items")
    print("=" * 60)
    
    # Get counts before deletion
    lost_count = LostProduct.objects.count()
    found_count = FoundProduct.objects.count()
    match_count = MatchResult.objects.count()
    notification_count = Notification.objects.count()
    route_count = RouteMap.objects.count()
    pending_claim_count = PendingClaim.objects.count()
    
    print(f"📊 Current Database Statistics:")
    print(f"   Lost Products: {lost_count}")
    print(f"   Found Products: {found_count}")
    print(f"   Match Results: {match_count}")
    print(f"   Notifications: {notification_count}")
    print(f"   Route Maps: {route_count}")
    print(f"   Pending Claims: {pending_claim_count}")
    print()
    
    total_items = lost_count + found_count + match_count + notification_count + route_count + pending_claim_count
    
    if total_items == 0:
        print("✅ Database is already empty - nothing to clear!")
        return
    
    # Confirm deletion
    response = input("⚠️  Are you sure you want to delete ALL items? This cannot be undone! (type 'YES' to confirm): ")
    
    if response != 'YES':
        print("❌ Operation cancelled.")
        return
    
    print("\n🔄 Starting deletion process...")
    
    try:
        # Delete in order to avoid foreign key constraints
        
        # 1. Delete pending claims first (they reference lost products)
        if pending_claim_count > 0:
            deleted_pending = PendingClaim.objects.all().delete()
            print(f"✅ Deleted {deleted_pending[0]} pending claims")
        
        # 2. Delete notifications
        if notification_count > 0:
            deleted_notifications = Notification.objects.all().delete()
            print(f"✅ Deleted {deleted_notifications[0]} notifications")
        
        # 3. Delete route maps
        if route_count > 0:
            deleted_routes = RouteMap.objects.all().delete()
            print(f"✅ Deleted {deleted_routes[0]} route maps")
        
        # 4. Delete match results
        if match_count > 0:
            deleted_matches = MatchResult.objects.all().delete()
            print(f"✅ Deleted {deleted_matches[0]} match results")
        
        # 5. Delete found products
        if found_count > 0:
            deleted_found = FoundProduct.objects.all().delete()
            print(f"✅ Deleted {deleted_found[0]} found products")
        
        # 6. Delete lost products
        if lost_count > 0:
            deleted_lost = LostProduct.objects.all().delete()
            print(f"✅ Deleted {deleted_lost[0]} lost products")
        
        print("\n🎉 Database cleared successfully!")
        
        # Verify deletion
        final_lost_count = LostProduct.objects.count()
        final_found_count = FoundProduct.objects.count()
        final_match_count = MatchResult.objects.count()
        final_notification_count = Notification.objects.count()
        final_route_count = RouteMap.objects.count()
        final_pending_count = PendingClaim.objects.count()
        
        print(f"\n📊 Final Database Statistics:")
        print(f"   Lost Products: {final_lost_count}")
        print(f"   Found Products: {final_found_count}")
        print(f"   Match Results: {final_match_count}")
        print(f"   Notifications: {final_notification_count}")
        print(f"   Route Maps: {final_route_count}")
        print(f"   Pending Claims: {final_pending_count}")
        
        final_total = final_lost_count + final_found_count + final_match_count + final_notification_count + final_route_count + final_pending_count
        
        if final_total == 0:
            print("\n✅ All items successfully cleared from the database!")
        else:
            print("\n⚠️  Warning: Some items may still remain in the database.")
            
    except Exception as e:
        print(f"\n❌ Error during deletion: {str(e)}")
        print("The database may be partially cleared.")
        
def show_current_stats():
    """Show current database statistics without clearing."""
    lost_count = LostProduct.objects.count()
    found_count = FoundProduct.objects.count()
    match_count = MatchResult.objects.count()
    notification_count = Notification.objects.count()
    route_count = RouteMap.objects.count()
    pending_claim_count = PendingClaim.objects.count()
    
    print("📊 Current Database Statistics:")
    print(f"   Lost Products: {lost_count}")
    print(f"   Found Products: {found_count}")
    print(f"   Match Results: {match_count}")
    print(f"   Notifications: {notification_count}")
    print(f"   Route Maps: {route_count}")
    print(f"   Pending Claims: {pending_claim_count}")
    print(f"   Total Items: {lost_count + found_count + match_count + notification_count + route_count + pending_claim_count}")
    
    # Additional statistics
    lost_by_status = {
        'lost': LostProduct.objects.filter(status='lost').count(),
        'found': LostProduct.objects.filter(status='found').count(),
        'claimed': LostProduct.objects.filter(status='claimed').count(),
    }
    
    print(f"\n📋 Lost Items by Status:")
    print(f"   Still Lost: {lost_by_status['lost']}")
    print(f"   Found: {lost_by_status['found']}")
    print(f"   Claimed: {lost_by_status['claimed']}")
    
    pending_by_status = {
        'pending': PendingClaim.objects.filter(status='pending').count(),
        'approved': PendingClaim.objects.filter(status='approved').count(),
        'rejected': PendingClaim.objects.filter(status='rejected').count(),
        'expired': PendingClaim.objects.filter(status='expired').count(),
    }
    
    print(f"\n⏳ Pending Claims by Status:")
    print(f"   Pending: {pending_by_status['pending']}")
    print(f"   Approved: {pending_by_status['approved']}")
    print(f"   Rejected: {pending_by_status['rejected']}")
    print(f"   Expired: {pending_by_status['expired']}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clear lost and found items from database")
    parser.add_argument('--stats-only', action='store_true', help='Show statistics only without clearing')
    parser.add_argument('--force', action='store_true', help='Clear without confirmation (dangerous!)')
    
    args = parser.parse_args()
    
    if args.stats_only:
        show_current_stats()
    else:
        if args.force:
            # Override the confirmation for automated scripts
            original_input = input
            input = lambda x: 'YES'
        
        clear_database()
        
        if args.force:
            input = original_input