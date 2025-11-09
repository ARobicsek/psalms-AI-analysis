r"""
Automated screenshot capture from HathiTrust using full screen mode.

USAGE:
1. Open Chrome with remote debugging:
   "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:/temp/chrome_debug"

2. Navigate to first page manually in that Chrome window:
   https://babel.hathitrust.org/cgi/pt?id=uc1.b4508670&seq=33

3. Run this script:
   python scripts/hirsch_screenshot_automation_fullscreen.py

The script will:
- Enter full screen mode (removes ALL UI elements)
- Detect and skip loading screens
- Capture screenshots automatically
- Navigate through all pages

Requirements: pip install selenium webdriver-manager
"""

import os
import time
from pathlib import Path
import numpy as np

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
except ImportError:
    print("ERROR: Selenium is not installed.")
    print("Install with: pip install selenium")
    exit(1)

try:
    from PIL import Image
    import io
except ImportError:
    print("ERROR: Pillow is not installed.")
    print("Install with: pip install pillow")
    exit(1)

# --- Configuration ---
BOOK_ID = "uc1.b4508670"
START_PAGE = 33
END_PAGE = 533  # All 501 pages
OUTPUT_DIR = "data/hirsch_images"
PAGE_DELAY_SECONDS = 3  # Delay between pages
CHROME_DEBUG_PORT = 9222

# For testing, use smaller range:
# END_PAGE = 40  # Just 8 pages for testing
# ---------------------

def connect_to_existing_browser(debug_port=9222):
    """
    Connect to an existing Chrome browser opened with remote debugging.
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
        print('  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:/temp/chrome_debug"')
        print("\nThen navigate to the first HathiTrust page manually.")
        return None

def enter_fullscreen_mode(driver):
    """
    Enter full screen mode to remove all UI elements.
    """
    try:
        print("  Entering full screen mode...")

        # Try multiple methods to enter full screen

        # Method 1: Look for full screen button
        try:
            fullscreen_button = driver.find_element(By.CSS_SELECTOR, "button[title*='fullscreen'], button[title*='Fullscreen'], button[aria-label*='fullscreen']")
            fullscreen_button.click()
            time.sleep(1)
            print("  OK: Entered full screen via button")
            return True
        except:
            pass

        # Method 2: Press F key (HathiTrust shortcut)
        try:
            actions = ActionChains(driver)
            actions.send_keys('f').perform()
            time.sleep(1)
            print("  OK: Entered full screen via 'F' key")
            return True
        except:
            pass

        # Method 3: Press F11 (browser full screen)
        try:
            actions = ActionChains(driver)
            actions.send_keys(Keys.F11).perform()
            time.sleep(1)
            print("  OK: Entered full screen via F11")
            return True
        except:
            pass

        print("  WARNING: Could not enter full screen mode")
        return False

    except Exception as e:
        print(f"  WARNING: Error entering full screen: {e}")
        return False

def exit_fullscreen_mode(driver):
    """
    Exit full screen mode.
    """
    try:
        # Press Escape to exit full screen
        actions = ActionChains(driver)
        actions.send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5)
    except:
        pass

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

        # Check if image is mostly uniform (loading screens are typically
        # blank or have repetitive patterns)

        # Calculate standard deviation of pixel values
        # Low std dev = uniform/blank image = likely loading
        std_dev = np.std(img_array)

        # Threshold: if std dev is very low, it's likely a loading screen
        if std_dev < 20:  # Adjust threshold as needed
            return True

        # Additional check: look for Google watermark pattern
        # (loading screens often show just the watermark)
        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = np.mean(img_array, axis=2)
        else:
            gray = img_array

        # Check if most pixels are similar (within 10% of each other)
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
    print("  Waiting for page to load...")

    for attempt in range(max_wait):
        time.sleep(1)

        # Take a quick screenshot to check
        screenshot_bytes = driver.get_screenshot_as_png()

        if not is_loading_screen(screenshot_bytes):
            print(f"  OK: Page loaded (waited {attempt + 1}s)")
            return True

        print(f"  Still loading... ({attempt + 1}/{max_wait})")

    print(f"  WARNING: Page still loading after {max_wait}s, proceeding anyway")
    return False

def capture_page_screenshot(driver, page_num, output_dir):
    """Capture screenshot of current page."""
    try:
        # Wait for page content to load
        wait_for_page_load(driver, max_wait=10)

        # Additional wait for any animations
        time.sleep(1)

        # Take screenshot
        screenshot_bytes = driver.get_screenshot_as_png()

        # Final check: make sure it's not a loading screen
        if is_loading_screen(screenshot_bytes):
            print(f"    WARNING: Still showing loading screen, skipping page {page_num}")
            return False

        # Save screenshot
        screenshot_path = os.path.join(output_dir, f"page_{page_num:04d}.png")
        with open(screenshot_path, 'wb') as f:
            f.write(screenshot_bytes)

        # Get file size for verification
        file_size = os.path.getsize(screenshot_path)
        print(f"    OK: Saved page_{page_num:04d}.png ({file_size:,} bytes)")

        return True

    except Exception as e:
        print(f"    ERROR: Error capturing page {page_num}: {e}")
        return False

def navigate_to_page(driver, book_id, page_num):
    """Navigate to a specific page."""
    url = f"https://babel.hathitrust.org/cgi/pt?id={book_id};view=1up;seq={page_num}"
    driver.get(url)

    # Short wait for navigation
    time.sleep(1)

def main():
    """
    Main function to automate screenshot capture.
    """
    print("="*70)
    print("HathiTrust Screenshot Automation Tool (Full Screen Mode)")
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
    estimated_minutes = (total_pages * (PAGE_DELAY_SECONDS + 2)) / 60
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
    print(f"The browser will enter full screen mode automatically.")
    print()

    successful_captures = 0
    failed_captures = 0
    in_fullscreen = False

    try:
        for page_num in range(START_PAGE, END_PAGE + 1):
            # Progress indicator
            progress = page_num - START_PAGE + 1
            print(f"[{progress}/{total_pages}] Page {page_num}...")

            # Navigate to page
            navigate_to_page(driver, BOOK_ID, page_num)

            # Enter full screen on first page
            if not in_fullscreen:
                in_fullscreen = enter_fullscreen_mode(driver)

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
        print("\n\nInterrupted by user")
        print(f"Captured {successful_captures} pages before interruption")
        print("You can resume by adjusting START_PAGE in the script")

    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Exit full screen
        if in_fullscreen:
            print("\nExiting full screen mode...")
            exit_fullscreen_mode(driver)

        print("Keeping browser open...")
        print("Script complete.")

if __name__ == "__main__":
    main()
