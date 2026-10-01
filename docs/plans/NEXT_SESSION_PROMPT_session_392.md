# Next session (392) — start here

Session 391 evaluated Sefaria (`docs/plans/S391_SEFARIA_EVALUATION.md`) and, at the author's go-ahead, BUILT the
pieces for a Ps 76 A/B: the reception section, the Targum line, the hardened commentary fetch, and the driver.
Nothing paid has run. Details: `IMPLEMENTATION_LOG.md`, Session 391.

## 1. Run the Ps 76 A/B (the author approved; ~$9–13)

```bash
git checkout claude/bold-lamport-yq84so          # or wherever S391 was merged
python scripts/run_s391_reception_ab.py 76 --dry-run     # $0 first: must say 19 passages / ~20.7K chars, 13 Targum verses
python scripts/run_s391_reception_ab.py 76
```

Watch in the log:
- **Arm A** is the first paid run on S388–S391 code, so it also settles old checks: the SD → writer **shared cache**
  (`[forest] dossier head (… chars) matches what synthesis discovery cached`, then call 1 READING ~230K tokens, not
  writing; see `NEXT_SESSION_PROMPT_session_389.md` §1), Brenton's Greek (`LXX Psalm 76 … Brenton's Greek`), and
  the **new commentary fetch**: 11 requests, `data/sefaria_cache/commentary/` filling, and NO
  `is MISSING from this bundle` warning.
- **Arm B**: `[STEP 2+] Reception section: 19 passages …`, `Arm B bundle will be N chars … trim ceiling 350,000`
  (the driver refuses to run B over it), the Targum lines in `output/debug/*forest_prompt_psalm_76.txt`, and
  the dossier-head match again (its own cache).
- After: `output/_s391_reception_ab/psalm_76/README.md` (per-stage cost, both arms) and the two DOCX/PDF at the
  folder's top. The production Ps 76 files must be untouched (the driver restores the echoes dossier and the
  debug dumps; `PSALMS_OUTPUT_ROOT` keeps the writer's files in each arm).

## 2. Then, at $0

- **The claim check** (the reason for the test): every Talmud / midrash / Targum / Hasidic attribution in BOTH
  guides, checked against the cached Sefaria texts (`data/sefaria_cache/reception/psalm_076.json`,
  `…/targum/psalm_076.json`, Sefaria for anything else). Count right / wrong / unverifiable per arm. The S385
  guide's error class: the Targum on 76:5 reported through the Alshich as דְּחִיל alone (it reads נְהִיר דְּחִיל).
- **What B used**: which reception passages and Targum readings reached the guide, and whether synthesis
  discovery's observations changed.
- Then the author reads both guides. N = 1 per arm: differences in style are mostly noise (S372).

## 3. Open decisions after the A/B

- Adopt `--reception` / `--targum` as defaults? Budget (1,400/verse, 40K cap) and tier C scope (Hasidut, Musar,
  halakhah) are the knobs.
- The Sacks rebuild (§3.3 of the evaluation doc; Ps 76 has no Sacks, so this A/B does not test it).
- The 350K trim ceiling: keep until Ps 78; measure the long psalms first (§6a).

## 4. Still open from Session 391's prompt

`NEXT_SESSION_PROMPT_session_391.md` §1 (the author's read of the Ps 77 echoes-v3 guide) and §4.
