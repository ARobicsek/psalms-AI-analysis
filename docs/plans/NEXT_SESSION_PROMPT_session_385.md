# Next session (385) — start from the author's reading of the essay trials

## Where Session 384 left things
- **The author is reading** `Documents/Psalm study guide/Psalm 76 - Essay trials (S384).docx`. It has 11 essays under blind letters with the key on the last page, plus a companion file of the writers' reasoning. **Ask what they found before proposing anything.** They asked for descriptive reader's notes, not ratings. Do not produce AI rankings unless they ask.
- **Key**: A = P1 Sol high; B = REF-A (production Opus 5); C = P2 Opus high; D = P1 Opus high (second run); E = P0 Sol high; F = P1 Opus high; G = P1 Sol high (second run); H = P2 Sol high; I = P0 Opus high; J = P1 Sol xhigh; K = REF-B (all-Opus-5.5 run). The P1 Opus max arm produced nothing.
- **Artifacts**: `archive/psalm_76_S384_essay_trials/` (essays, notes, first readings, ideas map, metrics, ledger, prompts, and B's inputs block). Harness: `scripts/s384_essay_trials.py` (the "forest" prompt is `P1_INSTRUCTIONS`). Packet builder: `scripts/s384_build_packet.py`.
- **Shipped to production, but no full guide has run on it yet**: in-context lemma resolution, no alphabetical truncation, section-stratified concordance display, the shared-vocabulary radar section in every bundle, the honest methods line, the echo budget (~3 per 4 verses), GPT-6 Sol pricing, and the writer's refusal of `gpt-6-*`.

## Likely next steps (the author chooses)
1. **Take the winning essay approach into a full guide.** Extend the chosen prompt to the verse commentary: echo budget, "read like a poet", commentators demoted, deferral to the essay. Consider the essay-then-verses two-call structure the author suggested; the essay-only P1 is already the first call of it. Run on B's materials first, then on a fresh psalm.
2. **Ablate whatever won.** P1 bundled five changes: the essay task, the listening procedure, the whole-library mandate, commentator demotion, and no wit quota.
3. **Regenerate the Ps 76 bundle** with the fixed concordance and radar. Micro + assembler + SD cost ~$2–3. See whether synthesis discovery picks up Isa 31, Isa 43:17, Hos 1:7 and Gen 49. In the essays the radar did not surface them.
4. **Literary echoes v3** (deferred by the author): the ideas in `SESSION_384_PLAN_concordance_echoes_writer.md` §2.3. Byron's poem, which the current pipeline discards, appeared in 4 trial essays from model knowledge alone.
5. **SD-only on Opus 5.5** (S383's pending suggestion). B's SD was already on 5.5, so the trials used it.

## Gotchas measured in Session 384
- **Opus 5.5 at effort `max` burned 128K output tokens thinking and wrote nothing** (twice, ~$2.61 each). Use `high`.
- **Put instructions AFTER the inputs**, with a 1-hour `cache_control` on the inputs block. An extra Opus essay then costs ~$0.24; GPT-6 Sol ~$0.08 with `prompt_cache_key`.
- **GPT-6 Sol** needs the Responses API with explicit `reasoning.effort` (it reasons only ~2.5–5K tokens at `high`). One call returned `incomplete` with zero usage and succeeded on retry. It counts B's inputs at ~129K tokens, well under the 272K surcharge.
- **The concordance's COMMON_CAP (>120 hits drops a single-word search) now sees true totals and fires.** That is intended.
