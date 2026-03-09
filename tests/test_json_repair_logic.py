import json
import logging
from json_repair import repair_json

# Setup basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_json_repair")

def simulate_discovery_pass(response_text: str, expected_verses: int) -> dict:
    """
    Simulates the JSON parsing and repair logic to be added to MicroAnalystV2._discovery_pass.
    """
    try:
        discoveries = json.loads(response_text)
        logger.info("  ✓ Discovery pass complete (standard JSON load)")
        return discoveries
        
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parsing error: {e}")
        logger.info("  Attempting to repair truncated JSON...")
        
        try:
            # Attempt to repair the JSON string
            repaired_text = repair_json(response_text, return_objects=False)
            if not repaired_text:
                raise ValueError("JSON repair returned empty string")
                
            discoveries = json.loads(repaired_text)
            
            # --- STRUCTURAL VALIDATION ---
            
            # 1. Check if we have the expected number of verses
            parsed_verse_count = len(discoveries.get('verse_discoveries', []))
            if parsed_verse_count != expected_verses:
                raise ValueError(f"Structural validation failed: Expected {expected_verses} verses, but found {parsed_verse_count}")
                
            # 2. Check if we have the interesting_questions section
            questions = discoveries.get('interesting_questions', [])
            if not questions or len(questions) < 3:
                raise ValueError(f"Structural validation failed: Missing or insufficient interesting_questions (found {len(questions) if isinstance(questions, list) else 0})")
                
            logger.info("  ✓ Successfully repaired and validated truncated JSON!")
            return discoveries
            
        except Exception as repair_e:
             logger.error(f"Failed to repair/validate structural JSON: {repair_e}")
             raise ValueError(f"Invalid JSON from discovery pass (repair failed): {repair_e}")

def test_valid_json():
    print("\n--- Testing Valid JSON ---")
    valid_json = '''{
      "verse_discoveries": [
        {
          "verse_number": 1,
          "observations": "Observation 1",
          "lexical_insights": [],
          "figurative_elements": []
        },
        {
          "verse_number": 2,
          "observations": "Observation 2",
          "lexical_insights": [],
          "figurative_elements": []
        }
      ],
      "interesting_questions": [
        "Question 1?",
        "Question 2?",
        "Question 3?",
        "Question 4?"
      ]
    }'''
    try:
        res = simulate_discovery_pass(valid_json, 2)
        print("SUCCESS: Valid JSON parsed.")
    except Exception as e:
        print(f"FAILED: {e}")

def test_truncated_json_repairable():
    print("\n--- Testing Truncated JSON (Repairable) ---")
    # Missing closing braces/brackets for the 'interesting_questions' array and main object
    truncated_json = '''{
      "verse_discoveries": [
        {
          "verse_number": 1,
          "observations": "Observation 1",
          "lexical_insights": [],
          "figurative_elements": []
        },
        {
          "verse_number": 2,
          "observations": "Observation 2",
          "lexical_insights": [],
          "figurative_elements": []
        }
      ],
      "interesting_questions": [
        "Question 1?",
        "Question 2?",
        "Question 3?",
        "Question 4?"'''
    try:
        res = simulate_discovery_pass(truncated_json, 2)
        print("SUCCESS: Truncated JSON repaired and validated.")
    except Exception as e:
        print(f"FAILED (Unexpected): {e}")

def test_severely_truncated_json():
    print("\n--- Testing Severely Truncated JSON (Fails Validation) ---")
    # Cut off in the middle of verse 2 - missing verses and questions
    severely_truncated_json = '''{
      "verse_discoveries": [
        {
          "verse_number": 1,
          "observations": "Observation 1",
          "lexical_insights": [],
          "figurative_elements": []
        },
        {
          "verse_number": 2,
          "observations": "Observation 2",
          "lexi'''
    try:
        res = simulate_discovery_pass(severely_truncated_json, 2)
        print(f"FAILED: Should have raised ValueError but succeeded: {res}")
    except ValueError as e:
        print(f"SUCCESS: Validation correctly rejected the repair. Error: {e}")
        
if __name__ == "__main__":
    test_valid_json()
    test_truncated_json_repairable()
    test_severely_truncated_json()
