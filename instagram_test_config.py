#!/usr/bin/env python3
"""
Instagram Test URL Configuration
Central place to maintain test URLs for Instagram downloading
"""

# Main test URL - easy to maintain and update
MAIN_TEST_URL = "https://www.instagram.com/p/DOCCkdVj0Iy/"

# Backup test URLs (public posts that should work)
BACKUP_TEST_URLS = [
    "https://www.instagram.com/p/DABbmEBM8gU/",  # Example public post
    "https://www.instagram.com/reel/C_8gQZNtKhG/",  # Example reel
]

# Invalid URLs for error testing
INVALID_TEST_URLS = [
    "https://www.instagram.com/p/INVALID_POST_ID/",  # Non-existent
    "https://www.instagram.com/p/",  # Malformed
    "https://invalid-url.com/test",  # Non-Instagram
]

# Instructions for updating test URLs
INSTRUCTIONS = """
To update test URLs:

1. Edit MAIN_TEST_URL above with a new public Instagram post
2. Test URLs should be:
   - Public posts (not private accounts)
   - Still available (not deleted)
   - Preferably short videos or images

3. Test the URL with:
   python3 quick_instagram_test.py

4. URLs are automatically used in:
   - test_instagram_downloads.py
   - run_comprehensive_tests.py 
   - quick_instagram_test.py

5. The main service also has a comment about the test URL in:
   /home/pi/skatehive-monorepo/skatehive-instagram-downloader/ytipfs-worker/src/main.py
"""

if __name__ == "__main__":
    print("Instagram Test URL Configuration")
    print("=" * 40)
    print(f"Main Test URL: {MAIN_TEST_URL}")
    print(f"Backup URLs: {len(BACKUP_TEST_URLS)} available")
    print(f"Invalid URLs: {len(INVALID_TEST_URLS)} for error testing")
    print("\n" + INSTRUCTIONS)