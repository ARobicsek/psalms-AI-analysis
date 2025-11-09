# OCR Dependencies Installation Instructions

## Required for Hirsch Commentary Extraction

The OCR pipeline requires two components: Tesseract (OCR engine) and Poppler (PDF extraction).

---

## PART A: Tesseract OCR Installation

### Step 1: Download Tesseract Installer

Download the latest Tesseract OCR installer for Windows from:
https://github.com/UB-Mannheim/tesseract/wiki

**Recommended version**: tesseract-ocr-w64-setup-5.x.x.exe (64-bit)

### Step 2: Install Tesseract

1. Run the downloaded installer
2. **IMPORTANT**: During installation, select "Additional language data (download)"
3. Install to default location: `C:\Program Files\Tesseract-OCR\`
4. Add Tesseract to system PATH when prompted

### Step 3: Download German Fraktur Language Pack

If not included during installation:

1. Download `deu_frak.traineddata` from:
   https://github.com/tesseract-ocr/tessdata/raw/main/deu_frak.traineddata

2. Place the file in:
   `C:\Program Files\Tesseract-OCR\tessdata\`

### Step 4: Verify Tesseract Installation

Open a **new** command prompt and run:
```bash
tesseract --version
tesseract --list-langs
```

You should see `deu_frak` in the list of available languages.

**STATUS**: ✅ Tesseract v5.5.0 installed with deu_frak language pack

---

## PART B: Poppler Installation (Required for PDF Extraction)

### Option 1: Download Pre-built Binaries (Recommended)

1. Download the latest Windows poppler binaries from:
   https://github.com/oschwartz10612/poppler-windows/releases/

2. Download `Release-24.08.0-0.zip` (or latest version)

3. Extract the ZIP file to a permanent location, e.g.:
   `C:\Program Files\poppler\`

4. Add the `bin` folder to your system PATH:
   - Right-click "This PC" → Properties → Advanced system settings
   - Click "Environment Variables"
   - Under "System variables", find "Path" and click "Edit"
   - Click "New" and add: `C:\Program Files\poppler\Library\bin`
   - Click "OK" on all dialogs

5. **IMPORTANT**: Restart your terminal/IDE for PATH changes to take effect

### Option 2: Install via Package Manager

**Using Chocolatey**:
```bash
choco install poppler
```

**Using Scoop**:
```bash
scoop install poppler
```

### Verify Poppler Installation

Open a **new** command prompt and run:
```bash
pdftoppm -v
```

You should see version information for poppler.

---

## Installation Status Summary

### ✅ Completed
- Python libraries: pdf2image, pytesseract, opencv-python, Pillow, numpy
- Tesseract v5.5.0 with deu_frak language pack
- Tesseract path configured: `C:\Program Files\Tesseract-OCR\tesseract.exe`

### ⚠️ Required Next
- **Poppler** (for PDF to image conversion)

### 📝 Next Steps

Once Poppler is installed and in PATH:

1. **Restart your terminal/IDE** to load new PATH settings
2. **Verify installation**:
   ```bash
   pdftoppm -v
   ```
3. **Test OCR** on sample pages:
   ```bash
   python scripts/test_ocr_sample.py --pdf "Documents/Hirsch on Tehilim.pdf" --pages 36 37 --output data/hirsch_test/
   ```

---

## Troubleshooting

### Poppler not found
- Ensure you added the correct path to system PATH (should include `\Library\bin`)
- Restart terminal/IDE after changing PATH
- Verify with: `where pdftoppm` (should show full path)

### Alternative: Specify poppler path in code
If you prefer not to modify PATH, you can specify poppler location when running scripts:
```python
from pdf2image import convert_from_path
images = convert_from_path('file.pdf', poppler_path=r'C:\Program Files\poppler\Library\bin')
```
