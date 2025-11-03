
import json
import re

INPUT_OUTPUT_JSON_PATH = "sacks_on_psalms.json"

# --- Gematria Conversion ---
GEMATRIA_MAP = {
    1: 'א', 2: 'ב', 3: 'ג', 4: 'ד', 5: 'ה', 6: 'ו', 7: 'ז', 8: 'ח', 9: 'ט',
    10: 'י', 20: 'כ', 30: 'ל', 40: 'מ', 50: 'נ', 60: 'ס', 70: 'ע', 80: 'פ', 90: 'צ',
    100: 'ק', 200: 'ר', 300: 'ש', 400: 'ת'
}

def to_hebrew_numeral(num: int) -> str:
    """Converts an integer to a Hebrew numeral string using Gematria."""
    if not 1 <= num <= 999:
        return str(num) # Return as string if out of typical range

    # Special cases for 15 and 16
    if num == 15: return 'טו'
    if num == 16: return 'טז'

    hebrew_num = ''
    remaining = num

    for val in sorted(GEMATRIA_MAP.keys(), reverse=True):
        if remaining >= val:
            count = remaining // val
            hebrew_num += GEMATRIA_MAP[val] * count
            remaining %= val
    
    # Add gershayim for multi-letter numerals
    if len(hebrew_num) > 1:
        hebrew_num = hebrew_num[:-1] + '"' + hebrew_num[-1]
    # Add geresh for single-letter numerals
    elif len(hebrew_num) == 1:
        hebrew_num += "'"

    return hebrew_num

# --- Bilingual Snippet Extraction Logic ---
def extract_context_snippet(en_text: list, he_text: list, source_ref: str) -> str:
    """Tries to find a snippet in English text first, then falls back to Hebrew."""
    if not source_ref:
        return ""

    parts = source_ref.split('.')
    if len(parts) != 3:
        return ""
    
    book, chapter_num, verse_num = parts[0], int(parts[1]), int(parts[2])

    # 1. Try English
    if en_text:
        full_text_en = " ".join([re.sub(r'<[^>]+>', '', p) for p in en_text])
        full_text_en = " ".join(full_text_en.split())
        
        base_formats_en = [
            f"{book} {chapter_num}:{verse_num}",
            f"{book} {chapter_num}, {verse_num}",
            f"Ps. {chapter_num}:{verse_num}",
            f"Psalm {chapter_num}:{verse_num}",
        ]
        possible_markers_en = []
        for fmt in base_formats_en:
            possible_markers_en.append(fmt)
            possible_markers_en.append(f"({fmt})")

        for marker in possible_markers_en:
            pos = full_text_en.find(marker)
            if pos != -1:
                start = max(0, pos - 1000)
                end = min(len(full_text_en), pos + len(marker) + 1000)
                prefix = "..." if start > 0 else ""
                suffix = "..." if end < len(full_text_en) else ""
                return f"{prefix}{full_text_en[start:end]}{suffix}"

    # 2. Try Hebrew if English fails or is empty
    if he_text:
        full_text_he = " ".join([re.sub(r'<[^>]+>', '', p) for p in he_text])
        full_text_he = " ".join(full_text_he.split())

        he_book = "תהלים"
        he_chapter = to_hebrew_numeral(chapter_num)
        he_verse = to_hebrew_numeral(verse_num)

        base_formats_he = [
            f"{he_book} {he_chapter}, {he_verse}", # תהלים כ"ג, א'
            f"{he_book} {he_chapter} {he_verse}",
        ]
        possible_markers_he = []
        for fmt in base_formats_he:
            possible_markers_he.append(fmt)
            possible_markers_he.append(f"({fmt})")

        for marker in possible_markers_he:
            pos = full_text_he.find(marker)
            if pos != -1:
                start = max(0, pos - 1000)
                end = min(len(full_text_he), pos + len(marker) + 1000)
                prefix = "..." if start > 0 else ""
                suffix = "..." if end < len(full_text_he) else ""
                return f"{prefix}{full_text_he[start:end]}{suffix}"

    return "" # Return empty if nothing found

# --- Main Reprocessing Logic ---
def reprocess_file_final():
    print(f"Reading data from {INPUT_OUTPUT_JSON_PATH}...")
    try:
        with open(INPUT_OUTPUT_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error reading file: {e}")
        return

    print(f"Found {len(data)} entries to reprocess.")
    processed_count = 0
    snippet_added_count = 0

    for entry in data:
        source_ref = entry.get('source_psalm_ref')
        en_text = entry.get('text', [])
        he_text = entry.get('he', [])

        snippet = extract_context_snippet(en_text, he_text, source_ref)
        if snippet:
            # Only count as added if it wasn't already populated
            if not entry.get('context_snippet'): 
                snippet_added_count += 1
            entry['context_snippet'] = snippet
        
        processed_count += 1
        print(f"\rProcessed {processed_count}/{len(data)}... Total snippets: {snippet_added_count}", end="")

    # Recalculate total snippets at the end
    final_snippet_count = sum(1 for e in data if e.get('context_snippet'))

    print(f"\n\nFinished reprocessing. Total entries with snippets: {final_snippet_count}/{len(data)}.")
    print(f"Saving updated data back to {INPUT_OUTPUT_JSON_PATH}...")
    try:
        with open(INPUT_OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Successfully saved updated file.")
    except IOError as e:
        print(f"Error writing to file: {e}")

if __name__ == "__main__":
    reprocess_file_final()
