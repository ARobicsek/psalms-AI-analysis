"""
Session 350 — trace ONE psalm's concordance pipeline end to end (DISCARDABLE).

Captures, using the REAL production methods (via lightweight wrappers, no logic
duplicated):
  STAGE A: what the LLM asked for (raw Stage-2 picks)
  STAGE B: after _override_llm_base_forms (exact-phrase clobbering for collocations;
           single-word root queries left intact)
  STAGE C: after _augment_with_root_searches (2-word cap + added distinctive-root traces)
  FINAL  : what we searched, and what came back (external count, self dropped, common drop)

Usage: python scripts/EXPERIMENT_concordance_trace.py 55
"""
import sys, json, copy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
import logging; logging.disable(logging.WARNING)
from dotenv import load_dotenv; load_dotenv()

from src.agents.micro_analyst import MicroAnalystV2
from src.concordance.hebrew_text_processor import split_words

LIVE_DB = "database/tanakh.db"
COMMON_CAP = 60


def load_discoveries(psalm: int) -> dict:
    pp = f"{psalm:03d}"
    data = json.loads(Path(f"output/psalm_{psalm}/psalm_{pp}_micro_v2.json").read_text(encoding="utf-8"))
    return {"verse_discoveries": [
        {"verse_number": vc.get("verse_number"), "observations": vc.get("commentary", ""),
         "lexical_insights": vc.get("lexical_insights", []),
         "figurative_elements": vc.get("figurative_analysis", [])}
        for vc in data.get("verse_commentaries", [])
    ]}


def main():
    psalm = int(sys.argv[1]) if len(sys.argv) > 1 else 55
    analyst = MicroAnalystV2(db_path=LIVE_DB)
    discoveries = load_discoveries(psalm)
    cap = {}

    orig_override = analyst._override_llm_base_forms
    def wrap_override(rr, *a, **k):
        cap['A'] = [(r.query, (r.notes or ''), list(getattr(r, 'alternate_queries', []) or []))
                    for r in rr.concordance_requests]
        res = orig_override(rr, *a, **k)
        cap['B'] = [(r.query, (r.notes or '')) for r in res.concordance_requests]
        return res
    analyst._override_llm_base_forms = wrap_override

    orig_aug = analyst._augment_with_root_searches
    def wrap_aug(rr, *a, **k):
        res = orig_aug(rr, *a, **k)
        cap['C'] = list(res.concordance_requests)
        return res
    analyst._augment_with_root_searches = wrap_aug

    rr = analyst._generate_research_requests(discoveries, psalm)
    librarian = analyst.research_assembler.concordance_librarian

    def hdr(t): print(f"\n{'='*82}\n{t}\n{'='*82}")

    hdr(f"PSALM {psalm} — STAGE A: what the LLM asked for ({len(cap['A'])} searches)")
    for q, notes, alts in cap['A']:
        print(f"  q={q!r}  ({len(split_words(q))}w)")
        if alts: print(f"      alternates: {alts}")
        print(f"      purpose: {notes[:110]}")

    hdr("STAGE B: after override (collocations forced to exact verse form; roots untouched)")
    for (qa, _, _), (qb, nb) in zip(cap['A'], cap['B']):
        changed = '  <-- CHANGED' if qa != qb else ''
        tag = ' [FIXED]' if 'FIXED' in nb else (' [GUARANTEED]' if 'GUARANTEED' in nb else '')
        print(f"  {qa!r:26} -> {qb!r}{tag}{changed}")

    hdr("STAGE C: after augmentation (2-word cap + added distinctive-root traces)")
    a_b_queries = {qb for _, qb in cap['B']}
    for r in cap['C']:
        words = len(split_words(r.query))
        if '[root trace' in (r.notes or ''):
            kind = 'ADDED ROOT'
        elif 'CAPPED' in (r.notes or ''):
            kind = 'CAPPED 2w'
        elif r.query in a_b_queries:
            kind = 'kept (LLM)'
        else:
            kind = 'kept'
        note = (r.notes or '')
        note = note[note.find('['):] if '[' in note else note[:60]
        print(f"  [{kind:11} {words}w] {r.query:22} {note[:80]}")

    hdr("FINAL: what we searched + what came back")
    kept = dropped = ext_yield = 0
    for r in cap['C']:
        r.source_psalm = psalm
        b = librarian.search_with_variations(r)
        nwords = len(split_words(r.query))
        ext = len(b.results)
        if nwords <= 1 and ext > COMMON_CAP:
            print(f"  DROP-common  {r.query:20} ext={ext}")
            dropped += 1; continue
        kept += 1
        if ext > 0: ext_yield += 1
        kind = 'ROOT' if '[root trace' in (r.notes or '') else ('COLLOC' if nwords >= 2 else 'word')
        flag = 'only-self' if (ext == 0 and b.only_self) else ('none' if ext == 0 else 'EXTERNAL')
        print(f"  [{kind:6}] {r.query:20} ext={ext:3} self_drop={b.self_match_count} {flag:9} {[x.reference for x in b.results][:7]}")
    print(f"\n  SUMMARY: {len(cap['A'])} LLM picks -> {len(cap['C'])} after augment -> "
          f"{kept} searched ({dropped} common dropped); {ext_yield}/{kept} yielded external matches")


if __name__ == "__main__":
    main()
