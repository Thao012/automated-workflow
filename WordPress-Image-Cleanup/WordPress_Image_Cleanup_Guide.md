# WordPress Image Cleanup Guide

## ⚠️ CRITICAL WARNING - SAFETYCHAMPION INCIDENT

**On 7 July 2025, this tool incorrectly deleted 167 legitimate business assets** from SafetyChampion.digitallink.com.au. The deleted files included client logos, partner assets, and development resources that appeared "unused" because the tool only checked the production WordPress site.

**Key Lessons:**
- ❌ NEVER assume "not in current content" means "not needed"
- ❌ ALWAYS check development/staging environments
- ❌ VERIFY business context for logos and partner assets
- ❌ CONSULT stakeholders before deleting client materials

See [WordPress_Image_Cleanup_Client_Report.html](./WordPress_Image_Cleanup_Client_Report.html) for full details.

---

## Overview
This guide provides a complete reference for safely identifying and removing unused images from WordPress sites using automated scripts with multiple safety layers.

## System Architecture

### Core Scripts
- **`wordpress_image_cleanup.py`** - Main analysis and deletion engine
- **`auto_execute_cleanup.py`** - Non-interactive deletion execution
- **`verify_site_after_cleanup.py`** - Post-cleanup site verification

### Safety Features
- Multi-layer content protection
- Batch processing with rate limiting
- Complete backup before deletion
- Real-time verification and logging

## Image Deletion Criteria

### ✅ PROTECTED IMAGES (Never Deleted)
1. **Featured Images** - Set as post/page featured media (`featured_media` field)
2. **Embedded Content** - Referenced in post/page HTML content via `<img>` tags
3. **Gallery Images** - Used in WordPress `[gallery ids="..."]` shortcodes
4. **Attached Images** - Linked to specific posts (`post` field ≠ 0)
5. **Size Variants** - If any variant (thumbnail, medium, large) is used, all are protected
6. **Theme Images** - Files outside `/wp-content/uploads/` directory

### ❌ FLAGGED FOR DELETION
1. **Orphaned Uploads** - Images uploaded but never attached to content
2. **Temporary Files** - Images with `temp_` prefix or similar patterns
3. **Duplicate Versions** - Old versions when newer ones exist and are used
4. **Test Images** - Clearly marked test/placeholder content
5. **Zero References** - No content references found across entire site

### ⚠️ CRITICAL GAPS (SafetyChampion Incident)
The current implementation **DOES NOT** check:
- **Development/Staging Sites** - Images may be used in non-production environments
- **Business Context** - Client logos, partner assets, case study materials
- **External Usage** - Marketing materials, email campaigns, presentations
- **Future Content** - Planned posts, seasonal campaigns, upcoming projects
- **Historical Value** - Archive materials, company history assets

### 🔍 Detection Process
```python
# Content scanning covers:
- All published posts and pages
- Post/page excerpts
- HTML content parsing for <img> tags
- WordPress gallery shortcode parsing
- Featured image relationships
- Image attachment relationships

# BUT MISSES:
- Development/staging environments
- Business relationship context
- External marketing usage
- Future content plans
```

## Pre-Execution Checklist

### 1. Environment Setup
```bash
# Verify Python dependencies
python3 -c "import requests; print('✓ requests available')"

# Check WordPress API access
curl -u "username:password" "https://site.com/wp-json/wp/v2/media?per_page=1"
```

### 2. Credentials Configuration
```python
# Update in scripts:
BASE_URL = "https://your-site.com"
USERNAME = "your_username"
PASSWORD = "your_app_password"  # WordPress Application Password, not main password
```

### 3. Site Backup (MANDATORY)
- Create full WordPress backup before cleanup
- Verify backup integrity
- Document restoration procedure
- **NEW:** Export complete media library separately

### 4. Business Context Review (NEW)
- Identify all client/partner logos
- Document active business relationships
- Check with marketing team for asset usage
- Review development/staging sites

## Execution Workflow

### Step 1: Analysis (Dry Run)
```bash
cd "/path/to/project"
python3 wordpress_image_cleanup.py
```

