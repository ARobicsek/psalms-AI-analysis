"""
Build the stress lexicon consumed by src/agents/phonetic_analyst.py.

Most Hebrew accents sit on the stressed syllable, so the cantillation tells the
PhoneticAnalyst where the stress falls. Three do not: dehi, geresh muqdam and
ole are written on the first letter of the word regardless (measured coincidence
with the stressed letter: 11.2%, 8.8%, 7.0%), and a lone postpositive accent
gives no position either. For those words the analyst would have to fall back on
the default ultima stress -- wrong about one time in five, which is how
Ps 70:4 יָ֭שׁוּבוּ came out as "ya-shu-VU" instead of "ya-SHU-vu".

This script resolves those words from the Masoretic text itself: the same pointed
form, read off another verse where its accent IS unambiguous. Ps 70:4's
יָשׁוּבוּ carries only a dehi, but ten other occurrences (Gen 15:16 and on) carry
a merkha, munah or tifcha, all on the shin.

Output: src/agents/stress_lexicon.json.gz, {pointed form: stressed letter index}.
Letter indices rather than syllable indices, so the file stays valid if the
syllabifier changes.

Usage:
    python scripts/build_stress_lexicon.py            # write the lexicon
    python scripts/build_stress_lexicon.py --check     # report only, write nothing
"""
import argparse
import gzip
import json
import os
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.agents.phonetic_analyst import PhoneticAnalyst  # noqa: E402

DB_PATH = os.path.join(ROOT, 'database', 'tanakh.db')
OUT_PATH = os.path.join(ROOT, 'src', 'agents', 'stress_lexicon.json.gz')

# A form is only recorded when this fraction of its readings agree, so that words
# with genuine contextual variation (pausal retraction) are left to the accents.
MIN_AGREEMENT = 0.6


def stressed_letter_index(analyst, word):
    """
    Index of the stressed letter, but only where the accents settle it. Returns
    None for words whose stress the analyst has to infer -- those are what the
    lexicon is for, so recording them would just feed a guess back in.
    """
    normalized = unicodedata.normalize('NFD', word)
    _, _, _, letter_accents, _ = analyst._scan_word(normalized)
    char_index, source = analyst._stress_letter(letter_accents, normalized)
    if char_index is None or source not in ('accent', 'doubled', 'tsinnorit'):
        return None
    chars = list(normalized)
    return sum(1 for c in chars[:char_index] if c in analyst.consonant_map)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true',
                    help='report statistics without writing the lexicon')
    ap.add_argument('--db', default=DB_PATH, help=f'Tanakh database (default: {DB_PATH})')
    ap.add_argument('--out', default=OUT_PATH, help=f'output path (default: {OUT_PATH})')
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding='utf-8')
    if not os.path.exists(args.db):
        sys.exit(f'no such database: {args.db}')

    analyst = PhoneticAnalyst(stress_lexicon={})  # never consult an existing lexicon
    con = sqlite3.connect(args.db)

    readings = defaultdict(Counter)
    words = skipped = 0
    for (hebrew,) in con.execute('select hebrew from verses'):
        for token in hebrew.split():
            # Maqqef compounds are one accent domain: split so each component is
            # keyed on its own, and drop the ketiv/qere and section markers.
            if any(c in token for c in '()[]{}'):
                continue
            for part in token.split('־'):
                if not part.strip():
                    continue
                words += 1
                index = stressed_letter_index(analyst, part)
                if index is None:
                    skipped += 1
                    continue
                readings[PhoneticAnalyst.lexicon_key(part)][index] += 1

    lexicon = {}
    ambiguous = 0
    for key, counts in readings.items():
        index, hits = counts.most_common(1)[0]
        if hits / sum(counts.values()) >= MIN_AGREEMENT:
            lexicon[key] = index
        else:
            ambiguous += 1

    print(f'words scanned                     : {words:,}')
    print(f'  stress inferred, not recorded   : {skipped:,}')
    print(f'distinct forms with a fixed stress: {len(readings):,}')
    print(f'  dropped, readings disagree      : {ambiguous:,} '
          f'(below {MIN_AGREEMENT:.0%} agreement)')
    print(f'lexicon entries                   : {len(lexicon):,}')

    if args.check:
        print('\n--check: nothing written')
        return

    payload = json.dumps(lexicon, ensure_ascii=False, separators=(',', ':'))
    with gzip.open(args.out, 'wt', encoding='utf-8') as fh:
        fh.write(payload)
    print(f'\nwrote {args.out}  ({os.path.getsize(args.out) / 1e6:.2f} MB)')

    # Round-trip check: the analyst must read back exactly what was written.
    reloaded = PhoneticAnalyst()._load_stress_lexicon()
    if reloaded != lexicon:
        sys.exit('ERROR: lexicon did not round-trip through the analyst loader')
    print('round-trip verified')


if __name__ == '__main__':
    main()
