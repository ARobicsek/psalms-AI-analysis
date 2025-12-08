import json

prayers = []
with open('output/test_canonical_sample.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            prayers.append(json.loads(line))

with open('output/test_results_summary.txt', 'w', encoding='utf-8') as out:
    out.write('='*80 + '\n')
    out.write('LITURGICAL CANONICALIZATION TEST RESULTS\n')
    out.write('Model: gemini-2.5-pro\n')
    out.write('='*80 + '\n\n')

    for i, p in enumerate(prayers, 1):
        out.write(f'\nPRAYER #{i}: {p["canonical_prayer_name"]}\n')
        out.write('='*80 + '\n')
        out.write(f'\nORIGINAL: ID={p["original_prayer_id"]}, Source={p["source_corpus"]}\n')
        out.write(f'\nHIERARCHY:\n')
        out.write(f'  L1 (Occasion):   {p["L1_Occasion"]}\n')
        out.write(f'  L2 (Service):    {p["L2_Service"]}\n')
        out.write(f'  L3 (Signpost):   {p["L3_Signpost"]}\n')
        out.write(f'  L4 (SubSection): {p.get("L4_SubSection", "N/A")}\n')
        out.write(f'\nDETAILS:\n')
        out.write(f'  Canonical Name: {p["canonical_prayer_name"]}\n')
        out.write(f'  Nusach: {p["nusach"]}\n')
        out.write(f'  Usage Type: {p["usage_type"]}\n')
        out.write(f'\nLOCATION:\n  {p["relative_location_description"]}\n')
        out.write(f'\nHEBREW TEXT:\n  {p["hebrew_text"][:150]}...\n\n')

    out.write('\n' + '='*80 + '\n')
    out.write('SUMMARY\n')
    out.write('='*80 + '\n')
    out.write(f'Total prayers processed: {len(prayers)}\n')
    out.write(f'All have L3_Signpost: {all("L3_Signpost" in p for p in prayers)}\n')
    out.write(f'All have canonical_name: {all("canonical_prayer_name" in p for p in prayers)}\n')
    out.write(f'All have location_description: {all("relative_location_description" in p for p in prayers)}\n')

    l3_cats = set(p.get('L3_Signpost', 'N/A') for p in prayers)
    out.write(f'\nL3 Signpost categories used:\n')
    for cat in sorted(l3_cats):
        out.write(f'  - {cat}\n')

print('Results written to: output/test_results_summary.txt')