**Output Files:**
- `cleanup_report_YYYYMMDD_HHMMSS.txt` - Detailed analysis
- `image_backup_YYYYMMDD_HHMMSS.json` - Backup data
- `image_cleanup.log` - Execution log

### Step 2: Review Results
```bash
# Check the analysis report
cat cleanup_report_YYYYMMDD_HHMMSS.txt

# Verify backup data
head -20 image_backup_YYYYMMDD_HHMMSS.json
```

**Enhanced Review Checklist:**
- [ ] Total images count reasonable
- [ ] Unused images list makes sense
- [ ] No critical images flagged for deletion
- [ ] Storage savings estimate acceptable
- [ ] **NEW:** No client/partner logos in deletion list
- [ ] **NEW:** No industry-specific assets flagged
- [ ] **NEW:** Development site images checked
- [ ] **NEW:** Marketing team approval obtained

### Step 3: Execute Deletion (WITH EXTREME CAUTION)
```bash
# ONLY after thorough review and approval
python3 auto_execute_cleanup.py
```

**Safety Features:**
- Processes 10 images per batch
- 500ms delay between deletions
- 2-second pause between batches
- Continues on individual failures
- Logs all operations

### Step 4: Verify Site Health
```bash
python3 verify_site_after_cleanup.py
```

**Verification Checks:**
- WordPress API accessibility
- Recent posts loading correctly
- Featured images functionality
- Homepage rendering properly
- **NEW:** Client logos still present
- **NEW:** Development sites functioning

## Configuration Options

### Rate Limiting Settings
```python
# In wordpress_image_cleanup.py
self.request_delay = 0.5          # Delay between requests (seconds)
self.max_deletions_per_batch = 10 # Images per batch
self.batch_size = 50              # API pagination size
```

### Safety Controls
```python
# Conservative settings for high-traffic sites
self.request_delay = 1.0          # Slower processing
self.max_deletions_per_batch = 5  # Smaller batches

# Aggressive settings for development sites
self.request_delay = 0.2          # Faster processing
self.max_deletions_per_batch = 20 # Larger batches
```

## Troubleshooting

### Common Issues

#### API Connection Failures
```bash
# Test basic connectivity
curl -I "https://your-site.com"

# Test WordPress API
curl "https://your-site.com/wp-json/wp/v2/"

# Test authentication
curl -u "username:password" "https://your-site.com/wp-json/wp/v2/users/me"
```

#### Permission Errors
- Verify Application Password is correct
- Check user has media management permissions
- Confirm WordPress REST API is enabled

#### Timeout Issues
- Increase `request_delay` setting
- Reduce `max_deletions_per_batch`
- Check server performance during execution

#### Deletion Failures
```python
# Check logs for specific errors
tail -f image_cleanup.log

# Common failure reasons:
# - Image in use (protection working correctly)
# - File system permissions
# - WordPress hooks preventing deletion
```

## Recovery Procedures

### Restore Individual Images
```python
# From backup file, restore specific images
import json
import requests

with open('image_backup_YYYYMMDD_HHMMSS.json', 'r') as f:
    backup = json.load(f)

# Find specific image by ID or URL
target_image = next(img for img in backup if img['id'] == 1234)
print(f"Image: {target_image['title']}")
print(f"URL: {target_image['source_url']}")
```

### Full Restoration Process
1. Identify required images from backup file
2. Re-upload images to WordPress media library
3. Update post/page content with new media IDs
4. Verify all content displays correctly

### SafetyChampion Incident Recovery Example
```bash
# 1. Review backup for client logos
grep -i "client\|partner\|logo" image_backup_20250707_131051.json

# 2. Extract specific industry categories
jq '.[] | select(.title | contains("Energy", "Healthcare", "Mining"))' backup.json

# 3. Restore business-critical assets first
# Use restoration script with filtered list
```

## Performance Metrics

### Typical Results
- **Analysis Time:** 2-5 minutes for 1000 images
- **Deletion Time:** 10-15 minutes for 100 images
- **Storage Savings:** 15-25% typical reduction
- **Success Rate:** 95-100% deletion success

### Optimisation Tips
- Run during low-traffic periods
- Monitor server resources during execution
- Use smaller batches for shared hosting
- Increase delays for slower servers

