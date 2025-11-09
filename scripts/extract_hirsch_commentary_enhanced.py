"""
Enhanced Hirsch Commentary OCR Extraction

This script:
1. Extracts Hebrew chapter number(s) from page header
2. Crops out UI elements (sidebar, navigation)
3. Finds the horizontal line separating verse from commentary
4. Extracts only the commentary text below the line
5. Detects verse markers (V. 19, VV. 1-3, etc.)
6. Runs OCR with English + Hebrew

Requirements: pip install opencv-python pillow pytesseract numpy
"""

import os
import re
import cv2
import numpy as np
from PIL import Image
import pytesseract
from pathlib import Path
import json

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# --- Configuration ---
INPUT_DIR = "data/hirsch_images"
OUTPUT_TEXT_DIR = "data/hirsch_commentary_text"
OUTPUT_METADATA_DIR = "data/hirsch_metadata"
OUTPUT_DEBUG_DIR = "data/hirsch_cropped"  # For debugging

# OCR settings
TESSERACT_CONFIG_MIXED = '-l eng+heb --psm 6 --oem 3'  # English + Hebrew, uniform block
TESSERACT_CONFIG_HEBREW = '-l heb --psm 6 --oem 3'     # Hebrew only, for headers

# Cropping parameters (based on 1920x1065 screenshots)
LEFT_CROP_PIXELS = 310      # Remove left sidebar
RIGHT_CROP_PIXELS = 120     # Remove right controls
TOP_CROP_PIXELS = 80        # Remove top navigation
BOTTOM_CROP_PIXELS = 80     # Remove bottom controls and page navigation

# Region detection
HEADER_HEIGHT = 150         # Height of header region to extract psalm number
MIN_LINE_LENGTH = 400       # Minimum length for horizontal line (pixels) - increased to avoid short header lines
LINE_SEARCH_HEIGHT = 500    # How far from top to search for the line - increased for pages with more verse text
# ---------------------

# Hebrew gematria mappings for psalm numbers
HEBREW_NUMERALS = {
    'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9,
    'י': 10, 'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90,
    'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400,
    # Final forms
    'ך': 20, 'ם': 40, 'ן': 50, 'ף': 80, 'ץ': 90
}

def parse_hebrew_numeral(hebrew_text):
    """
    Parse Hebrew numeral to integer.
    Examples: כ = 20, כג = 23, קמה = 145
    """
    total = 0
    for char in hebrew_text:
        if char in HEBREW_NUMERALS:
            total += HEBREW_NUMERALS[char]
    return total if total > 0 else None

def extract_psalm_numbers(header_text):
    """
    Extract psalm number(s) from Hebrew header text.
    Looks for patterns like:
    - "תהלים א" (Psalms 1)
    - "מזמור כ" (Psalm 20)
    - "מזמורים כ-כא" (Psalms 20-21)

    Returns: list of psalm numbers (can be 1 or 2)
    """
    psalm_numbers = []

    # Pattern 1: Look for תהלים (tehillim) followed by Hebrew numeral
    if 'תהלים' in header_text or 'תְּהִלִּים' in header_text:
        # Find position (try with and without nikud)
        idx = -1
        for variant in ['תהלים', 'תְּהִלִּים']:
            if variant in header_text:
                idx = header_text.find(variant)
                break

        if idx >= 0:
            # Get text after תהלים (next 10 chars)
            after_tehillim = header_text[idx+5:idx+15]

            # Extract Hebrew numerals
            current_num = ""
            for char in after_tehillim:
                if char in HEBREW_NUMERALS:
                    current_num += char
                elif char in [' ', '\n', '\t', 'ׇ', 'ְ', 'ֱ', 'ֲ', 'ֳ', 'ִ', 'ֵ', 'ֶ', 'ַ', 'ָ', 'ֹ', 'ֺ', 'ֻ', 'ּ', 'ֽ', '־']:
                    # Skip whitespace and nikud
                    continue
                elif current_num:
                    # End of number
                    break

            if current_num:
                num = parse_hebrew_numeral(current_num)
                if num and num <= 150:
                    psalm_numbers.append(num)

    # Pattern 2: Look for מזמור (mizmor) - alternative header format
    if not psalm_numbers and 'מזמור' in header_text:
        idx = header_text.find('מזמור')
        after_mizmor = header_text[idx+5:idx+15]

        current_num = ""
        for char in after_mizmor:
            if char in HEBREW_NUMERALS:
                current_num += char
            elif char in [' ', '\n', '\t', 'ְ', 'ִ', '־']:
                continue
            elif current_num:
                break

        if current_num:
            num = parse_hebrew_numeral(current_num)
            if num and num <= 150:
                psalm_numbers.append(num)

    return psalm_numbers if psalm_numbers else None

