# Micro agent: Sonnet 4.6 → Sonnet 5.5 (Session 394, 2026-10-02) — ADOPTED

**Decision (the author): `MicroAnalystV2.DEFAULT_MODEL = "claude-sonnet-5-5"`, Stage 1 adaptive thinking at
effort `xhigh`.** Session spend on the A/B ≈ $2.60. Earlier Sonnet 5 attempts (S362 Ps 65, S382 Ps 76) were
not adopted: `SONNET5_MICRO_AB_FINDINGS.md`.

## Ps 76 (micro stage only; three Sonnet 4.6 runs as the noise floor)

| | 4.6 (3 runs) | S5 xhigh | S5 max | **S5.5 high** | **S5.5 xhigh** | S5.5 max |
|---|--:|--:|--:|--:|--:|--:|
| cost | $0.53–0.66 | $0.35 | $1.21 | $0.19 | **$0.43** | ≈ $1.28, **no output** |
| wall clock | — | 6.4 min | 26.6 min | 1.7 min | **5.0 min** | 16 min → empty |
| lexical insights | 29–36 | 43 | 51 | 40 | **46** | — |
| chars per insight | 459–553 | 181 | 226 | 189 | 233 | — |
| figurative flags | 27–31 | 11 | 26 | 24 | **35** | — |
| questions | 10–11 | 12 | 16 | 8 | 11 | — |
| new phrase targets | 0–5 (vs the other two 4.6 runs) | 5 | 10 | 1 | 4 | — |

- **`max` thought through all 128K output tokens and wrote nothing** (as Opus 5.5 at `max` did in S384). The
  agent's empty-response retry repeated the identical request; stopped by hand. → The production ladder never
  goes above `xhigh` and steps DOWN (`xhigh` → `high` → `medium`) on an empty or cut-off answer.
- **`high`**: cheap and fast, but the S382 terseness: v. 11's crux summary is muddled.
- **`xhigh`, read against 4.6 Sep 30 on vv. 5, 6, 11**: sharper connections (טֶרֶף + מְעוֹנָה = Nah 2:12–13, an
  Assyria oracle, giving the LXX title "against the Assyrian" an internal basis; comparative מ in
  מֵהַרְרֵי־טָרֶף; אַדִּיר / אַבִּירֵי לֵב; the Edom/Hamath emendation with Isa 37:13; תּוֹדָה → v. 12's vows;
  תַּחְגֹּר / יִבְצֹר end-rhyme) and the best questions of any arm (שַׁלְּמוּ ↔ שָׁלֵם; YHWH once in an Elohistic
  psalm; עַנְוֵי אֶרֶץ). Less explanation per item (missed 4.6's אַתָּה build-up v. 5 → v. 8); one slip
  (אֶשְׁתּוֹלְלוּ "hapax"; Isa 59:15 has the hithpolel).

## Ps 77 (one Sonnet 4.6 run, S387, Sep 29)

| | 4.6 | **S5.5 xhigh** |
|---|--:|--:|
| cost | ≈ $0.90 (not recorded; estimate) | **$0.69** |
| wall clock | 16 min (Stage 1 alone) | **7.8 min** |
| lexical insights | 53 | **60** |
| chars per insight | 469 | 254 |
| figurative flags | 32 | **37** |
| questions | 12 | 12 |

New in 5.5: מַיִם רַבִּים (v. 20) → מֹשֶׁה (v. 21) via Ps 18:17 / Exod 2:10; עִקְּבוֹת ↔ Song 1:8 "tracks of the
flock" → v. 21's flock; "the psalmist's eyes never see; only the waters see" (v. 17); Exod 15:14's רגז + חיל
reassigned to the waters; Jer 10:19 and Deut 32:7–8 at the v. 11 crux; the v. 12 ketiv/qere אזכיר / אזכור as
public vs private memory. 4.6 explains more per item (v. 20's road/track/footprint scale). **Confounder**: the
4.6 run read Bolls' lemmatized Greek (its false "LXX: the psalmist listens" at v. 2); 5.5 read Brenton (S390).

## Not measured

The Stage-2 research requests (which concordance/lexicon searches run): the runner could not serialize the
request object, and the log truncates the raw JSON. A full pipeline run records them in the bundle.

## Files

`arm_s55_high/`, `arm_s55_xhigh/` (Ps 76), `ps77_arm_s55_xhigh/`, `max_arm_failed.log`, `scores.txt`,
`scores_ps77.txt`; `scripts/ab_micro_sonnet55.py` (shim runner; no production code touched) and
`scripts/score_micro_s55.py` (`python … 76 --list-new`). The 4.6 baselines stay in `output/psalm_76/`,
`output/psalm_76/_opus55_B/`, `output/_s391_reception_ab/psalm_76/A/psalm_76/`, `output/psalm_77/`.
