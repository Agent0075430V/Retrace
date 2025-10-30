#!/usr/bin/env python
"""
Advanced Database Management Script for Retrace Lost & Found System
Provides selective clearing options and maintenance utilities.
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Add the project directory to the path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Retrace.settings')
django.setup()

from AI.models import LostProduct, FoundProduct, MatchResult, Notification, RouteMap, PendingClaim
from django.utils import timezone

class DatabaseManager:
    def __init__(self):
        self.dry_run = False
    
    def set_dry_run(self, dry_run=True):
        """Enable/disable dry run mode for testing."""
        self.dry_run = dry_run
        if dry_run:
            print("🔍 DRY RUN MODE: No actual changes will be made")
    
    def clear_all(self, force=False):
        """Clear all lost and found items from the database."""
        print("🗑️  CLEARING ALL DATABASE ITEMS")
        print("=" * 50)
        
        if not force:
            response = input("⚠️  Delete ALL items? Type 'DELETE ALL' to confirm: ")
            if response != 'DELETE ALL':
                print("❌ Operation cancelled.")
                return
        
        if not self.dry_run:
            try:
                # Delete in dependency order
                PendingClaim.objects.all().delete()
                print("✅ Cleared pending claims")
                
                Notification.objects.all().delete()
                print("✅ Cleared notifications")
                
                RouteMap.objects.all().delete()
                print("✅ Cleared route maps")
                
                MatchResult.objects.all().delete()
                print("✅ Cleared match results")
                
                FoundProduct.objects.all().delete()
                print("✅ Cleared found products")
                
                LostProduct.objects.all().delete()
                print("✅ Cleared lost products")
                
                print("\n🎉 All items cleared successfully!")
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print("🔍 DRY RUN: Would clear all items")
    
    def clear_old_items(self, days=30, force=False):
        """Clear items older than specified days."""
        cutoff_date = timezone.now() - timedelta(days=days)
        
        old_lost = LostProduct.objects.filter(created_at__lt=cutoff_date)
        old_found = FoundProduct.objects.filter(created_at__lt=cutoff_date)
        
        print(f"🗓️  CLEARING ITEMS OLDER THAN {days} DAYS")
        print("=" * 50)
        print(f"Found {old_lost.count()} old lost items")
        print(f"Found {old_found.count()} old found items")
        
        if old_lost.count() == 0 and old_found.count() == 0:
            print("✅ No old items to clear!")
            return
        
        if not force:
            response = input(f"Delete items older than {days} days? (y/N): ")
            if response.lower() != 'y':
                print("❌ Operation cancelled.")
                return
        
        if not self.dry_run:
            # Clear related objects first
            old_lost_ids = list(old_lost.values_list('id', flat=True))
            old_found_ids = list(old_found.values_list('id', flat=True))
            
            PendingClaim.objects.filter(lost_item_id__in=old_lost_ids).delete()
            RouteMap.objects.filter(lost_product_id__in=old_lost_ids).delete()
            RouteMap.objects.filter(found_product_id__in=old_found_ids).delete()
            MatchResult.objects.filter(lost_product_id__in=old_lost_ids).delete()
            MatchResult.objects.filter(found_product_id__in=old_found_ids).delete()
            
            old_lost.delete()
            old_found.delete()
            
            print(f"✅ Cleared items older than {days} days")
        else:
            print(f"🔍 DRY RUN: Would clear {old_lost.count() + old_found.count()} old items")
    
    def clear_by_status(self, status, force=False):
        """Clear items by specific status."""
        items = LostProduct.objects.filter(status=status)
        
        print(f"🎯 CLEARING ITEMS WITH STATUS: {status.upper()}")
        print("=" * 50)
        print(f"Found {items.count()} items with status '{status}'")
        
        if items.count() == 0:
            print(f"✅ No items with status '{status}' found!")
            return
        
        if not force:
            response = input(f"Delete all '{status}' items? (y/N): ")
            if response.lower() != 'y':
                print("❌ Operation cancelled.")
                return
        
        if not self.dry_run:
            item_ids = list(items.values_list('id', flat=True))
            
            # Clear related objects
            PendingClaim.objects.filter(lost_item_id__in=item_ids).delete()
            RouteMap.objects.filter(lost_product_id__in=item_ids).delete()
            MatchResult.objects.filter(lost_product_id__in=item_ids).delete()
            
            items.delete()
            print(f"✅ Cleared all '{status}' items")
        else:
            print(f"🔍 DRY RUN: Would clear {items.count()} '{status}' items")
    
    def clear_expired_claims(self, force=False):
        """Clear expired pending claims."""
        expired_claims = PendingClaim.objects.filter(expires_at__lt=timezone.now())
        
        print("⏰ CLEARING EXPIRED PENDING CLAIMS")
        print("=" * 50)
        print(f"Found {expired_claims.count()} expired claims")
        
        if expired_claims.count() == 0:
            print("✅ No expired claims found!")
            return
        
        if not force:
            response = input("Delete expired claims? (y/N): ")
            if response.lower() != 'y':
                print("❌ Operation cancelled.")
                return
        
        if not self.dry_run:
            expired_claims.delete()
            print("✅ Cleared expired claims")
        else:
            print(f"🔍 DRY RUN: Would clear {expired_claims.count()} expired claims")
    
    def cleanup_orphaned_data(self, force=False):
        """Clean up orphaned data (notifications, routes, etc. without parent items)."""
        print("🧹 CLEANING UP ORPHANED DATA")
        print("=" * 50)
        
        orphaned_notifications = Notification.objects.filter(user__isnull=True)
        orphaned_routes = RouteMap.objects.filter(lost_product__isnull=True, found_product__isnull=True)
        
        print(f"Found {orphaned_notifications.count()} orphaned notifications")
        print(f"Found {orphaned_routes.count()} orphaned route maps")
        
        total_orphaned = orphaned_notifications.count() + orphaned_routes.count()
        
        if total_orphaned == 0:
            print("✅ No orphaned data found!")
            return
        
        if not force:
            response = input("Delete orphaned data? (y/N): ")
            if response.lower() != 'y':
                print("❌ Operation cancelled.")
                return
        
        if not self.dry_run:
            orphaned_notifications.delete()
            orphaned_routes.delete()
            print("✅ Cleaned up orphaned data")
        else:
            print(f"🔍 DRY RUN: Would clean up {total_orphaned} orphaned records")
    
    def show_detailed_stats(self):
        """Show comprehensive database statistics."""
        print("📊 DETAILED DATABASE STATISTICS")
        print("=" * 50)
        
        # Basic counts
        lost_count = LostProduct.objects.count()
        found_count = FoundProduct.objects.count()
        match_count = MatchResult.objects.count()
        notification_count = Notification.objects.count()
        route_count = RouteMap.objects.count()
        pending_count = PendingClaim.objects.count()
        
        print(f"📦 Total Items:")
        print(f"   Lost Products: {lost_count}")
        print(f"   Found Products: {found_count}")
        print(f"   Match Results: {match_count}")
        print(f"   Notifications: {notification_count}")
        print(f"   Route Maps: {route_count}")
        print(f"   Pending Claims: {pending_count}")
        
        # Status breakdown
        print(f"\n📋 Lost Items by Status:")
        for status_code, status_name in LostProduct.STATUS_CHOICES:
            count = LostProduct.objects.filter(status=status_code).count()
            print(f"   {status_name}: {count}")
        
        # Time-based statistics
        now = timezone.now()
        today = LostProduct.objects.filter(created_at__date=now.date()).count()
        this_week = LostProduct.objects.filter(created_at__gte=now - timedelta(days=7)).count()
        this_month = LostProduct.objects.filter(created_at__gte=now - timedelta(days=30)).count()
        
        print(f"\n📅 Recent Activity:")
        print(f"   Items reported today: {today}")
        print(f"   Items reported this week: {this_week}")
        print(f"   Items reported this month: {this_month}")
        
        # Pending claims breakdown
        print(f"\n⏳ Pending Claims by Status:")
        for status_code, status_name in PendingClaim.STATUS_CHOICES:
            count = PendingClaim.objects.filter(status=status_code).count()
            print(f"   {status_name}: {count}")
        
        # Expired claims
        expired_count = PendingClaim.objects.filter(expires_at__lt=now).count()
        print(f"\n⚠️  Expired Claims: {expired_count}")
        
        # Database size estimation
        total_records = lost_count + found_count + match_count + notification_count + route_count + pending_count
        print(f"\n📈 Total Database Records: {total_records}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Advanced Database Management for Retrace")
    parser.add_argument('--stats', action='store_true', help='Show detailed statistics')
    parser.add_argument('--clear-all', action='store_true', help='Clear all items')
    parser.add_argument('--clear-old', type=int, metavar='DAYS', help='Clear items older than N days')
    parser.add_argument('--clear-status', choices=['lost', 'found', 'claimed'], help='Clear items by status')
    parser.add_argument('--clear-expired', action='store_true', help='Clear expired pending claims')
    parser.add_argument('--cleanup', action='store_true', help='Clean up orphaned data')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompts')
    
    args = parser.parse_args()
    
    if not any([args.stats, args.clear_all, args.clear_old, args.clear_status, 
                args.clear_expired, args.cleanup]):
        parser.print_help()
        return
    
    manager = DatabaseManager()
    
    if args.dry_run:
        manager.set_dry_run(True)
    
    if args.stats:
        manager.show_detailed_stats()
    
    if args.clear_all:
        manager.clear_all(force=args.force)
    
    if args.clear_old:
        manager.clear_old_items(days=args.clear_old, force=args.force)
    
    if args.clear_status:
        manager.clear_by_status(args.clear_status, force=args.force)
    
    if args.clear_expired:
        manager.clear_expired_claims(force=args.force)
    
    if args.cleanup:
        manager.cleanup_orphaned_data(force=args.force)

if __name__ == "__main__":
    main()