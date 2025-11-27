# Manual Download Guide for Hirsch Commentary

Since HathiTrust blocks automated downloads with Cloudflare protection, here's an efficient manual workflow.

## Quick Manual Download Method

### Option 1: Use Browser Developer Tools (FASTEST)

1. **Open first page in browser:**
   ```
   https://babel.hathitrust.org/cgi/pt?id=uc1.b4508670&seq=33
   ```

2. **Open Developer Tools:**
   - Press `F12` or `Ctrl+Shift+I`
   - Go to "Network" tab
   - Look for image requests (filter by "Img")

3. **Find the image URL pattern:**
   - Refresh the page
   - Look for requests to `/cgi/imgsrv/image?`
   - Right-click → "Copy" → "Copy URL"

4. **Extract image URL:**
   - You should see something like:
   ```
   https://babel.hathitrust.org/cgi/imgsrv/image?id=uc1.b4508670;seq=33;width=1000
   ```

5. **Open image in new tab:**
   - Right-click image → "Open Image in New Tab"
   - Save with `Ctrl+S`

6. **Automate with browser bookmark:**
   - Create a bookmarklet to save images quickly
   - Or use browser extension like "Tab Save" or "Download All Images"

### Option 2: Screenshot Method (SIMPLER)

1. **Navigate to page:**
   ```
   https://babel.hathitrust.org/cgi/pt?id=uc1.b4508670&seq=33
   ```

2. **Zoom to fit:**
   - Use HathiTrust's zoom controls to fit page to window
   - Or press `Ctrl+0` to reset zoom

3. **Screenshot:**
   - Windows: `Win+Shift+S` (Snipping Tool)
   - Or use full-page screenshot extension (e.g., "GoFullPage")

4. **Save numbered:**
   - Save as `page_0033.png`, `page_0034.png`, etc.

### Option 3: Download Button (IF AVAILABLE)

1. Look for download button on HathiTrust page
2. Some public domain books allow page-by-page download
3. Check if you're logged in (UC institutional access may help)

## Batch Processing

Once you have ~10 sample pages, we can:

1. **Test OCR quality:**
   ```bash
   python scripts/extract_hirsch_pdf.py --test-pages data/hirsch_images/
   ```

2. **Assess if it's worth continuing:**
   - If OCR quality is good → continue manual download
   - If OCR quality is poor → try different approach

## Time Estimate

- **3 pages (test):** 5 minutes
- **50 pages (Psalm 1-10):** ~1 hour
- **501 pages (all):** ~8-10 hours spread over time

## Alternative: Request Just Psalm Pages

Instead of downloading all 501 pages, we could:

1. Identify which pages contain which Psalms
2. Download only the ~150 pages we actually need
3. Reduces effort by 70%

## Next Steps After Download

1. Save images to `data/hirsch_images/`
2. Run OCR with our existing Tesseract pipeline
3. Parse with Hirsch parser
4. Integrate into commentary generation

---

**NOTE:** This approach respects HathiTrust's intent (preventing bulk automated downloads) while allowing legitimate research access that's explicitly permitted by their policy: "no restrictions on use of text transcribed from the images."
