# Psalm 76 essay trials: the author's blind reading and what it showed (Session 385)

## The author's verdict (blind, before seeing the key)

> Best: F (prob best overall though it mis-explains a Rashi a bit), C
> Middle group: I=J<K<H<D
> Weaker: A, E, B, G
> "I would take the middle and weaker groups as a very approximate ranking… But the best were considerably better than the others."

| Letter | Arm | Model / effort | Words | Group |
|---|---|---|---|---|
| F | P1 forest, run 1 | Opus 5.5 high | 1,987 | **Best** |
| C | P2 forest + first readings + radar | Opus 5.5 high | 2,055 | **Best** |
| D | P1 forest, run 2 | Opus 5.5 high | 1,898 | Middle (top) |
| H | P2 | GPT-6 Sol high | 1,412 | Middle |
| K | REF-B: the all-5.5 guide's essay (production prompt, full guide) | Opus 5.5 high | 1,446 | Middle |
| I | P0 production instructions, essay only | Opus 5.5 high | 1,435 | Middle (low) |
| J | P1 | GPT-6 Sol xhigh | 1,542 | Middle (low) |
| A | P1, run 1 | GPT-6 Sol high | 1,591 | Weaker |
| E | P0 | GPT-6 Sol high | 1,014 | Weaker |
| B | REF-A: the production guide's essay (A's dossier) | Opus 5 | 1,185 | Weaker |
| G | P1, run 2 | GPT-6 Sol high | 1,668 | Weaker |

## Findings

1. **The forest instructions won on Opus.** I, F and D share the model, effort and inputs, and differ only in the instructions. I landed in the middle group, and F and D in the top three. Carving the essay into its own call did not help by itself: I (production instructions, essay only) ranks with K (the same model writing the full guide). **Confound:** P0 allows 800–1,400 words and P1 allows 1,200–2,000. Opus hit the ceiling both times, and the extra ~500 words is where Herodotus, Byron and the Talmud went. Length alone does not explain the result, because A and G ran ~1,600–1,700 words and landed at the bottom.
2. **Opus 5.5 is much stronger than GPT-6 Sol here.** The top three are all Opus. Both P1 Sol-high runs are in the weakest group, and xhigh (J) only reached the middle. The "your knowledge is the larger library" mandate depends on the model. Opus's research-free first reading named specific works: Herodotus 2.141, the Lachish reliefs, Resheph, Byron and the Black Obelisk. Sol's gave only categories ("as in a painting of abandoned arms…", "music offers an analogy…"). Sol also hedges 2–3× more per word (3.8–5.8 hedges per 1,000 words vs 0.5–2.5), but hedging does not predict the order among the Sol essays.
3. **The best outside material was about the same night, not an analogy.** F, C and D triangulate the event from Sennacherib's prism (Hezekiah "like a bird in a cage"; the king's terrifying radiance), Herodotus's mice and Byron's *Destruction of Sennacherib*. **None of the top three quoted a poem from the literary-echoes dossier. All five essays that did are in the lower half:** I (Da Ponte), J (Su Shi), A (Paz), B (Hughes), G (Trakl). Byron was not in the dossier, because the echoes pipeline records it as "Default bypassed" and throws it away. This is correlational and confounded with model and prompt, since the Sol and P0 essays are the ones that leaned on the dossier. It still supports the deferred echoes item: aptness over novelty (`SESSION_384_PLAN_concordance_echoes_writer.md` §2.3).
4. **Demoting commentators made Opus cite them more, and better.** Commentator mentions went from 3 (P0) to 6–8 (P1/P2). The winning essays use commentators as readers who noticed something: Malbim on horses staying alert at night; Malbim Beur Hamilot on a human rebuke waking a sleeper while God's puts the waking to sleep; b. Shabbat 88a's "first it feared, then it was still". The cost is **F's Rashi on 76:11**. Rashi gives ONE continuous reading: human fury ends in praise (Nebuchadnezzar, Dan 3:28), *and thereby* the remaining fury is restrained (תחגר in the Mishnah's sense of a knife-nick that "catches" the nail). Then he gives an alternative, the literal girding: it befits You to gird on wrath. F presents the two halves of the first reading as two alternatives and drops the girding reading. F's thinking had it right ("עכבה as 'restrain,' tied to Nebuchadnezzar's praise"), so the slip came in drafting, not in reading. H (Sol) gets it right. If the forest prompt goes to production, it needs a cheap commentator-attribution check downstream, not RULE 8b back.
5. **P2's first readings transferred ideas, and the radar had no visible effect.** C's distinctive material (Black Obelisk, Adam's sleep, combat freeze) is all in Opus's first reading. F found Herodotus, Byron and the prism without it, so on Opus P2 ≈ P1. H, the only Sol essay to quote Byron, got it from Opus's first reading, and H is the best Sol essay. So P2 mainly lent Opus's ideas to Sol.
6. **Run-to-run variance is real, but the prompt effect is bigger than it.** F and D are the same arm and landed in different groups, so a single run per arm cannot rank arms finely. Even so, all three forest-Opus runs beat I, both production references, and every Sol run. K (5.5 guide) > B (production Opus 5 guide) agrees with S383's originality verdict. It contradicts S383's own read that A's essay was the better-written one.