## File Structure Reference

```
project/
├── wordpress_image_cleanup.py         # Main cleanup engine
├── auto_execute_cleanup.py            # Non-interactive execution
├── verify_site_after_cleanup.py       # Post-cleanup verification
├── WordPress_Image_Cleanup_Client_Report.html  # SafetyChampion incident report
├── cleanup_report_*.txt               # Analysis reports
├── image_backup_*.json                # Backup data
└── image_cleanup.log                  # Execution logs
```

## Security Considerations

### Credential Management
- Use WordPress Application Passwords only
- Never commit credentials to version control
- Store sensitive data in environment variables
- Rotate passwords regularly

### Access Control
- Limit script execution to authorised users
- Use read-only analysis when possible
- Implement approval workflows for large deletions
- Maintain audit logs of all operations

### Data Protection
- Always create backups before deletion
- Verify backup integrity before proceeding
- Store backups in secure, separate location
- Document recovery procedures

## Monitoring and Maintenance

### Regular Cleanup Schedule
- **Monthly:** Run analysis to identify new unused images
- **Quarterly:** Execute cleanup on development sites first
- **Annually:** Review and update deletion criteria
- **NEW:** Always include business stakeholder review

### Health Checks
```bash
# Quick site verification
curl -s "https://your-site.com" | grep -i "error" || echo "✓ Homepage OK"

# Media library status
curl -u "user:pass" "https://your-site.com/wp-json/wp/v2/media?per_page=1" | jq '.[] | {id, title}'

# Check for missing client logos
curl -s "https://your-site.com/clients" | grep -c "logo"
```

### Log Management
```bash
# Archive old logs
mkdir -p logs/archive
mv image_cleanup_*.log logs/archive/

# Monitor current cleanup
tail -f image_cleanup.log | grep -E "(ERROR|WARN|Deleted)"
```

## Integration with CI/CD

### Automated Analysis
```yaml
# Example GitHub Action
name: Image Analysis
on:
  schedule:
    - cron: '0 2 * * 1'  # Weekly Monday 2AM

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Image Analysis
        run: python3 wordpress_image_cleanup.py
      - name: Upload Reports
        uses: actions/upload-artifact@v2
        with:
          name: cleanup-reports
          path: "*_report_*.txt"
      - name: Notify Team
        if: always()
        run: |
          # Send report to stakeholders for review
          # NEVER auto-delete without human approval
```

### Deployment Pipeline
1. Run analysis on staging environment
2. Review results with stakeholders
3. **NEW:** Business team approval required
4. Execute cleanup on staging
5. Verify functionality
6. Apply same cleanup to production

## Support and Maintenance

### Documentation Updates
- Update this guide when modifying scripts
- Document any site-specific customisations
- Maintain changelog of criteria modifications
- **NEW:** Document all incidents and lessons learned

### Script Maintenance
- Test scripts on development sites first
- Update WordPress API compatibility as needed
- Monitor for changes in image handling
- **NEW:** Regular review of deletion criteria with business team

### Knowledge Transfer
- Ensure multiple team members understand process
- Document any manual intervention requirements
- Maintain emergency contact procedures
- **NEW:** Include business context in all documentation

---

## Quick Reference Commands

```bash
# Full cleanup workflow
python3 wordpress_image_cleanup.py          # Analyse (dry run)
python3 auto_execute_cleanup.py             # Execute deletion
python3 verify_site_after_cleanup.py        # Verify results

# Emergency verification
curl -I "https://your-site.com"              # Quick site check
tail -20 image_cleanup.log                   # Check recent activity

# Backup verification
ls -la image_backup_*.json                   # List backup files
jq '.[] | {id, title, size: .file_size}' image_backup_*.json | head -10

# SafetyChampion incident checks
grep -i "logo\|client\|partner" cleanup_report_*.txt
jq '.[] | select(.title | test("Energy|Healthcare|Mining|Food"; "i"))' backup.json
```

This guide ensures consistent, safe image cleanup procedures whilst maintaining comprehensive documentation for future AI agents or team members. The SafetyChampion incident serves as a critical reminder that technical checks alone are insufficient - business context is essential.