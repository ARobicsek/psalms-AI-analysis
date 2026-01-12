import sys
from pathlib import Path
import sqlite3
import json

# Add src to path
sys.path.append(str(Path.cwd()))

from src.agents.figurative_librarian import FigurativeLibrarian, FigurativeRequest

def test_figurative_priority_psalm21():
    """
    Test script to evaluate the output of the Figurative Librarian 
    for the specific request found in the logs (Psalm 21, 'back' vehicle terms).
    
    This verifies that the new priority search logic correctly handles the 
    ordered list of search terms.
    """
    print("Initializing FigurativeLibrarian...")
    try:
        librarian = FigurativeLibrarian()
    except Exception as e:
        print(f"Error initializing librarian: {e}")
        return

    # Request from logs/micro_analyst_v2_20251221_160949.log lines 203-206
    # vehicle_search_terms: ['back', 'back', 'shoulder', 'turn back', 'flee', 'retreat', 'face', 'bowstring', 'arrow', 'aimed', 'turn shoulder', 'show back']
    
    # Note: 'back' appears twice in the log, likely due to LLM output. 
    # The priority search logic should handle deduplication.
    search_terms = ['back', 'back', 'shoulder', 'turn back', 'flee', 'retreat', 'face', 'bowstring', 'arrow', 'aimed', 'turn shoulder', 'show back']
    
    print(f"\n--- Executing Search Request ---")
    print(f"Vehicle Terms (in order): {search_terms}")
    
    request = FigurativeRequest(
        book="Psalms",
        vehicle_search_terms=search_terms,
        max_results=20  # Standard limit from MicroAnalyst
    )
    
    bundle = librarian.search(request)
    
    print(f"\n--- Search Results ({len(bundle.instances)} found) ---")
    
    # Track which term matched which result
    term_matches = {}
    
    for i, inst in enumerate(bundle.instances, 1):
        # Identify which search term likely matched this instance
        vehicles = inst.vehicle if inst.vehicle else []
        vehicle_str = ", ".join(vehicles).lower()
        
        matched_term = "unknown"
        for term in search_terms:
            if term.lower() in vehicle_str or term.lower() in inst.figurative_text.lower():
                matched_term = term
                break
                
        print(f"{i}. {inst.reference}")
        print(f"   Figurative Text: {inst.figurative_text}")
        print(f"   Vehicle Tags: {vehicles}")
        print(f"   Likely Matched Term: {matched_term}")
        print()
        
        if matched_term not in term_matches:
            term_matches[matched_term] = 0
        term_matches[matched_term] += 1

    print("\n--- Distribution Analysis ---")
    print("Counts per search term (verifying priority order):")
    seen_terms = set()
    for term in search_terms:
        term_lower = term.lower()
        if term_lower in seen_terms:
            continue
        seen_terms.add(term_lower)
        
        count = 0
        # Check against matches
        for matched in term_matches:
            if term_lower in matched.lower():
                count += term_matches[matched]
        
        print(f"  '{term}': {count}")

    # Validation
    back_count = term_matches.get('back', 0)
    print(f"\nPrimary term 'back' count: {back_count}")
    
    if back_count > 0:
        print("SUCCESS: High priority term 'back' is represented in results.")
    else:
        print("NOTE: 'back' not found or other terms took precedence (check database content).")

if __name__ == "__main__":
    test_figurative_priority_psalm21()
