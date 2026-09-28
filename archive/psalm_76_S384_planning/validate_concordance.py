"""Session 384: re-run Ps 76 arm A's and arm B's concordance searches through the fixed
librarian and compare with what their saved research bundles reported. $0, no API.

Usage: python archive/psalm_76_S384_planning/validate_concordance.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import logging
logging.disable(logging.CRITICAL)

from src.agents.concordance_librarian import ConcordanceLibrarian, ConcordanceRequest
from src.agents.research_assembler import (_distribution_line, _sample_for_display,
                                           MAX_DISPLAY_RESULTS)

BUNDLES = {
    "A": ROOT / "output/psalm_76/psalm_076_research_v2.md",
    "B": ROOT / "output/psalm_76/_opus55_B/psalm_076_research_v2.md",
}
HEADER = re.compile(r"^### (.+?) \((\d+) external results, auto, (\w+)\)", re.M)

lib = ConcordanceLibrarian()
for arm, path in BUNDLES.items():
    text = path.read_text(encoding="utf-8")
    print(f"\n===== Arm {arm}: {path.relative_to(ROOT)}")
    print(f"{'query':14} {'old':>4} {'new':>5}  lemma(s) now          shown-Psalms  where it occurs")
    old_total = new_total = 0
    for q, old, level in HEADER.findall(text):
        req = ConcordanceRequest(query=q, level=level, source_psalm=76, include_variations=True)
        b = lib.search_with_variations(req)
        n = len(b.results)
        words = q.split()
        lemmas = [lib.search._resolve_lemma(w, 76) for w in words]
        shown = _sample_for_display(b.results, MAX_DISPLAY_RESULTS, q, "")
        ps_shown = sum(1 for r in shown if r.book == "Psalms")
        old_total += int(old)
        new_total += n
        flag = "  (>120: dropped as over-common)" if len(words) == 1 and n > 120 else ""
        print(f"{q:14} {old:>4} {n:>5}  {'+'.join(str(l) for l in lemmas):20} {ps_shown:>5}         "
              f"{_distribution_line(b.results) if b.results else '-'}{flag}")
    print(f"TOTAL old {old_total}  new {new_total}")
