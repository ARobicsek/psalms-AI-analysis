import sys
from pathlib import Path
import sqlite3
from dataclasses import replace

# Add src to path
sys.path.append(str(Path.cwd()))

from src.agents.figurative_librarian import FigurativeLibrarian, FigurativeRequest

def test_priority_search():
    print("Initializing FigurativeLibrarian...")
    try:
        librarian = FigurativeLibrarian()
    except Exception as e:
        print(f"Error initializing librarian: {e}")
        return

    # Database path check
    if not librarian.db_path.exists():
        print(f"Database not found at {librarian.db_path}")
        return

    print("Database found.")

    # Test Case 1: High Priority Term First
    # "rock" is very common, "water" is also common.
    # If we ask for ["rock", "water"] with max_results=5, we should see mostly rock.
    
    terms_order_1 = ["rock", "water"]
    req1 = FigurativeRequest(
        book="Psalms",
        vehicle_search_terms=terms_order_1,
        max_results=5,
        metaphor=True # Filter to ensure we get metaphors
    )
    
    print(f"\nTest 1: Searching for {terms_order_1} (Max 5)...")
    bundle1 = librarian.search(req1)
    
    print(f"Found {len(bundle1.instances)} results.")
    for i, inst in enumerate(bundle1.instances):
        vehicles = inst.vehicle if inst.vehicle else []
        print(f"  {i+1}. {inst.reference} - Vehicles: {vehicles}")

    # Analyze Test 1
    rock_count = sum(1 for inst in bundle1.instances if any("rock" in v.lower() for v in (inst.vehicle or [])))
    water_count = sum(1 for inst in bundle1.instances if any("water" in v.lower() for v in (inst.vehicle or [])))
    print(f"  Analysis: Rock matches: {rock_count}, Water matches: {water_count}")


    # Test Case 2: Reverse Order
    # "water" first, then "rock".
    terms_order_2 = ["water", "rock"]
    req2 = FigurativeRequest(
        book="Psalms",
        vehicle_search_terms=terms_order_2,
        max_results=5,
        metaphor=True
    )
    
    print(f"\nTest 2: Searching for {terms_order_2} (Max 5)...")
    bundle2 = librarian.search(req2)
    
    print(f"Found {len(bundle2.instances)} results.")
    for i, inst in enumerate(bundle2.instances):
        vehicles = inst.vehicle if inst.vehicle else []
        print(f"  {i+1}. {inst.reference} - Vehicles: {vehicles}")
        
    # Analyze Test 2
    rock_count_2 = sum(1 for inst in bundle2.instances if any("rock" in v.lower() for v in (inst.vehicle or [])))
    water_count_2 = sum(1 for inst in bundle2.instances if any("water" in v.lower() for v in (inst.vehicle or [])))
    print(f"  Analysis: Water matches: {water_count_2}, Rock matches: {rock_count_2}")

    # Conclusion
    if rock_count > water_count and water_count_2 > rock_count_2:
        print("\nSUCCESS: Priority search is working. Order of terms affects result composition.")
    else:
        print("\nWARNING: Priority search might not be working as expected. Check distribution.")

if __name__ == "__main__":
    test_priority_search()
