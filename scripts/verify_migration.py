import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.master_editor import MasterEditor, MASTER_WRITER_PROMPT_V3
from src.agents.master_editor_si import MasterEditorSI, MASTER_WRITER_PROMPT_SI

def verify_migration():
    print("="*50)
    print("VERIFYING MIGRATION TO MASTER WRITER V3")
    print("="*50)

    # 1. Verify MasterEditor (V3)
    try:
        print("\n[1] Checking MasterEditor (V3)...")
        editor = MasterEditor()
        print("  - Instantiation successful")
        
        # Check inheritance
        from src.agents.archive.master_editor_v2 import MasterEditorV2
        if isinstance(editor, MasterEditorV2):
            print("  - Correctly inherits from MasterEditorV2 (Archive)")
        else:
            print("  - FAIL: Does not inherit from MasterEditorV2")
            return

        # Check prompts
        if "Robert Alter" in MASTER_WRITER_PROMPT_V3:
            print("  - MASTER_WRITER_PROMPT_V3 loaded correctly (contains 'Robert Alter')")
        else:
            print("  - FAIL: MASTER_WRITER_PROMPT_V3 content mismatch")
            return

    except Exception as e:
        print(f"  - FAIL: {e}")
        return

    # 2. Verify MasterEditorSI (V3 + SI)
    try:
        print("\n[2] Checking MasterEditorSI...")
        si_editor = MasterEditorSI()
        print("  - Instantiation successful")

        # Check inheritance
        if isinstance(si_editor, MasterEditor):
            print("  - Correctly inherits from MasterEditor (V3)")
        else:
            print("  - FAIL: Does not inherit from MasterEditor")
            return

        # Check prompt injection
        if "SPECIAL AUTHOR DIRECTIVE" in MASTER_WRITER_PROMPT_SI:
            print("  - MASTER_WRITER_PROMPT_SI contains 'SPECIAL AUTHOR DIRECTIVE'")
        else:
            print("  - FAIL: SI Prompt Injection failed")
            return

        if "{special_instruction}" in MASTER_WRITER_PROMPT_SI:
            print("  - MASTER_WRITER_PROMPT_SI contains {special_instruction} placeholder")
        else:
            print("  - FAIL: SI Prompt missing placeholder")
            return

    except Exception as e:
        print(f"  - FAIL: {e}")
        return

    print("\n" + "="*50)
    print("MIGRATION VERIFICATION PASSED")
    print("="*50)

if __name__ == "__main__":
    verify_migration()
