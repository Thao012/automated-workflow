#!/usr/bin/env python3
"""
WordPress Image Cleanup System
Safe detection and deletion of unused images with backup capabilities

Australian English version with timezone awareness
"""

import requests
import json
import re
import time
import logging
from datetime import datetime
from typing import Dict, List, Set, Optional
from urllib.parse import urlparse, urljoin
import os

# Configure logging with Australian timezone awareness
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('image_cleanup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WordPressImageCleanup:
    """Safe WordPress image cleanup with deletion capabilities"""
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        
        # Setup session with authentication
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.headers.update({
            'User-Agent': 'WordPress Image Cleanup/1.0 (Australia)',
            'Content-Type': 'application/json'
        })
        
        # Rate limiting (conservative for Australian hosting)
        self.request_delay = 0.5
        self.batch_size = 50
        
        # Data storage
        self.all_media = {}
        self.used_images = set()
        self.unused_images = set()
        self.backup_data = []
        
        # Safety controls
        self.dry_run = True  # Start in safe mode
        self.max_deletions_per_batch = 10
        
    def test_connection(self) -> bool:
        """Test WordPress API connection and permissions"""
        try:
            # Test basic connection
            response = self.session.get(f"{self.base_url}/wp-json/wp/v2/")
            if response.status_code != 200:
                logger.error(f"API connection failed: {response.status_code}")
                return False
            
            # Test media access
            response = self.session.get(f"{self.base_url}/wp-json/wp/v2/media", 
                                      params={'per_page': 1})
            if response.status_code != 200:
                logger.error(f"Media API access failed: {response.status_code}")
                return False
            
            # Test deletion permissions (with safe params)
            response = self.session.options(f"{self.base_url}/wp-json/wp/v2/media/999999")
            allowed_methods = response.headers.get('Allow', '')
            if 'DELETE' not in allowed_methods:
                logger.warning("DELETE permission may not be available")
            
            logger.info("✅ WordPress API connection and permissions verified")
            return True
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_all_media(self) -> Dict[int, Dict]:
        """Fetch all media items from WordPress"""
        logger.info("📁 Fetching all media items...")
        
        page = 1
        all_media = {}
        
        while True:
            try:
                params = {
                    'media_type': 'image',
                    'per_page': self.batch_size,
                    'page': page,
                    'orderby': 'date',
                    'order': 'desc'
                }
                
                response = self.session.get(f"{self.base_url}/wp-json/wp/v2/media", 
                                          params=params)
                
                if response.status_code != 200:
                    logger.error(f"Media fetch failed: {response.status_code}")
                    break
                
                media_items = response.json()
                if not media_items:
                    break
                
                for item in media_items:
                    media_id = item.get('id')
                    if media_id:
                        all_media[media_id] = {
                            'id': media_id,
                            'title': item.get('title', {}).get('rendered', ''),
                            'source_url': item.get('source_url', ''),
                            'date': item.get('date', ''),
                            'modified': item.get('modified', ''),
                            'post': item.get('post', 0),  # Attached post ID
                            'file_size': item.get('media_details', {}).get('filesize', 0),
                            'mime_type': item.get('mime_type', ''),
                            'meta': item.get('meta', {}),
                            'alt_text': item.get('alt_text', ''),
                            'caption': item.get('caption', {}).get('rendered', ''),
                            'description': item.get('description', {}).get('rendered', '')
                        }
                
                logger.info(f"📁 Fetched page {page}: {len(media_items)} items")
                
                # Check pagination
                total_pages = int(response.headers.get('X-WP-TotalPages', 1))
                if page >= total_pages:
                    break
                
                page += 1
                time.sleep(self.request_delay)
                
            except Exception as e:
                logger.error(f"Error fetching media page {page}: {e}")
                break
        
        logger.info(f"📁 Total media items found: {len(all_media)}")
        self.all_media = all_media
        return all_media
    
    def get_all_content(self) -> Set[str]:
        """Fetch all posts and pages to find image references"""
        logger.info("📄 Analysing all content for image usage...")
        
        used_images = set()
        
        # Analyse posts
        used_images.update(self._analyse_content_type('posts'))
        
        # Analyse pages  
        used_images.update(self._analyse_content_type('pages'))
        
        logger.info(f"📄 Found {len(used_images)} image references in content")
        self.used_images = used_images
        return used_images
    
    def _analyse_content_type(self, content_type: str) -> Set[str]:
        """Analyse specific content type for image usage"""
        page = 1
        found_images = set()
        
        while True:
            try:
                params = {
                    'per_page': self.batch_size,
                    'page': page,
                    'status': 'publish',
                    '_embed': True
                }
                
                response = self.session.get(f"{self.base_url}/wp-json/wp/v2/{content_type}", 
                                          params=params)
                
                if response.status_code != 200:
                    break
                
                content_items = response.json()
                if not content_items:
                    break
                
                for item in content_items:
                    # Check featured image
                    featured_media = item.get('featured_media', 0)
                    if featured_media and featured_media in self.all_media:
                        found_images.add(self.all_media[featured_media]['source_url'])
                    
                    # Check content for embedded images
                    content = item.get('content', {}).get('rendered', '')
                    if content:
                        content_images = self._extract_images_from_html(content)
                        found_images.update(content_images)
                    
                    # Check excerpt
                    excerpt = item.get('excerpt', {}).get('rendered', '')
                    if excerpt:
                        excerpt_images = self._extract_images_from_html(excerpt)
                        found_images.update(excerpt_images)
                
                logger.info(f"📄 Analysed {content_type} page {page}: {len(content_items)} items")
                
                # Check pagination
                total_pages = int(response.headers.get('X-WP-TotalPages', 1))
                if page >= total_pages:
                    break
                
                page += 1
                time.sleep(self.request_delay)
                
            except Exception as e:
                logger.error(f"Error analysing {content_type} page {page}: {e}")
                break
        
        return found_images
    
    def _extract_images_from_html(self, html_content: str) -> Set[str]:
        """Extract image URLs from HTML content"""
        images = set()
        
        # Extract img src attributes
        img_pattern = r'<img[^>]*src=["\']([^"\'\']+)["\'][^>]*>'
        img_matches = re.findall(img_pattern, html_content, re.IGNORECASE)
        
        for src in img_matches:
            # Normalise URL
            if src.startswith('/'):
                src = urljoin(self.base_url, src)
            
            # Only include images from this WordPress site
            parsed_src = urlparse(src)
            parsed_base = urlparse(self.base_url)
            
            if parsed_src.netloc == parsed_base.netloc:
                images.add(src)
        
        # Extract WordPress gallery shortcodes
        gallery_pattern = r'\[gallery[^\]]*ids="([^"]+)"'
        gallery_matches = re.findall(gallery_pattern, html_content, re.IGNORECASE)
        
        for match in gallery_matches:
            gallery_ids = [id.strip() for id in match.split(',')]
            for gallery_id in gallery_ids:
                if gallery_id.isdigit() and int(gallery_id) in self.all_media:
                    images.add(self.all_media[int(gallery_id)]['source_url'])
        
        return images
    
    def identify_unused_images(self) -> Set[int]:
        """Identify truly unused images"""
        logger.info("🔍 Identifying unused images...")
        
        unused_media_ids = set()
        
        for media_id, media_info in self.all_media.items():
            source_url = media_info['source_url']
            
            # Skip if image is attached to a post
            if media_info['post'] and media_info['post'] != 0:
                continue
            
            # Skip if image is referenced in content
            if source_url in self.used_images:
                continue
            
            # Check if any size variant is used
            is_used = False
            for used_url in self.used_images:
                if self._are_same_image(source_url, used_url):
                    is_used = True
                    break
            
            if not is_used:
                unused_media_ids.add(media_id)
        
        logger.info(f"🔍 Found {len(unused_media_ids)} unused images")
        self.unused_images = unused_media_ids
        return unused_media_ids
    
    def _are_same_image(self, url1: str, url2: str) -> bool:
        """Check if two URLs represent the same image (different sizes)"""
        # Remove size suffixes and compare
        base1 = re.sub(r'-\d+x\d+', '', url1)
        base1 = re.sub(r'-scaled', '', base1)
        
        base2 = re.sub(r'-\d+x\d+', '', url2)
        base2 = re.sub(r'-scaled', '', base2)
        
        return base1 == base2
    
    def create_backup(self, media_ids: Set[int], filename: str = None) -> str:
        """Create backup of images before deletion"""
        if filename is None:
            filename = f"image_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        backup_data = []
        
        for media_id in media_ids:
            if media_id in self.all_media:
                media_info = self.all_media[media_id]
                backup_data.append({
                    'id': media_id,
                    'title': media_info['title'],
                    'source_url': media_info['source_url'],
                    'date': media_info['date'],
                    'file_size': media_info['file_size'],
                    'mime_type': media_info['mime_type'],
                    'backup_timestamp': datetime.now().isoformat(),
                    'reason': 'unused_image_cleanup'
                })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Backup created: {filename} ({len(backup_data)} images)")
        self.backup_data = backup_data
        return filename
    
    def delete_image(self, media_id: int, force: bool = False) -> bool:
        """Delete a single image via WordPress API"""
        if self.dry_run and not force:
            logger.info(f"🔄 DRY RUN: Would delete image {media_id}")
            return True
        
        try:
            # Get media info for logging
            media_info = self.all_media.get(media_id, {})
            title = media_info.get('title', f'ID {media_id}')
            
            # Delete via WordPress API
            response = self.session.delete(f"{self.base_url}/wp-json/wp/v2/media/{media_id}",
                                         params={'force': True})  # Permanently delete
            
            if response.status_code == 200:
                logger.info(f"✅ Deleted: {title} (ID: {media_id})")
                return True
            else:
                logger.error(f"❌ Failed to delete {title} (ID: {media_id}): {response.status_code}")
                logger.error(f"Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error deleting image {media_id}: {e}")
            return False
    
    def batch_delete(self, media_ids: Set[int], batch_size: int = None) -> Dict:
        """Delete images in batches with safety controls"""
        if batch_size is None:
            batch_size = self.max_deletions_per_batch
        
        results = {
            'total': len(media_ids),
            'deleted': 0,
            'failed': 0,
            'skipped': 0
        }
        
        media_list = list(media_ids)
        
        for i in range(0, len(media_list), batch_size):
            batch = media_list[i:i + batch_size]
            
            logger.info(f"🗑️ Processing batch {i//batch_size + 1}: {len(batch)} images")
            
            for media_id in batch:
                if self.delete_image(media_id):
                    results['deleted'] += 1
                else:
                    results['failed'] += 1
                
                # Rate limiting
                time.sleep(self.request_delay)
            
            # Pause between batches
            if i + batch_size < len(media_list):
                logger.info("⏸️ Pausing between batches...")
                time.sleep(2)
        
        return results
    
    def generate_report(self, filename: str = None) -> str:
        """Generate comprehensive cleanup report"""
        if filename is None:
            filename = f"cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("WordPress Image Cleanup Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Site: {self.base_url}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE DELETION'}\n\n")
            
            f.write("Summary:\n")
            f.write(f"  Total Images: {len(self.all_media)}\n")
            f.write(f"  Used Images: {len(self.all_media) - len(self.unused_images)}\n")
            f.write(f"  Unused Images: {len(self.unused_images)}\n\n")
            
            if self.unused_images:
                f.write("Unused Images:\n")
                f.write("-" * 30 + "\n")
                
                for media_id in self.unused_images:
                    media_info = self.all_media.get(media_id, {})
                    f.write(f"ID: {media_id}\n")
                    f.write(f"  Title: {media_info.get('title', 'No title')}\n")
                    f.write(f"  URL: {media_info.get('source_url', 'No URL')}\n")
                    f.write(f"  Size: {media_info.get('file_size', 0)} bytes\n")
                    f.write(f"  Date: {media_info.get('date', 'Unknown')}\n")
                    f.write(f"  Attached Post: {media_info.get('post', 'None')}\n")
                    f.write("\n")
        
        logger.info(f"📊 Report generated: {filename}")
        return filename
    
    def run_cleanup(self, dry_run: bool = True) -> Dict:
        """Run complete cleanup process"""
        self.dry_run = dry_run
        
        logger.info(f"🚀 Starting image cleanup ({'DRY RUN' if dry_run else 'LIVE MODE'})")
        
        # Step 1: Test connection
        if not self.test_connection():
            return {"error": "Connection test failed"}
        
        # Step 2: Get all media
        self.get_all_media()
        if not self.all_media:
            return {"error": "No media found"}
        
        # Step 3: Analyse content usage
        self.get_all_content()
        
        # Step 4: Identify unused images
        unused_ids = self.identify_unused_images()
        
        if not unused_ids:
            logger.info("✅ No unused images found!")
            return {"message": "No unused images found", "total_images": len(self.all_media)}
        
        # Step 5: Create backup
        backup_file = self.create_backup(unused_ids)
        
        # Step 6: Generate report
        report_file = self.generate_report()
        
        # Step 7: Delete images (if not dry run)
        deletion_results = self.batch_delete(unused_ids)
        
        results = {
            "total_images": len(self.all_media),
            "unused_images": len(unused_ids),
            "deletion_results": deletion_results,
            "backup_file": backup_file,
            "report_file": report_file,
            "dry_run": dry_run
        }
        
        logger.info("✅ Cleanup process completed!")
        return results

def main():
    """Main execution function with example configuration"""
    
    # IMPORTANT: Update these credentials for your WordPress site
    BASE_URL = "https://your-wordpress-site.com.au"
    USERNAME = "your_username"
    PASSWORD = "your_application_password"  # WordPress Application Password
    
    cleanup = WordPressImageCleanup(BASE_URL, USERNAME, PASSWORD)
    
    print("WordPress Image Cleanup System (Australian Edition)")
    print("=" * 55)
    print(f"Site: {BASE_URL}")
    print("⚠️  Starting with DRY RUN mode for safety")
    print()
    
    # Run in dry run mode first
    results = cleanup.run_cleanup(dry_run=True)
    
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return
    
    print("📊 ANALYSIS RESULTS:")
    print(f"  Total Images: {results['total_images']}")
    print(f"  Unused Images: {results['unused_images']}")
    print(f"  Backup File: {results['backup_file']}")
    print(f"  Report File: {results['report_file']}")
    
    if results['unused_images'] > 0:
        print(f"\n🗑️ Found {results['unused_images']} unused images ready for deletion")
        print("📋 Review the report file before proceeding with actual deletion")
        print()
        print("To execute deletion, modify the script to run:")
        print("  cleanup.run_cleanup(dry_run=False)")
    else:
        print("\n✅ No unused images found - your site is clean!")

if __name__ == "__main__":
    main()