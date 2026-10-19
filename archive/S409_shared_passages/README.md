# Session 409: Related Psalms → Shared Passages (measurement record)

- `doublet_scan.py`: the OLD detector (`RelatedPsalmsLibrarian._find_shared_verse_pairs`, its real thresholds) run on every psalm against every chapter of the Bible. 8 doublets, 15 single-verse flags (8 of them matching headings); misses listed in IMPLEMENTATION_LOG Session 409.
- `doublet_chain.py`, `doublet_chain3.py`: the lemma-chain prototypes (all words counted: 1,920 hits; content words or dense runs: 121 hits, 25/32 known).
- `eval_shared.py`: the production module against the 32 known cases and the old section's size for all 150 psalms (old 1,953,321 chars, new 53,422).
- `refresh_dry.py`: the reused-bundle swap on copies of the 86 production bundles (median 18,251 chars saved, no other section changed).
- `all_sections.md`: the production module's section for every psalm, 1–150, as built on 2026-10-19.

Run from the repo root with `PYTHONIOENCODING=utf-8 python archive/S409_shared_passages/<script>.py <out.json>` (the scan and eval scripts take an output path). The old librarian now lives in `src/agents/archive/`; `doublet_scan.py` and `eval_shared.py` import it from `src.agents.related_psalms_librarian` and need that path updated to run again.
