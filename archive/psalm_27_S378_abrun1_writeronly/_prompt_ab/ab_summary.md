# Writer PROMPT A/B/C — Psalm 27

Model is fixed; only the prompt differs between arms. All upstream artifacts
(macro, micro, dossier, synthesis discovery) are shared.

| arm | prompt Δchars | cost | in tok | out tok | words | intro w | verses w | secs |
|---|---|---|---|---|---|---|---|---|
| Baseline | +0 | $1.7517 | 194049 | 31259 | 7,562 | 1,814 | 5,748 | 549.1 |
| no analytical framework | -80 | $1.7427 | 188679 | 31971 | 7,547 | 1,743 | 5,804 | 583.0 |

**vs baseline:**

- no analytical framework: words 1.00x (-15), output tokens 1.02x, cost $-0.01
