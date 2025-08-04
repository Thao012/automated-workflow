#!/usr/bin/env python3
"""
Site Verification After Image Cleanup
Checks that the site is still functioning properly after image deletion
Australian English version with timezone awareness
"""

import requests
import re
import json
from datetime import datetime
import time

def verify_site_health(base_url, username, password):
    """Verify site is still healthy after cleanup"""
    
    print("🔍 Verifying site health after image cleanup...")
    
    session = requests.Session()
    session.auth = (username, password)
    session.timeout = 30  # 30 second timeout for Australian hosting
    
    checks = {
        'api_access': False,
        'recent_posts': False,
        'images_loading': False,
        'no_broken_links': False,
        'homepage_loading': False
    }
    
    # Check 1: WordPress API still accessible
    try:
        response = session.get(f"{base_url}/wp-json/wp/v2/")
        if response.status_code == 200:
            checks['api_access'] = True
            print("✅ WordPress API accessible")
        else:
            print(f"❌ WordPress API issue: {response.status_code}")
    except Exception as e:
        print(f"❌ WordPress API error: {e}")
    
    # Check 2: Recent posts are accessible
    try:
        response = session.get(f"{base_url}/wp-json/wp/v2/posts", 
                              params={'per_page': 5, '_embed': True})
        if response.status_code == 200:
            posts = response.json()
            if posts:
                checks['recent_posts'] = True
                print(f"✅ Recent posts accessible ({len(posts)} found)")
                
                # Check 3: Featured images still loading
                working_images = 0
                for post in posts:
                    if '_embedded' in post and 'wp:featuredmedia' in post['_embedded']:
                        featured = post['_embedded']['wp:featuredmedia'][0]
                        img_url = featured.get('source_url', '')
                        if img_url:
                            try:
                                img_response = requests.head(img_url, timeout=10)
                                if img_response.status_code == 200:
                                    working_images += 1
                            except:
                                pass
                
                if working_images > 0:
                    checks['images_loading'] = True
                    print(f"✅ Featured images loading ({working_images} verified)")
                else:
                    print("⚠️  No working featured images found (may be normal after cleanup)")
            else:
                print("⚠️  No recent posts found")
    except Exception as e:
        print(f"❌ Posts check error: {e}")
    
    # Check 4: Homepage loads properly
    try:
        response = requests.get(base_url, timeout=30)
        if response.status_code == 200:
            checks['homepage_loading'] = True
            
            # Look for broken image indicators
            content = response.text
            broken_img_patterns = [
                r'alt="[^"]*"\s+src=""',  # Empty src
                r'src="[^"]*404[^"]*"',   # 404 in URL
                r'src="[^"]*error[^"]*"', # Error in URL
                r'src="[^"]*missing[^"]*"', # Missing in URL
            ]
            
            broken_found = False
            for pattern in broken_img_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    broken_found = True
                    break
            
            if not broken_found:
                checks['no_broken_links'] = True
                print("✅ Homepage loads without obvious broken images")
            else:
                print("⚠️  Possible broken images detected on homepage")
                
            # Check for common Australian WordPress themes/plugins
            if 'astra' in content.lower() or 'oceanwp' in content.lower():
                print("✅ Australian-popular theme detected and loading")
                
        else:
            print(f"❌ Homepage loading issue: {response.status_code}")
    except Exception as e:
        print(f"❌ Homepage check error: {e}")
    
    # Check 5: Performance check (Australian hosting considerations)
    try:
        start_time = time.time()
        response = requests.get(base_url, timeout=30)
        load_time = time.time() - start_time
        
        if load_time < 5.0:  # Under 5 seconds is good for Australian hosting
            print(f"✅ Site loading time: {load_time:.2f}s (Good for Australian hosting)")
        elif load_time < 10.0:
            print(f"⚠️  Site loading time: {load_time:.2f}s (Acceptable for Australian hosting)")
        else:
            print(f"❌ Site loading time: {load_time:.2f}s (Slow - may need optimisation)")
            
    except Exception as e:
        print(f"⚠️  Could not measure load time: {e}")
    
    # Summary
    passed = sum(checks.values())
    total = len(checks)
    
    print(f"\n📊 Site Health: {passed}/{total} checks passed")
    
    if passed == total:
        print("✅ Site appears fully healthy after cleanup!")
        health_status = "excellent"
    elif passed >= total - 1:
        print("⚠️  Site mostly healthy with minor issues")
        health_status = "good"
    elif passed >= total - 2:
        print("⚠️  Site functional but has some issues to review")
        health_status = "fair"
    else:
        print("❌ Site may have significant issues - review carefully")
        health_status = "poor"
    
    return checks, health_status

def main():
    """Run site verification with Australian standards"""
    
    # IMPORTANT: Update these credentials for your WordPress site
    BASE_URL = "https://your-wordpress-site.com.au"
    USERNAME = "your_username"
    PASSWORD = "your_application_password"  # WordPress Application Password
    
    print("WordPress Site Verification After Image Cleanup (Australian Edition)")
    print("=" * 75)
    print(f"Site: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%d/%m/%Y %H:%M:%S AEST')}")
    print()
    
    try:
        results, health_status = verify_site_health(BASE_URL, USERNAME, PASSWORD)
        
        # Save verification log
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'site': BASE_URL,
            'checks': results,
            'health_status': health_status,
            'summary': f"{sum(results.values())}/{len(results)} checks passed",
            'timezone': 'AEST/AEDT',
            'notes': 'Post-cleanup verification for Australian WordPress site'
        }
        
        log_filename = f"site_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_filename, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        print(f"\n💾 Verification log saved: {log_filename}")
        
        # Provide specific recommendations
        print("\n📋 RECOMMENDATIONS:")
        if health_status == "excellent":
            print("✅ No action required - site is performing excellently")
        elif health_status == "good":
            print("✅ Minor monitoring recommended, but site is healthy")
        elif health_status == "fair":
            print("⚠️  Review any failed checks and monitor site performance")
            print("⚠️  Consider running a backup verification")
        else:
            print("❌ Immediate attention required - check logs for details")
            print("❌ Consider restoring from backup if issues persist")
        
        # Australian-specific recommendations
        print("\n🇦🇺 AUSTRALIAN HOSTING CONSIDERATIONS:")
        print("   • Monitor site during peak Australian business hours")
        print("   • Consider CDN optimisation for interstate visitors")
        print("   • Ensure mobile performance for Australian 4G/5G networks")
        
        print("\n" + "=" * 75)
        
    except KeyboardInterrupt:
        print("\n⚠️ Verification interrupted by user")
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        print("Check your credentials and site accessibility")

if __name__ == "__main__":
    main()