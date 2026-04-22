import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.document_generator import DocumentGenerator

def main():
    parser = argparse.ArgumentParser(description="Regenerate DOCX for a specific Psalm")
    parser.add_argument("psalm", type=int, help="Psalm number")
    args = parser.parse_args()

    psalm_number = args.psalm
    
    # Handle optional leading zero directories
    base_dir = Path(f'output/psalm_{psalm_number:03d}')
    if not base_dir.exists():
        base_dir = Path(f'output/psalm_{psalm_number}')
        if not base_dir.exists():
            print(f"Error: Could not find output directory for Psalm {psalm_number}")
            return

    # Check for copy edited versions first (the final state of the pipeline)
    edited_intro_file = base_dir / f"psalm_{psalm_number:03d}_edited_intro.md"
    edited_verses_file = base_dir / f"psalm_{psalm_number:03d}_edited_verses.md"
    
    # If the combined copy_edited file exists, handle it (some pipeline versions produce a single file)
    copy_edited = base_dir / f"psalm_{psalm_number:03d}_copy_edited.md"
    if copy_edited.exists():
        if not edited_intro_file.exists():
            edited_intro_file = copy_edited
        if not edited_verses_file.exists():
            edited_verses_file = copy_edited

    # Check for original markdown files if copy-edited files aren't found
    if not edited_intro_file.exists():
        edited_intro_file = base_dir / f"psalm_{psalm_number:03d}_intro.md"
    if not edited_verses_file.exists():
        edited_verses_file = base_dir / f"psalm_{psalm_number:03d}_commentary.md"

    if not edited_intro_file.exists() or not edited_verses_file.exists():
         print(f"Error: Missing required markdown files in {base_dir}")
         return

    summary_json_file = base_dir / f"psalm_{psalm_number:03d}_pipeline_stats.json"
    if not summary_json_file.exists():
        summary_json_file = base_dir / f"psalm_{psalm_number:03d}_summary.json"
        
    docx_output_file = base_dir / f"psalm_{psalm_number:03d}_commentary.docx"
    
    refined_q = base_dir / f"psalm_{psalm_number:03d}_reader_questions_refined.json"
    reader_questions_file = base_dir / f"psalm_{psalm_number:03d}_reader_questions.json"
    
    q_file = refined_q if refined_q.exists() else (reader_questions_file if reader_questions_file.exists() else None)

    print(f"Generating DOCX for Psalm {psalm_number}...")
    try:
        gen = DocumentGenerator(
            psalm_number, 
            edited_intro_file, 
            edited_verses_file, 
            summary_json_file, 
            docx_output_file, 
            q_file
        )
        gen.generate()
        print(f"Success! Saved to {docx_output_file}")
    except Exception as e:
        print(f"Error generating Word document: {e}")

if __name__ == "__main__":
    main()
