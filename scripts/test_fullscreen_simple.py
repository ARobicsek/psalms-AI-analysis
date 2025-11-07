"""
Simple test of full screen screenshot capture.

This is a standalone test script that doesn't require imports.

USAGE:
1. Make sure Chrome with remote debugging is running:
   "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:/temp/chrome_debug"

2. Navigate to: https://babel.hathitrust.org/cgi/pt?id=uc1.b4508670&seq=39

3. Run: python scripts/test_fullscreen_simple.py
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# Test configuration
BOOK_ID = "uc1.b4508670"
START_PAGE = 39
END_PAGE = 41  # Just 3 pages
OUTPUT_DIR = "data/hirsch_images_fullscreen_test"
CHROME_DEBUG_PORT = 9222

def main():
    print("="*70)
    print("Full Screen Screenshot Test")
    print("="*70)
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
            print(f"\nPage {page_num}:")
            print("-" * 40)

            # Navigate
            url = f"https://babel.hathitrust.org/cgi/pt?id={BOOK_ID};view=1up;seq={page_num}"
            driver.get(url)
            time.sleep(2)

            # Enter fullscreen AFTER navigation using JavaScript
            print("  Entering full screen mode via JavaScript...")
            try:
                # Use JavaScript to enter fullscreen mode
                driver.execute_script("""
                    var elem = document.documentElement;
                    if (elem.requestFullscreen) {
                        elem.requestFullscreen();
                    } else if (elem.webkitRequestFullscreen) {
                        elem.webkitRequestFullscreen();
                    } else if (elem.mozRequestFullScreen) {
                        elem.mozRequestFullScreen();
                    } else if (elem.msRequestFullscreen) {
                        elem.msRequestFullscreen();
                    }
                """)
                time.sleep(2)  # Wait for fullscreen transition
                print("  OK: Fullscreen requested via JavaScript")
            except Exception as e:
                print(f"  WARNING: Could not enter full screen: {e}")

            # Wait for page to load and render in full screen
            print("  Waiting for page to render...")
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
        print("Next steps:")
        print("  1. Compare images in data/hirsch_images/ (original)")
        print("     with data/hirsch_images_fullscreen_test/ (full screen)")
        print("  2. Check if full screen removed UI elements")
        print("  3. If better, we can use full screen for all 501 pages")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")

    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Exit full screen via JavaScript
        print("\nExiting full screen mode...")
        try:
            driver.execute_script("""
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                } else if (document.webkitExitFullscreen) {
                    document.webkitExitFullscreen();
                } else if (document.mozCancelFullScreen) {
                    document.mozCancelFullScreen();
                } else if (document.msExitFullscreen) {
                    document.msExitFullscreen();
                }
            """)
            time.sleep(0.5)
            print("OK: Exited full screen")
        except:
            pass

        print("Browser left open for inspection")

if __name__ == "__main__":
    main()
