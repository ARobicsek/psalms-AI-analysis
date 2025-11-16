"""
Test HathiTrust's built-in zoom to get higher resolution page images.

This script uses HathiTrust's zoom controls to magnify the page image.

USAGE:
1. Make sure Chrome with remote debugging is running:
   "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:/temp/chrome_debug"

2. Navigate to: https://babel.hathitrust.org/cgi/pt?id=uc1.b4508670&seq=39

3. Run: python scripts/test_hathitrust_zoom.py
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

# Test configuration
BOOK_ID = "uc1.b4508670"
START_PAGE = 39
END_PAGE = 41  # Just 3 pages
OUTPUT_DIR = "data/hirsch_images_zoom_test"
CHROME_DEBUG_PORT = 9222

# HathiTrust zoom settings
ZOOM_CLICKS = 1  # Number of times to click zoom in button (start conservative: 1-2)

def zoom_in_hathitrust(driver, zoom_clicks):
    """
    Zoom in using HathiTrust's zoom controls.

    Tries multiple methods:
    1. Find and click the zoom in button
    2. Use keyboard shortcuts
    """
    print(f"  Zooming in {zoom_clicks} times...")

    try:
        # Store current URL to verify we don't navigate away
        current_url = driver.current_url

        # Method 1: Try to find zoom in button by various selectors
        zoom_selectors = [
            "button[aria-label*='Zoom in']",
            "button[title*='Zoom in']",
            "button[aria-label*='zoom in']",
            "button[title*='zoom in']",
            ".zoom-in",
            "#zoom-in",
            "button.zoom-in-btn",
        ]

        for selector in zoom_selectors:
            try:
                zoom_button = driver.find_element(By.CSS_SELECTOR, selector)
                for i in range(zoom_clicks):
                    zoom_button.click()
                    time.sleep(1.0)  # Longer delay to let zoom settle

                    # Verify we didn't navigate away
                    if driver.current_url != current_url:
                        print(f"  WARNING: Page changed after zoom click!")
                        driver.get(current_url)
                        time.sleep(2)

                print(f"  OK: Zoomed in using button (selector: {selector})")
                return True
            except:
                continue

        # Method 2: Try keyboard shortcut (+ key often zooms in)
        try:
            actions = ActionChains(driver)
            for i in range(zoom_clicks):
                actions.send_keys('+').perform()
                time.sleep(0.5)
            print(f"  OK: Zoomed in using '+' key")
            return True
        except:
            pass

        # Method 3: Try clicking on image first, then + key
        try:
            img_element = driver.find_element(By.TAG_NAME, "img")
            img_element.click()
            time.sleep(0.3)
            actions = ActionChains(driver)
            for i in range(zoom_clicks):
                actions.send_keys('+').perform()
                time.sleep(0.5)
            print(f"  OK: Zoomed in using '+' key after clicking image")
            return True
        except:
            pass

        print(f"  WARNING: Could not find zoom control")
        return False

    except Exception as e:
        print(f"  WARNING: Error zooming: {e}")
        return False

def zoom_out_hathitrust(driver, zoom_clicks):
    """
    Zoom out to reset for next page.
    """
    try:
        # Try zoom out button
        zoom_selectors = [
            "button[aria-label*='zoom out']",
            "button[title*='zoom out']",
            "button[aria-label*='Zoom out']",
            ".zoom-out",
        ]

        for selector in zoom_selectors:
            try:
                zoom_button = driver.find_element(By.CSS_SELECTOR, selector)
                for i in range(zoom_clicks):
                    zoom_button.click()
                    time.sleep(0.3)
                return True
            except:
                continue

        # Try - key
        actions = ActionChains(driver)
        for i in range(zoom_clicks):
            actions.send_keys('-').perform()
            time.sleep(0.3)
        return True

    except:
        return False

def main():
    print("="*70)
    print("HathiTrust Zoom Test")
    print("="*70)
    print()
    print(f"Settings:")
    print(f"  Zoom clicks: {ZOOM_CLICKS}")
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
        for page_num in range(START_PAGE, END_PAGE + 1):
            print(f"Page {page_num}:")
            print("-" * 40)

            # Navigate
            url = f"https://babel.hathitrust.org/cgi/pt?id={BOOK_ID};view=1up;seq={page_num}"
            driver.get(url)

            # Wait for page to load
            print("  Waiting for page to load...")
            time.sleep(3)

            # Zoom in using HathiTrust controls
            zoom_in_hathitrust(driver, ZOOM_CLICKS)

            # Wait for zoom to render
            time.sleep(2)

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
        print(f"Images captured with {ZOOM_CLICKS}x zoom")
        print()
        print("Next steps:")
        print(f"  1. Compare with original images in data/hirsch_images/")
        print(f"  2. Check if text is larger and clearer")
        print(f"  3. Test OCR on zoomed version")
        print(f"  4. If better, adjust ZOOM_CLICKS and update main script")

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
