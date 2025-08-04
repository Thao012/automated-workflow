#!/usr/bin/env python3
"""
Auto Execute Image Cleanup - Non-interactive deletion
Australian English version with enhanced safety features
"""

from wordpress_image_cleanup import WordPressImageCleanup
import json
import time
from datetime import datetime

def main():
    """Execute the actual image deletion automatically"""
    
    print("WordPress Image Cleanup - AUTO EXECUTION (Australian Edition)")
    print("=" * 65)
    print("🚀 Starting automatic deletion of unused images...")
    print()
    
    # Load the backup file to show what will be deleted
    backup_files = []
    import glob
    backup_files = glob.glob('image_backup_*.json')
    
    if not backup_files:
        print("❌ No backup file found. Please run the analysis first.")
        return
    
    # Use the most recent backup file
    backup_file = max(backup_files)
    
    try:
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        print(f"📋 Deleting {len(backup_data)} unused images from backup: {backup_file}")
        
        # Calculate total size
        total_size = sum(img['file_size'] for img in backup_data)
        print(f"💾 Total size to free: {total_size / (1024*1024):.2f} MB")
        print()
        
        # Show sample of what will be deleted
        print("Sample of images to be deleted:")
        for i, img in enumerate(backup_data[:5]):
            print(f"  {i+1}. {img['title']} ({img['file_size']/1024:.1f} KB)")
        if len(backup_data) > 5:
            print(f"  ... and {len(backup_data) - 5} more images")
        print()
        
    except FileNotFoundError:
        print("❌ Backup file not found. Please run the analysis first.")
        return
    except json.JSONDecodeError:
        print("❌ Invalid backup file format. Please run the analysis again.")
        return
    
    print("⏳ Starting deletion process with safety controls...")
    print("   Processing in batches of 10 with delays to prevent timeouts...")
    print()
    
    # IMPORTANT: Update these credentials for your WordPress site
    BASE_URL = "https://your-wordpress-site.com.au"
    USERNAME = "your_username"
    PASSWORD = "your_application_password"  # WordPress Application Password
    
    cleanup = WordPressImageCleanup(BASE_URL, USERNAME, PASSWORD)
    
    # Test connection first
    if not cleanup.test_connection():
        print("❌ Connection test failed. Aborting deletion.")
        return
    
    print("✅ WordPress API connection verified")
    print("🗑️ Beginning deletion process...")
    print()
    
    try:
        # Run with actual deletion (dry_run=False)
        results = cleanup.run_cleanup(dry_run=False)
        
        if "error" in results:
            print(f"❌ Error: {results['error']}")
            return
        
        print("\n" + "=" * 65)
        print("DELETION COMPLETED!")
        print("=" * 65)
        print(f"📊 Total Images Processed: {results['deletion_results']['total']}")
        print(f"✅ Successfully Deleted: {results['deletion_results']['deleted']}")
        print(f"❌ Failed to Delete: {results['deletion_results']['failed']}")
        print(f"⏭️  Skipped: {results['deletion_results']['skipped']}")
        
        # Calculate actual savings
        if results['deletion_results']['deleted'] > 0:
            deleted_percentage = (results['deletion_results']['deleted'] / len(backup_data)) * 100
            deleted_size = (results['deletion_results']['deleted'] / len(backup_data)) * total_size
            print(f"\n💾 Storage Freed: {deleted_size / (1024*1024):.2f} MB")
            print(f"📈 Deletion Rate: {deleted_percentage:.1f}%")
        
        success_rate = (results['deletion_results']['deleted'] / results['deletion_results']['total']) * 100
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if results['deletion_results']['failed'] > 0:
            print(f"\n⚠️  {results['deletion_results']['failed']} images failed to delete")
            print("   This is normal - some may be protected or in use")
            print("   Check image_cleanup.log for details")
        
        print(f"\n💾 Original backup preserved: {backup_file}")
        print(f"💾 New backup created: {results['backup_file']}")
        print(f"📊 Detailed log: image_cleanup.log")
        
        print("\n✅ WordPress image cleanup completed successfully!")
        print(f"🕐 Completed at: {datetime.now().strftime('%d/%m/%Y %H:%M:%S AEST')}")
        
        # Offer to run verification
        print("\n💡 Tip: Run 'python3 verify_site_after_cleanup.py' to verify site health")
        
    except KeyboardInterrupt:
        print("\n⚠️ Deletion interrupted by user. Some images may have been deleted.")
        print("Check image_cleanup.log for details of what was processed.")
    except Exception as e:
        print(f"\n❌ Unexpected error during deletion: {e}")
        print("Check image_cleanup.log for detailed error information.")

if __name__ == "__main__":
    main()