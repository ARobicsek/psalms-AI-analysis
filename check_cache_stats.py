#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check phrase cache statistics."""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import sqlite3

conn = sqlite3.connect('data/liturgy.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM phrase_cache')
print(f'Cached phrases: {cursor.fetchone()[0]:,}')

cursor.execute('SELECT COUNT(*) FROM phrase_cache WHERE is_searchable = 1')
print(f'Searchable phrases: {cursor.fetchone()[0]:,}')

print('\nTop 10 distinctive phrases:')
cursor.execute('''
    SELECT phrase_normalized, word_count, corpus_frequency, distinctiveness_score
    FROM phrase_cache
    WHERE is_searchable = 1
    ORDER BY distinctiveness_score DESC
    LIMIT 10
''')

for i, row in enumerate(cursor.fetchall(), 1):
    phrase, wc, freq, score = row
    print(f'{i:2}. {phrase[:40]:40} | words={wc} | freq={freq:3} | score={score:.3f}')

conn.close()
