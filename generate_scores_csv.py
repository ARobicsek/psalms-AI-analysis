#!/usr/bin/env python3
"""
Generate a CSV table from enhanced_scores_v6.json with one row per psalm pair.
"""

import json
import csv

# Read the JSON file
print("Reading enhanced_scores_v6.json...")
with open('/home/user/psalms-AI-analysis/data/analysis_results/enhanced_scores_v6.json', 'r') as f:
    data = json.load(f)

print(f"Found {len(data)} psalm pairs")

# Create the CSV file
output_path = '/home/user/psalms-AI-analysis/data/analysis_results/psalm_scores_table.csv'
print(f"Writing CSV to {output_path}...")

with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)

    # Write header
    writer.writerow([
        'Psalm A',
        'Psalm B',
        'Contiguous Phrase Matches',
        'Skipgram Matches',
        'Root Matches',
        'Final Score'
    ])

    # Write data rows
    for entry in data:
        writer.writerow([
            entry['psalm_a'],
            entry['psalm_b'],
            entry['deduplicated_contiguous_count'],
            entry['deduplicated_skipgram_count'],
            entry['deduplicated_root_count'],
            round(entry['final_score'], 2)  # Round to 2 decimal places for readability
        ])

print(f"CSV file created successfully with {len(data)} rows (plus header)")
print(f"Output saved to: {output_path}")
