#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Show all results for 'לא ימוט לעולם' search"""

import sys
from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest
from src.data_sources.tanakh_database import TanakhDatabase

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Initialize database and librarian
db = TanakhDatabase()
librarian = ConcordanceLibrarian()

request = ConcordanceRequest(
    query='לא ימוט לעולם',
    level='consonantal',
    scope='auto',
    include_variations=True
)

bundle = librarian.search_with_variations(request)

print('ALL RESULTS THAT MATCH "לא ימוט לעולם":')
print('='*80)
for i, result in enumerate(bundle.results, 1):
    print(f'{i}. {result.reference}')
    print(f'   Matched: {result.matched_word}')

    # Check if this is a full phrase match or partial
    if len(result.matched_word.split()) == 3:
        print(f'   Status: FULL PHRASE MATCH (3 words)')
    elif len(result.matched_word.split()) == 2:
        print(f'   Status: PARTIAL MATCH (2 words) - BUG!')
    else:
        print(f'   Status: Single word match - BUG!')

    # Show just the key part of the Hebrew
    if result.book == 'Psalms' and result.chapter == 15 and result.verse == 5:
        print(f'   Hebrew: ...לֹ֖א יִמּ֣וֹט לְעוֹלָֽם׃')
    elif result.book == 'Psalms' and result.chapter == 125 and result.verse == 1:
        print(f'   Hebrew: ...לֹא־יִ֝מּ֗וֹט לְעוֹלָ֥ם יֵשֵֽׁב׃')
    elif result.book == 'Isaiah' and result.chapter == 40 and result.verse == 20:
        print(f'   Hebrew: ...לֹ֥א יִמּֽוֹט׃')
    elif result.book == 'Isaiah' and result.chapter == 41 and result.verse == 7:
        print(f'   Hebrew: ...לֹ֥א יִמּֽוֹט׃')
    elif result.book == 'Isaiah' and result.chapter == 54 and result.verse == 10:
        print(f'   Hebrew: ...לֹ֣א תָמ֔וֹט')
    else:
        print(f'   Hebrew: {result.hebrew_text[:80]}...')
    print()