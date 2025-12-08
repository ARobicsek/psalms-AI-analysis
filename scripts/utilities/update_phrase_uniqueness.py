import sqlite3
import json
import re
import sys
from collections import defaultdict

try:
    import ahocorasick
except ImportError:
    print("Error: pyahocorasick library not found.")
    print("Please install it by running: pip install pyahocorasick")
    sys.exit(1)

LITURGY_DB_PATH = 'c:\\Users\\ariro\\OneDrive\\Documents\\Psalms\\data\\liturgy.db'
TANAKH_DB_PATH = 'c:\\Users\\ariro\\OneDrive\\Documents\\Psalms\\database\\tanakh.db'
LITURGY_TABLE_NAME = 'psalms_liturgy_index'
TANAKH_TABLE_NAME = 'verses'

def normalize_hebrew_text(text):
    """Normalizes Hebrew text by removing nikkud, ta'amim, and punctuation."""
    if not text:
        return ""
    # Remove nikkud, ta'amim, and other marks (Unicode range U+0590 to U+05C7)
    text = re.sub(r'[\u0590-\u05C7]', '', text)
    # Remove specific punctuation like sof pasuk, maqaf
    text = re.sub(r'[׃־]', '', text)
    # Optional: standardize spacing around shem Hashem or other elements if needed
    # For now, just collapse multiple spaces into one
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def add_columns_to_db(cursor):
    """Adds is_unique and locations columns to the specified table if they don't exist."""
    try:
        cursor.execute(f"ALTER TABLE {LITURGY_TABLE_NAME} ADD COLUMN is_unique BOOLEAN")
        print(f"Added 'is_unique' column to '{LITURGY_TABLE_NAME}' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("'is_unique' column already exists.")
        else:
            raise e
            
    try:
        cursor.execute(f"ALTER TABLE {LITURGY_TABLE_NAME} ADD COLUMN locations TEXT")
        print(f"Added 'locations' column to '{LITURGY_TABLE_NAME}' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("'locations' column already exists.")
        else:
            raise e

def get_phrases_from_liturgy(cursor):
    """Fetches phrases to be checked from the liturgy database."""
    query = f"""
        SELECT rowid, psalm_phrase_normalized, psalm_chapter 
        FROM {LITURGY_TABLE_NAME} 
        WHERE match_type = 'phrase_match' AND psalm_phrase_normalized IS NOT NULL AND psalm_phrase_normalized != ''
    """
    cursor.execute(query)
    return cursor.fetchall()

def build_automaton(phrases):
    """Builds an Aho-Corasick automaton from a list of phrases."""
    A = ahocorasick.Automaton()
    for _, phrase, _ in phrases:
        if phrase:
            # Ensure the phrase added to the automaton is also normalized in the same way
            normalized_phrase = normalize_hebrew_text(phrase)
            if normalized_phrase:
                A.add_word(normalized_phrase, normalized_phrase)
    A.make_automaton()
    return A

def main():
    """Main function to update phrase uniqueness in the liturgy database."""
    print("Starting phrase uniqueness update process.")

    liturgy_conn = sqlite3.connect(LITURGY_DB_PATH)
    liturgy_cursor = liturgy_conn.cursor()

    print(f"Step 1: Verifying and adding columns to {LITURGY_DB_PATH}...")
    add_columns_to_db(liturgy_cursor)
    liturgy_conn.commit()

    print("\nStep 2: Fetching phrases from liturgy database...")
    phrases_to_check = get_phrases_from_liturgy(liturgy_cursor)
    
    if not phrases_to_check:
        print("No phrases with match_type='phrase_match' found to check. Exiting.")
        liturgy_conn.close()
        return

    print(f"Found {len(phrases_to_check)} total phrase records to process.")
    
    # We use the already normalized phrases from the liturgy db for the search
    unique_phrases_for_search = list(set(p[1] for p in phrases_to_check if p[1]))
    print(f"Found {len(unique_phrases_for_search)} unique phrases to search for in the Tanakh.")

    print("\nStep 3: Building search automaton...")
    A = ahocorasick.Automaton()
    for phrase in unique_phrases_for_search:
        A.add_word(phrase, phrase)
    A.make_automaton()

    print("\nStep 4: Searching Tanakh for phrase occurrences...")
    phrase_locations = defaultdict(list)
    tanakh_conn = sqlite3.connect(TANAKH_DB_PATH)
    tanakh_cursor = tanakh_conn.cursor()
    # Fetching the raw hebrew text to normalize it ourselves
    tanakh_cursor.execute(f"SELECT book_name, chapter, verse, hebrew FROM {TANAKH_TABLE_NAME}")
    
    # Use fetchall to get a determinate row count
    all_verses = tanakh_cursor.fetchall()
    total_verses = len(all_verses)
    count = 0
    print(f"Processing {total_verses} verses from Tanakh...")
    for book_name, chapter, verse, hebrew_text in all_verses:
        count += 1
        if count % 1000 == 0:
            sys.stdout.write(f"  Processed {count}/{total_verses} verses...\r")
            sys.stdout.flush()
        
        if not hebrew_text:
            continue
        
        normalized_tanakh_text = normalize_hebrew_text(hebrew_text)
        
        for _, found_phrase in A.iter(normalized_tanakh_text):
            phrase_locations[found_phrase].append({'book': book_name, 'chapter': chapter, 'verse': verse})
    print(f"  Processed {total_verses}/{total_verses} verses... Done.")
    
    tanakh_conn.close()

    print("\nStep 5: Analyzing results and updating liturgy database...")
    
    total_updates = len(phrases_to_check)
    update_count = 0
    print(f"Updating {total_updates} records in the liturgy database...")

    for rowid, phrase, psalm_chapter in phrases_to_check:
        update_count += 1
        if update_count % 100 == 0:
            sys.stdout.write(f"  Updating record {update_count}/{total_updates}...\r")
            sys.stdout.flush()

        locations = phrase_locations.get(phrase, [])
        
        other_locations = []
        for loc in locations:
            if loc['book'] != 'Psalms' or loc['chapter'] != psalm_chapter:
                other_locations.append(f"{loc['book']} {loc['chapter']}:{loc['verse']}")
        
        is_unique = not bool(other_locations)
        locations_str = json.dumps(other_locations) if other_locations else None
        
        liturgy_cursor.execute(
            f"UPDATE {LITURGY_TABLE_NAME} SET is_unique = ?, locations = ? WHERE rowid = ?",
            (is_unique, locations_str, rowid)
        )
    
    print(f"  Updating record {total_updates}/{total_updates}... Done.")

    print("\nCommitting changes to the database...")
    liturgy_conn.commit()
    liturgy_conn.close()

    print("\nProcess completed successfully.")

if __name__ == '__main__':
    main()
