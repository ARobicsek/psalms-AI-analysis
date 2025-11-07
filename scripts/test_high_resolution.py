"""
Test high-resolution screenshot capture.

This script sets a large window size and optionally zooms to get higher resolution.

USAGE:
1. Make sure Chrome with remote debugging is running:
   "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:/temp/chrome_debug"

2. Navigate to: https://babel.hathitrust.org/cgi/pt?id=uc1.b4508670&seq=39

3. Run: python scripts/test_high_resolution.py
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Test configuration
BOOK_ID = "uc1.b4508670"
START_PAGE = 39
END_PAGE = 41  # Just 3 pages
OUTPUT_DIR = "data/hirsch_images_high_res_test"
CHROME_DEBUG_PORT = 9222

# Resolution settings
WINDOW_WIDTH = 2560   # Large window width
WINDOW_HEIGHT = 1440  # Large window height
ZOOM_LEVEL = 100      # 100 = normal, 150 = 1.5x zoom, 200 = 2x zoom

def main():
    print("="*70)
    print("High Resolution Screenshot Test")
    print("="*70)
    print()
    print(f"Settings:")
    print(f"  Window size: {WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    print(f"  Zoom level: {ZOOM_LEVEL}%")
    print()

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Connect to existing browser
    print("Connecting to Chrome browser...")
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", f"localhost:{CHROME_DEBUG_PORT}")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("OK: Connected to browser")
    except Exception as e:
        print(f"ERROR: Could not connect: {e}")
        print("\nMake sure Chrome is running with:")
        print('  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:/temp/chrome_debug"')
        return

    print()
    successful = 0

    try:
        # Set window size ONCE at the beginning
        print(f"Setting window size to {WINDOW_WIDTH}x{WINDOW_HEIGHT}...")
        driver.set_window_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        time.sleep(0.5)
        print("OK: Window size set")
        print()

        # Set zoom level ONCE at the beginning
        if ZOOM_LEVEL != 100:
            print(f"Setting zoom level to {ZOOM_LEVEL}%...")
            driver.execute_script(f"document.body.style.zoom='{ZOOM_LEVEL}%'")
            time.sleep(0.5)
            print("OK: Zoom set")
            print()

        for page_num in range(START_PAGE, END_PAGE + 1):
            print(f"Page {page_num}:")
            print("-" * 40)

            # Navigate
            url = f"https://babel.hathitrust.org/cgi/pt?id={BOOK_ID};view=1up;seq={page_num}"
            driver.get(url)

            # Wait for page to load
            print("  Waiting for page to load...")
            time.sleep(3)

            # Take screenshot
            screenshot_path = os.path.join(OUTPUT_DIR, f"page_{page_num:04d}.png")
            driver.save_screenshot(screenshot_path)

            # Check file size
            file_size = os.path.getsize(screenshot_path)
            print(f"  OK: Saved page_{page_num:04d}.png ({file_size:,} bytes)")
            successful += 1

            # Delay before next page
            if page_num < END_PAGE:
                time.sleep(2)

        print()
        print("="*70)
        print("Test Complete!")
        print("="*70)
        print(f"Captured: {successful}/{END_PAGE - START_PAGE + 1} pages")
        print(f"Output: {OUTPUT_DIR}")
        print()
        print(f"Images captured at {WINDOW_WIDTH}x{WINDOW_HEIGHT} with {ZOOM_LEVEL}% zoom")
        print()
        print("Next steps:")
        print(f"  1. Compare with original images in data/hirsch_images/")
        print(f"  2. Check resolution and text clarity")
        print(f"  3. Test OCR on high-res version")
        print(f"  4. If better, update main script with these settings")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")

    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\nBrowser left open for inspection")

if __name__ == "__main__":
    main()
