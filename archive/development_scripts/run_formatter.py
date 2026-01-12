"""
Simple Wrapper Script for Commentary Formatter

This script provides a simpler way to run the print-ready commentary formatter
for a given psalm, assuming the standard file structure.

Usage:
    python scripts/run_formatter.py PSALM_NUMBER

Example:
    python scripts/run_formatter.py 145

This will automatically find the necessary input files in the output directory
and generate the final print-ready markdown file.

Author: Gemini Code Assist
Date: 2025-10-19
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Main function to run the formatter."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_formatter.py <psalm_number>")
        sys.exit(1)

    try:
        psalm_number = int(sys.argv[1])
    except ValueError:
        print("Error: Psalm number must be an integer.")
        sys.exit(1)

    print(f"--- Running Print-Ready Formatter for Psalm {psalm_number} ---")

    # Define file paths based on convention
    project_root = Path(__file__).parent.parent
    output_dir = project_root / f"output/test_psalm_{psalm_number}"
    psalm_padded = f"{psalm_number:03d}"

    command = [
        sys.executable,
        str(project_root / "src" / "utils" / "commentary_formatter.py"),
        "--psalm", str(psalm_number),
        "--intro", str(output_dir / f"psalm_{psalm_padded}_edited_intro.md"),
        "--verses", str(output_dir / f"psalm_{psalm_padded}_edited_verses.md"),
        "--summary", str(output_dir / f"psalm_{psalm_padded}_pipeline_stats.json"),
        "--output", str(output_dir / f"psalm_{psalm_padded}_print_ready.md"),
        "--db-path", str(project_root / "database/tanakh.db")
    ]

    try:
        print(f"Executing: {' '.join(command)}\n")
        subprocess.run(command, check=True, text=True, encoding='utf-8')
        print(f"\n--- Successfully generated print-ready file for Psalm {psalm_number} ---")
    except FileNotFoundError as e:
        print(f"\nError: An input file was not found. Please ensure all pipeline steps before formatting have been run.")
        print(f"Missing file: {e.filename}")
    except subprocess.CalledProcessError as e:
        print(f"\nError: The formatter script failed with exit code {e.returncode}.")
        print(f"STDOUT:\n{e.stdout}")
        print(f"STDERR:\n{e.stderr}")

if __name__ == '__main__':
    main()