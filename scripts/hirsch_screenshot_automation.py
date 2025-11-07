"""
Automated screenshot capture from HathiTrust using existing browser session.

USAGE:
1. Open Chrome with remote debugging:
   chrome.exe --remote-debugging-port=9222 --user-data-dir="C:/temp/chrome_debug"

2. Navigate to first page manually in that Chrome window:
   https://babel.hathitrust.org/cgi/pt?id=uc1.b4508670&seq=33

3. Run this script:
   python scripts/hirsch_screenshot_automation.py

The script will attach to your open browser and automatically capture screenshots.

Requirements: pip install selenium webdriver-manager
"""

import os
import time
import io
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys
except ImportError:
    print("ERROR: Selenium is not installed.")
    print("Install with: pip install selenium")
    exit(1)

try:
    from PIL import Image
    import numpy as np
except ImportError:
    print("ERROR: PIL/numpy not installed (needed for loading screen detection).")
    print("Install with: pip install pillow numpy")
    exit(1)

# --- Configuration ---
BOOK_ID = "uc1.b4508670"
START_PAGE = 33
END_PAGE = 533  # All 501 pages
OUTPUT_DIR = "data/hirsch_images"
PAGE_DELAY_SECONDS = 2  # Short delay between pages
CHROME_DEBUG_PORT = 9222

# For testing, use smaller range:
# END_PAGE = 35  # Just 3 pages for testing
# ---------------------

def is_loading_screen(screenshot_bytes):
    """
    Detect if the screenshot shows a loading screen.

    Returns True if it's a loading screen, False otherwise.
    """
    try:
        # Convert screenshot to PIL Image
        img = Image.open(io.BytesIO(screenshot_bytes))

        # Convert to numpy array
        img_array = np.array(img)

        # Calculate standard deviation of pixel values
        # Low std dev = uniform/blank image = likely loading
        std_dev = np.std(img_array)

        # Threshold: if std dev is very low, it's likely a loading screen
        if std_dev < 20:
            return True

        # Additional check: look for very uniform images
        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = np.mean(img_array, axis=2)
        else:
            gray = img_array

        # Check if most pixels are similar
        pixel_range = np.ptp(gray)  # peak-to-peak (max - min)
        if pixel_range < 30:  # Very small range = uniform = loading
            return True

        return False

    except Exception as e:
        print(f"    WARNING: Error detecting loading screen: {e}")
        return False

def wait_for_page_load(driver, max_wait=10):
    """
    Wait for page to fully load (not showing loading screen).

    Returns True if page loaded, False if timeout.
    """
    for attempt in range(max_wait):
        time.sleep(1)

        # Take a quick screenshot to check
        screenshot_bytes = driver.get_screenshot_as_png()

        if not is_loading_screen(screenshot_bytes):
            return True

        if attempt < max_wait - 1:  # Don't print on last attempt
            print(".", end="", flush=True)

    return False

def connect_to_existing_browser(debug_port=9222):
    """
    Connect to an existing Chrome browser opened with remote debugging.

    Before running this, open Chrome with:
    chrome.exe --remote-debugging-port=9222 --user-data-dir="C:/temp/chrome_debug"
    """
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", f"localhost:{debug_port}")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        print(f"OK: Successfully connected to existing Chrome browser")
        return driver
    except Exception as e:
        print(f"ERROR: Failed to connect to browser: {e}")
        print("\nMake sure Chrome is running with remote debugging enabled:")
        print('  chrome.exe --remote-debugging-port=9222 --user-data-dir="C:/temp/chrome_debug"')
        print("\nThen navigate to the first HathiTrust page manually.")
        return None

def capture_page_screenshot(driver, page_num, output_dir):
    """Capture screenshot of current page with loading screen detection."""
    try:
        # Wait for page to load (not showing loading screen)
        if not wait_for_page_load(driver, max_wait=10):
            print(f" ⚠ Still loading after 10s", end="")

        # Additional wait for any animations
        time.sleep(1)

        # Take screenshot
        screenshot_bytes = driver.get_screenshot_as_png()

        # Final check: make sure it's not a loading screen
        if is_loading_screen(screenshot_bytes):
            print(f" ⚠ Loading screen detected, retrying...", end="")
            time.sleep(2)
            screenshot_bytes = driver.get_screenshot_as_png()

            # If still loading, give up
            if is_loading_screen(screenshot_bytes):
                print(f" ✗ SKIP (still loading)")
                return False

        # Save screenshot
        screenshot_path = os.path.join(output_dir, f"page_{page_num:04d}.png")
        with open(screenshot_path, 'wb') as f:
            f.write(screenshot_bytes)

        # Get file size for verification
        file_size = os.path.getsize(screenshot_path)
        print(f" OK: {file_size:,} bytes")

        return True

    except Exception as e:
        print(f" ERROR: {e}")
        return False

def navigate_to_page(driver, book_id, page_num):
    """Navigate to a specific page."""
    url = f"https://babel.hathitrust.org/cgi/pt?id={book_id};view=1up;seq={page_num}"
    driver.get(url)

    # Wait for navigation to complete
    time.sleep(1.5)

def main():
    """Main function to automate screenshot capture."""

    print("="*70)
    print("HathiTrust Screenshot Automation Tool")
    print("="*70)
    print()

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Calculate total pages
    total_pages = END_PAGE - START_PAGE + 1

    print(f"Configuration:")
    print(f"  Book ID: {BOOK_ID}")
    print(f"  Page range: {START_PAGE} to {END_PAGE} ({total_pages} pages)")
    print(f"  Output directory: {OUTPUT_DIR}")
    print(f"  Delay between pages: {PAGE_DELAY_SECONDS} seconds")
    print()

    # Estimate time
    estimated_minutes = (total_pages * (PAGE_DELAY_SECONDS + 1.5)) / 60
    print(f"Estimated time: ~{estimated_minutes:.1f} minutes")
    print()

    # Connect to existing browser
    print("Connecting to Chrome browser...")
    driver = connect_to_existing_browser(CHROME_DEBUG_PORT)

    if not driver:
        print("\nERROR: Could not connect to browser. Exiting.")
        return

    print()
    print(f"Starting screenshot capture...")
    print(f"You can minimize the browser window, but don't close it!")
    print()

    successful_captures = 0
    failed_captures = 0

    try:
        for page_num in range(START_PAGE, END_PAGE + 1):
            # Progress indicator
            progress = page_num - START_PAGE + 1
            print(f"[{progress}/{total_pages}] Page {page_num}...", end=" ")

            # Navigate to page
            navigate_to_page(driver, BOOK_ID, page_num)

            # Capture screenshot
            success = capture_page_screenshot(driver, page_num, OUTPUT_DIR)

            if success:
                successful_captures += 1
            else:
                failed_captures += 1

            # Short delay before next page
            if page_num < END_PAGE:
                time.sleep(PAGE_DELAY_SECONDS)

        print()
        print("="*70)
        print("Screenshot capture complete!")
        print("="*70)
        print(f"Successful: {successful_captures}")
        print(f"Failed: {failed_captures}")
        print(f"Images saved to: {OUTPUT_DIR}")
        print()

        if failed_captures > 0:
            print(f"WARNING: {failed_captures} pages failed to capture.")
            print("  You may want to review and re-run for those specific pages.")

    except KeyboardInterrupt:
        print("\n\nWARNING: Interrupted by user")
        print(f"Captured {successful_captures} pages before interruption")
        print("You can resume by adjusting START_PAGE in the script")

    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\nKeeping browser open (don't close it yourself if needed)...")
        print("Script complete.")

if __name__ == "__main__":
    main()