def extract_header_region(image_path):
    """
    Extract the header region containing psalm number.
    The Hebrew chapter number (e.g., תְּהִלִּים א) appears centered at the top.
    Returns: header image (numpy array)
    """
    img = cv2.imread(str(image_path))
    if img is None:
        return None

    height, width = img.shape[:2]

    # For header extraction, we want the CENTERED portion at the very top
    # Don't crop as much from the left to capture centered Hebrew text
    left = 200  # Less aggressive left crop to capture centered header
    right = width - 200  # Less aggressive right crop
    top = TOP_CROP_PIXELS  # Start after HathiTrust navigation

    # Extract just the header region (top 100 pixels of content)
    header = img[top:top+100, left:right]

    return header

def extract_chapter_info(image_path):
    """
    Extract Hebrew chapter number(s) from page header.
    Returns: {"psalm_numbers": [20] or [20, 21], "raw_hebrew": "מזמור כ"}
    """
    header = extract_header_region(image_path)
    if header is None:
        return None

    # Preprocess for Hebrew OCR
    gray = cv2.cvtColor(header, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # Convert to PIL Image
    pil_image = Image.fromarray(denoised)

    # Run Hebrew-only OCR on header
    hebrew_text = pytesseract.image_to_string(pil_image, config=TESSERACT_CONFIG_HEBREW).strip()

    # Parse psalm numbers
    psalm_numbers = extract_psalm_numbers(hebrew_text)

    return {
        "psalm_numbers": psalm_numbers,
        "raw_hebrew": hebrew_text
    }

def detect_horizontal_line(image):
    """
    Detect the horizontal line that separates verse from commentary.
    Returns the Y-coordinate of the line, or None if not found.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    search_region = gray[:LINE_SEARCH_HEIGHT, :]
    edges = cv2.Canny(search_region, 50, 150, apertureSize=3)

    lines = cv2.HoughLinesP(
        edges, rho=1, theta=np.pi/180, threshold=100,
        minLineLength=MIN_LINE_LENGTH, maxLineGap=20
    )

    if lines is None:
        return None

    # Find horizontal lines (y1 ≈ y2)
    horizontal_lines = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if abs(y2 - y1) < 5:  # Allow 5 pixel tolerance
            horizontal_lines.append((y1, x2 - x1))

    if not horizontal_lines:
        return None

    # Find the longest horizontal line (likely the separator)
    longest_line = max(horizontal_lines, key=lambda x: x[1])
    return longest_line[0]

def has_psalm_header(content_region, line_y):
    """
    Detect if there's a "PSALM" header far above the horizontal line.
    First pages of psalms have: PSALM header → verse text → line → commentary
    Continuation pages have: verse text → line → commentary

    Returns: True if PSALM header detected, False otherwise
    """
    if line_y < 200:
        # Not enough space above for PSALM header
        return False

    # Look for "PSALM" keyword in the upper/middle region
    # Based on debug: PSALM header appears around y=150-250 on page 33 (line_y=269)
    # This is roughly 200-50 pixels above the line
    # Check a larger region to be safe: 220-20 pixels above the line
    upper_region = content_region[max(0, line_y - 220):max(0, line_y - 20), :]

    if upper_region.shape[0] < 50:
        return False

    # Quick OCR to check for "PSALM" keyword
    try:
        gray = cv2.cvtColor(upper_region, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(
            Image.fromarray(gray),
            config='-l eng --psm 6'
        ).strip().upper()

        # Check if "PSALM" appears in the text
        has_psalm = 'PSALM' in text

        return has_psalm
    except:
        return False

def crop_to_commentary(image_path, debug=False):
    """
    Crop the image to show only the commentary region.
    Returns: cropped image (numpy array), or None if failed
    """
    img = cv2.imread(str(image_path))
    if img is None:
        print(f"    ERROR: Failed to read image: {image_path}")
        return None

    height, width = img.shape[:2]

    # Step 1: Remove UI elements
    left = LEFT_CROP_PIXELS
    right = width - RIGHT_CROP_PIXELS
    top = TOP_CROP_PIXELS
    bottom = height - BOTTOM_CROP_PIXELS

    content_region = img[top:bottom, left:right]

    # Step 2: Find the horizontal separator line
    line_y = detect_horizontal_line(content_region)

    if line_y is None:
        # Fallback: assume commentary starts at 1/4 of the page
        line_y = content_region.shape[0] // 4
        print(f"    INFO: Using fallback: assuming line at y={line_y}")
    else:
        print(f"    OK: Found separator line at y={line_y}")

    # Step 3: Detect if this is a PSALM header page
    has_header = has_psalm_header(content_region, line_y)

    if has_header:
        # Header page (e.g., "PSALM I") - capture header content
        margin = -180
        print(f"    INFO: PSALM header detected - using margin={margin}px")
    else:
        # Continuation page - use same margin as header pages to ensure we capture all commentary
        # Some pages (like page 56) need the full -180px even without PSALM headers
        margin = -180
        print(f"    INFO: Continuation page - using margin={margin}px")

    # Step 4: Crop to only the commentary (below the line with appropriate margin)
    commentary_region = content_region[max(0, line_y + margin):, :]

    if debug:
        debug_img = content_region.copy()
        cv2.line(debug_img, (0, line_y), (debug_img.shape[1], line_y), (0, 0, 255), 2)
        return commentary_region, debug_img

    return commentary_region, None

def is_loading_screen(image):
    """
    Detect if image is a loading screen (blank/grid pattern).
    Uses same logic as screenshot automation script.
    Returns: True if loading screen detected, False otherwise
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Calculate standard deviation and pixel range
    std_dev = np.std(gray)
    pixel_range = np.ptp(gray)  # max - min

    # Loading screens have very low variation
    # Grid pattern: std_dev < 20, pixel_range < 30
    is_loading = std_dev < 20 and pixel_range < 30

    return is_loading

def preprocess_for_ocr(image):
    """Preprocess the image to improve OCR accuracy."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    binary = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    return binary

def extract_text_from_commentary(image):
    """Run OCR on the commentary region."""
    processed = preprocess_for_ocr(image)
    pil_image = Image.fromarray(processed)
    text = pytesseract.image_to_string(pil_image, config=TESSERACT_CONFIG_MIXED)
    return text.strip()

def detect_verse_markers(text):
    """
    Detect verse markers in the commentary text.
    Returns: list of {"verse": "19", "position": 123} or {"verse": "1-3", "position": 456}
    """
    # Patterns: V. 19, VV. 1-3, V.19, VV.1-3
    pattern = r'\bVV?\.\s*(\d+(?:-\d+)?)\b'

    markers = []
    for match in re.finditer(pattern, text):
        markers.append({
            "verse": match.group(1),
            "position": match.start(),
            "marker": match.group(0)
        })

    return markers

def process_single_page(image_path, text_dir, metadata_dir, debug_dir=None):
    """
    Process a single page: extract metadata, crop, OCR, save.
    Returns: True if successful, False if failed/loading screen
    """
    page_name = Path(image_path).stem
    print(f"\nProcessing {page_name}...")

    # Step 0: Check if this is a loading screen
    img = cv2.imread(str(image_path))
    if img is None:
        print(f"    ERROR: Failed to read image")
        return False

    if is_loading_screen(img):
        print(f"    WARNING: LOADING SCREEN DETECTED - Skipping (needs recapture)")
        # Save metadata marking this as a loading screen
        metadata = {
            "page": page_name,
            "status": "LOADING_SCREEN",
            "error": "Loading screen detected - needs recapture",
            "chapter_info": None,
            "verse_markers": [],
            "text_length": 0
        }
        metadata_path = os.path.join(metadata_dir, f"{page_name}_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        return False

    # Step 1: Extract chapter information from header
    print(f"  Extracting header info...")
    chapter_info = extract_chapter_info(image_path)

    if chapter_info and chapter_info['psalm_numbers']:
        print(f"    Found Psalm(s): {chapter_info['psalm_numbers']}")
    else:
        print(f"    WARNING: Could not detect psalm number")

    # Step 2: Crop to commentary region
    result = crop_to_commentary(image_path, debug=debug_dir is not None)

    if result is None:
        return False

    if debug_dir:
        commentary_region, debug_img = result
        debug_path = os.path.join(debug_dir, f"{page_name}_debug.png")
        cv2.imwrite(debug_path, debug_img)
    else:
        commentary_region = result[0]

    if commentary_region is None or commentary_region.size == 0:
        print(f"    ERROR: Failed to extract commentary region")
        return False

    # Save cropped image (for inspection)
    if debug_dir:
        cropped_path = os.path.join(debug_dir, f"{page_name}_cropped.png")
        cv2.imwrite(cropped_path, commentary_region)

    # Step 3: Run OCR
    print(f"    Running OCR...")
    text = extract_text_from_commentary(commentary_region)

    if not text:
        print(f"    WARNING: No text extracted")
        return False

    # Step 4: Detect verse markers
    verse_markers = detect_verse_markers(text)

    if verse_markers:
        print(f"    Found {len(verse_markers)} verse marker(s): {', '.join(m['marker'] for m in verse_markers[:5])}")

    # Step 5: Save text
    text_path = os.path.join(text_dir, f"{page_name}.txt")
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(text)

    # Step 6: Save metadata
    metadata = {
        "page": page_name,
        "status": "SUCCESS",
        "chapter_info": chapter_info,
        "verse_markers": verse_markers,
        "text_length": len(text),
        "text_file": f"{page_name}.txt"
    }

    metadata_path = os.path.join(metadata_dir, f"{page_name}_metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # Show preview
    print(f"    OK: Extracted {len(text)} characters")

    return True

def main():
    """Main function to process all pages."""
    print("="*70)
    print("Enhanced Hirsch Commentary OCR Extraction")
    print("="*70)
    print()

    # Create output directories
    os.makedirs(OUTPUT_TEXT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_METADATA_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DEBUG_DIR, exist_ok=True)

    # Get all PNG files
    image_files = sorted(Path(INPUT_DIR).glob("page_*.png"))

    if not image_files:
        print(f"ERROR: No PNG files found in {INPUT_DIR}")
        return

    print(f"Found {len(image_files)} page images")
    print(f"Output text: {OUTPUT_TEXT_DIR}")
    print(f"Output metadata: {OUTPUT_METADATA_DIR}")
    print(f"Debug images: {OUTPUT_DEBUG_DIR}")
    print()

    # Process each page
    successful = 0
    failed = 0

    for image_path in image_files:
        try:
            success = process_single_page(
                str(image_path),
                OUTPUT_TEXT_DIR,
                OUTPUT_METADATA_DIR,
                debug_dir=OUTPUT_DEBUG_DIR
            )

            if success:
                successful += 1
            else:
                failed += 1

        except Exception as e:
            print(f"    ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print()
    print("="*70)
    print("OCR Extraction Complete")
    print("="*70)
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Text files: {OUTPUT_TEXT_DIR}")
    print(f"Metadata files: {OUTPUT_METADATA_DIR}")
    print(f"Debug images: {OUTPUT_DEBUG_DIR}")
    print()

    # Check for loading screens
    loading_screens = []
    for metadata_file in Path(OUTPUT_METADATA_DIR).glob("*_metadata.json"):
        with open(metadata_file, encoding='utf-8') as f:
            meta = json.load(f)
            if meta.get('status') == 'LOADING_SCREEN':
                loading_screens.append(meta['page'])

    if loading_screens:
        print("="*70)
        print(f"WARNING: {len(loading_screens)} pages need recapture (loading screens)")
        print("="*70)
        print(f"Pages to recapture: {', '.join(sorted(loading_screens))}")
        print()

        # Save list to file
        with open(os.path.join(OUTPUT_METADATA_DIR, "loading_screens.txt"), 'w') as f:
            f.write('\n'.join(sorted(loading_screens)))
        print(f"List saved to: {OUTPUT_METADATA_DIR}/loading_screens.txt")
        print()

if __name__ == "__main__":
    main()
