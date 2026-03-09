import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.cost_tracker import CostTracker

def test_cost_tracker_events():
    tracker = CostTracker()
    
    # Add some usage
    tracker.add_usage("claude-sonnet-4-6", input_tokens=1000, output_tokens=500, thinking_tokens=2000)
    tracker.add_usage("gpt-5.4", input_tokens=2000, output_tokens=800)
    
    # Log some events
    tracker.log_event("Micro Analyst", "Retry", "JSON repair/validation failed (attempt 1)")
    tracker.log_event("Macro Analyst", "Retry", "APIConnectionError (attempt 2)")
    tracker.log_event("Question Curator", "Error", "LLM error: RateLimitError")
    
    summary = tracker.get_summary()
    print(summary)
    
    assert "PIPELINE EVENTS & RETRIES" in summary
    assert "[Micro Analyst] Retry: JSON repair/validation failed (attempt 1)" in summary
    assert "[Macro Analyst] Retry: APIConnectionError (attempt 2)" in summary
    assert "[Question Curator] Error: LLM error: RateLimitError" in summary
    print("ALL TESTS PASSED")

if __name__ == "__main__":
    test_cost_tracker_events()
