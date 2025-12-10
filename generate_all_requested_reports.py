#!/usr/bin/env python3
"""
Generate thematic parallels reports for the specific Psalm chunks requested by the user:
a) ps 145, chunk starting with verse 14
b) ps 121, chunk starting with verse 3
c) ps 8, chunk starting with verse 1
d) ps 8, chunk starting with verse 2
e) ps 8, chunk starting with verse 6
f) ps 8, chunk starting with verse 9
"""
import subprocess
import sys
from pathlib import Path

# List of reports to generate: (psalm_number, start_verse)
reports = [
    (145, 14),
    (121, 3),
    (8, 1),
    (8, 2),
    (8, 6),
    (8, 9)
]

def main():
    print("Generating all requested Psalm thematic parallels reports...")
    print("="*80)

    script_path = Path(__file__).parent / "generate_psalm_reports.py"

    if not script_path.exists():
        print(f"Error: {script_path} not found!")
        print("Please run the single report generation script first.")
        sys.exit(1)

    for psalm, start_verse in reports:
        print(f"\nGenerating report for Psalm {psalm}, chunk starting at verse {start_verse}...")
        print("-"*60)

        try:
            # Run the report generation script
            result = subprocess.run(
                [sys.executable, str(script_path), str(psalm), str(start_verse)],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            if result.returncode == 0:
                print(f"✓ Successfully generated Psalm {psalm} report")
                # Show a snippet of the output
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if "Full report saved to:" in line:
                        print(f"  {line}")
                    elif "Total parallels found:" in line:
                        print(f"  {line}")
            else:
                print(f"✗ Error generating Psalm {psalm} report:")
                print(f"  {result.stderr}")

        except Exception as e:
            print(f"✗ Exception while generating Psalm {psalm} report: {e}")

    print("\n" + "="*80)
    print("Report generation complete!")
    print("All reports have been saved in the current directory.")


if __name__ == "__main__":
    main()