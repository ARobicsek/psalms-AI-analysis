# Hirsch Commentary Screenshot Automation Guide

This guide shows how to automate screenshot capture from HathiTrust after you've opened the page manually.

## Recommended: Selenium with Existing Browser (Full Automation)

This connects to your manually-opened browser and runs fully automated.

### Step 1: Install Requirements

```bash
pip install selenium
```

### Step 2: Open Chrome with Remote Debugging

**On Windows:**
```bash
# Close any existing Chrome windows first!
# Then run:
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:/temp/chrome_debug"
```

**On Mac:**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome_debug"
```

**On Linux:**
```bash
google-chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome_debug"
```

### Step 3: Navigate to First Page Manually

In the Chrome window that opened, go to:
```
https://babel.hathitrust.org/cgi/pt?id=uc1.b4508670&seq=33
```

This will pass Cloudflare's human verification.

### Step 4: Run the Automation Script

```bash
cd "C:\Users\ariro\OneDrive\Documents\Psalms"
python scripts/hirsch_screenshot_automation.py
```

The script will:
- Connect to your open browser
- Navigate through pages 33-533 (or whatever range you configure)
- Take a screenshot of each page
- Save as PNG files: `page_0033.png`, `page_0034.png`, etc.
- Estimated time: ~15-20 minutes for all 501 pages

### Step 5: Let It Run

You can minimize the browser but **don't close it!** The script will automatically:
- Navigate to each page
- Wait for it to load
- Capture screenshot
- Move to next page

When done, you'll have all images in `data/hirsch_images/`

## Configuration Options

Edit `scripts/hirsch_screenshot_automation.py`:

```python
# Test with small range first:
START_PAGE = 33
END_PAGE = 35  # Just 3 pages

# Then do full extraction:
START_PAGE = 33
END_PAGE = 533  # All 501 pages

# Adjust delay if needed:
PAGE_DELAY_SECONDS = 2  # Increase if pages load slowly
```

## Troubleshooting

### "Failed to connect to browser"
- Make sure Chrome is running with `--remote-debugging-port=9222`
- Check that no other Chrome instances are running
- Verify the port isn't being used by another program

### Screenshots are blank or incomplete
- Increase `PAGE_DELAY_SECONDS` to 3 or 4
- Check your internet connection
- HathiTrust might be slow - add more wait time

### Script stops midway
- Note which page it stopped at
- Change `START_PAGE` to resume from that page
- Re-run the script

### Cloudflare blocks after starting
- This shouldn't happen since you manually authenticated
- If it does, restart with a fresh manual navigation
- Try increasing delays between pages

## Alternative: Browser Console Method (Semi-Manual)

If Selenium doesn't work, use the browser console method:

### Step 1: Navigate to First Page

Open in browser:
```
https://babel.hathitrust.org/cgi/pt?id=uc1.b4508670&seq=33
```

### Step 2: Open Developer Console

Press `F12` or `Ctrl+Shift+I`

### Step 3: Paste JavaScript

Open: `scripts/hirsch_browser_console_script.js`

Copy entire contents and paste into Console tab, press Enter.

### Step 4: Repeat

The script captures one page at a time. After each page downloads, navigate to the next page and repeat.

**Pros:** Works in any browser
**Cons:** Must manually run script for each page (too tedious for 501 pages)

## After Screenshot Capture

Once you have the images:

### Step 1: Run OCR

```bash
python scripts/extract_hirsch_pdf.py --source data/hirsch_images/
```

### Step 2: Review Quality

Check a few OCR outputs:
```bash
# View OCR text for page 33
cat data/hirsch_test/page_0033_text.txt
```

### Step 3: Parse Commentary

```bash
python scripts/generate_hirsch_json.py
```

This will create `data/hirsch_on_psalms.json` with structured commentary.

### Step 4: Integrate

The `HirschLibrarian` class (already implemented in Session 70) will automatically load the JSON and include Hirsch commentary in psalm commentaries.

## Time Estimates

- **Setup (first time):** 10 minutes
- **Chrome debugging start:** 1 minute
- **Manual navigation:** 1 minute
- **Automated screenshot capture:** 15-20 minutes (501 pages)
- **OCR processing:** 30-45 minutes
- **Parsing and JSON generation:** 5 minutes
- **Total:** ~1 hour of mostly automated work

## Legal/Ethical Notes

This approach:
- ✅ Respects Cloudflare's bot detection (you authenticate manually)
- ✅ Respects HathiTrust's bulk download restrictions (rate-limited, one session)
- ✅ Falls under "text transcribed from images" permitted use
- ✅ Educational/research purpose clearly stated

HathiTrust policy explicitly permits: "no restrictions on use of text transcribed from the images" for educational and scholarly purposes.

---

**Ready to start?** Begin with the Selenium method and test with just 3 pages first (START_PAGE=33, END_PAGE=35) to verify it works before running the full 501-page extraction.
