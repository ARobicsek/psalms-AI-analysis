"""
Session 384 — Psalm 76 writer ESSAY trials (experimental; archive after the session).

Every arm reads arm B's EXACT inputs (the inputs block of B's saved writer prompt,
byte for byte) and writes only the INTRODUCTION ESSAY. Arms differ only in the
instructions. Design and prompt text: docs/plans/S384_writer_essay_prompt_DRAFT.md.

    P0  production prompt (current, incl. the S384 echo budget), production order,
        told to write the essay only
    P1  the "forest" rewrite (instructions AFTER the inputs)
    P2  P1 + two research-free "first readings" + the shared-vocabulary section

Models: claude-opus-5-5 (high; max) and gpt-6-sol (high; xhigh). Then descriptive
reader's notes on every essay (no scores), an ideas map, and metrics.

Writes ONLY under output/psalm_76/_S384_essays/. Resumable: a finished artifact is
never recomputed. Hard spend cap: no new call starts once the ledger passes it.

    python scripts/s384_essay_trials.py --dry-run     # build + check prompts, $0
    python scripts/s384_essay_trials.py               # run everything
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

import anthropic  # noqa: E402
import openai  # noqa: E402

from src.agents.master_editor import MASTER_WRITER_PROMPT_V4  # noqa: E402
from src.utils.cost_tracker import resolve_pricing  # noqa: E402

PSALM = 76
OUT = ROOT / "output" / "psalm_76" / "_S384_essays"
B_PROMPT = ROOT / "output/psalm_76/_opus55_B/_debug/master_writer_v4_prompt_psalm_76.txt"
REF_ESSAYS = {
    "REF-A (production, Opus 5)": ROOT / "output/psalm_76/psalm_076_edited_intro_pre_copy_edit.md",
    "REF-B (all-Opus-5.5 run)": ROOT / "output/psalm_76/_opus55_B/psalm_076_edited_intro_pre_copy_edit.md",
}
BUDGET_USD = 40.0
OPUS, SOL = "claude-opus-5-5", "gpt-6-sol"

# ---------------------------------------------------------------------------
# Prompt pieces
# ---------------------------------------------------------------------------

def _fill(fragment: str) -> str:
    return fragment.replace("{psalm_number}", str(PSALM)).replace("{{", "{").replace("}}", "}")


def split_saved_prompt(text: str):
    """(pre, inputs, task) of B's saved writer prompt. `inputs` runs from the
    '## YOUR INPUTS' heading to the separator line before '## YOUR TASK'."""
    a = text.index("## YOUR INPUTS")
    a = text.rfind("\n## ═", 0, a) + 1
    b = text.index("## YOUR TASK: WRITE THE COMMENTARY")
    b = text.rfind("\n## ═", 0, b) + 1
    return text[:a], text[a:b], text[b:]


def split_template(tpl: str):
    a = tpl.index("## YOUR INPUTS")
    a = tpl.rfind("\n## ═", 0, a) + 1
    b = tpl.index("## YOUR TASK: WRITE THE COMMENTARY")
    b = tpl.rfind("\n## ═", 0, b) + 1
    return _fill(tpl[:a]), _fill(tpl[b:])


def psalm_text_block(inputs: str) -> str:
    """Psalm text (Hebrew, English, LXX, phonetic) + the phonetic transcriptions,
    with no research — the only thing the first readings may see."""
    a = inputs.index("### PSALM TEXT (Hebrew, English, LXX, Phonetic)")
    b = inputs.index("### STRUCTURAL OVERVIEW")
    c = inputs.index("### PHONETIC TRANSCRIPTIONS")
    d = inputs.index("### KEY INSIGHTS TO INCORPORATE")
    return inputs[a:b].rstrip() + "\n\n" + inputs[c:d].rstrip() + "\n"


ESSAY_ONLY_OVERRIDE = """

---

## FOR THIS RUN — ESSAY ONLY

Write ONLY STAGE 1, the INTRODUCTION ESSAY. Do not write the liturgical section, the
verse-by-verse commentary, or the reader questions. Return exactly:

### INTRODUCTION ESSAY
[the essay]
"""

P1_INSTRUCTIONS = """## ═══════════════════════════════════════════════════════════════════════════
## YOUR TASK: THE INTRODUCTION ESSAY
## ═══════════════════════════════════════════════════════════════════════════

You have just been given everything a research pipeline could gather about Psalm 76: the text in Hebrew, English, Greek and transcription; a structural overview; verse notes; lexicon entries; concordance searches; figurative-language parallels; eleven traditional commentators on every verse; liturgical uses; related psalms; a reception-history report; literary echoes; and a set of cross-verse observations.{extra_inputs_note} Your task is to write the INTRODUCTION ESSAY of a study guide to this psalm.

## WHO YOU ARE WRITING AS

You read Hebrew poetry with a poet's ear and a scholar's precision — and with a range no single scholar has. You know the Bible in Hebrew and its commentators, but also the archives of the ancient Near East, the Greek and Latin classics, world poetry, history, music, the visual arts, anthropology, the psychology of religion and emotion, and philosophy. You are a frontier AI model: you have absorbed more of human culture than any person could read in several lifetimes. This guide exists to put that to use. The research above is what a pipeline could collect; your own knowledge is the larger library. Bring it.

Your reader is intelligent and curious, reads Hebrew, and is not a specialist. They read for their own education and delight, and they know what a routine commentary sounds like. Give them what they cannot get elsewhere.

## WHAT THE ESSAY IS FOR

A commentary explains a text. This essay shows the reader what the poem DOES — the experience it builds in someone who hears it, how it builds it, and why that matters — and then opens windows from the poem onto everything else it touches. It answers three questions, in this order of importance:

1. **What does this poem do to its hearer, and what is it for?** Follow it as an experience, moment by moment: what the listener sees, hears and feels first, and then next; where the camera stands and when it moves; who speaks to whom, and when that changes; where the poem is loud and where it goes quiet; what it withholds; where it turns. Then ask what it is meant to evoke — in whom, and when. Who needs this poem, and what does it give them? Name the effect in plain human terms. Your governing idea should be one a reader without Hebrew could feel.

2. **How does it do it?** The handful of artistic choices that produce that effect: repetitions (of words, roots, sounds), the grammar that swerves where prose would not (see READ LIKE A POET), pauses and silences, proportions (what gets three verses and what gets half a line), the order of things. Craft here is evidence for the experience — never a list of devices.

3. **What does it open onto?** Connections that make the poem newly visible: within the Bible (a text it answers, reverses, or quotes), in the world of its first audience (what they knew, saw and feared that we have lost), and far beyond — another poem, a piece of music, an artifact, a historical scene, a concept from another field that names what the poem is doing. See BRING THE WHOLE LIBRARY.

Most commentaries spend their energy on the second question and never reach the first. Spend yours on the first; use the second to prove it; let the third surprise.

## HOW TO WORK (your reasoning phase) — in this order

The order matters: it is what keeps the poem from disappearing under its apparatus.

1. **Listen first.** Before you consult the research, read the psalm three times in your head: once for the drama (who, where, what happens, in what order), once for its emotional arc (where the temperature changes), once for its oddities (anything a careful reader would stumble on). Write down, in your reasoning, your own reading of what the poem is doing — in a few plain sentences — before the dossier has a vote.{first_readings_step}

2. **Widen.** Ask what this poem resonates with, anywhere. List at least ten candidate connections from as many different domains as you can — biblical, ancient Near Eastern, classical, liturgical, literary, musical, visual, historical, psychological, philosophical — before judging any of them. Most will be discarded; the point of listing is to get past the first few that come to mind.

3. **Test and deepen with the research.** Now use the dossier to check your reading, correct it where it is wrong, and deepen it where it is thin. Look especially for anything in the research that contradicts your first reading — that is where the best essays come from. The cross-verse observations and the concordance material are rich in connections; the commentators are voices in a long conversation, worth quoting when one of them sees something (see COMMENTATORS).

4. **Choose.** Pick the governing idea and the few pieces of evidence and connection that make it land. Leave out much that is true.

Spend most of your reasoning on steps 1–3. Choosing which commentator to quote is a small decision; make it quickly while you draft.

## READ LIKE A POET

The grammarian's irregularity is often the poet's choice. Linger on:
- **Repetition** — the same word, root or sound returning; what changes between its appearances.
- **Swerves** — a conjunction with no grammatical job, a singular verb with a plural subject, a tense that shifts without warning, a possessive that is missing, a switch from speaking ABOUT God to speaking TO God (or back).
- **Silence and pause** — Selah, a line that stops short, an ending that refuses to resolve.
- **Proportion and order** — what gets room and what gets half a line; what comes first; what is saved for last.
- **Sound** — use the phonetic transcriptions when a sound pattern carries meaning.

For each, ask: what does it DO to a listener, and what would be lost if it were "corrected" into ordinary prose? Where the text does not compel a reading, offer it as a reading.

Three examples of the kind of move meant here — from other psalms, to show the move, never to be imitated in wording:
- Psalm 130: שֹׁמְרִים לַבֹּקֶר, שֹׁמְרִים לַבֹּקֶר, "those who watch for morning, who watch for morning." The repetition is not emphasis; it is the night getting longer. The line does to the reader what waiting does to the watchman.
- Psalm 1: the righteous get a whole tree — planted, watered, fruiting in season, its leaf unwithering; the wicked get half a verse and the one farm product that weighs nothing, chaff. The poem's proportions are its verdict.
- Psalm 23: the poem speaks ABOUT God ("He makes me lie down… He leads me") until the valley of deep darkness, and there, at the worst moment, turns to speak TO Him: כִּי אַתָּה עִמָּדִי, "for You are with me." You address the one you can no longer see.

## BRING THE WHOLE LIBRARY

The research dossier is a floor, not a ceiling. The essay should contain at least two connections that no standard Bible commentary would make — moves that come from your wider knowledge. Kinds of move that earn their place:
- **The first audience's world** — an artifact, inscription, custom, landscape or political fact that the poem's hearers lived with and we have forgotten, which changes what a line means.
- **The other side of the story** — how an enemy, a neighbor, or a later reader told or used the same events or images.
- **A mechanism from another art** — how a composer uses a rest, how a film cuts, how a painter frames a vista — when it EXPLAINS what the poem is doing, not merely resembles it.
- **A concept from another field** — psychology, anthropology, ritual studies, philosophy — that names precisely what the poem enacts.
- **The poem in a human mouth** — a documented moment when someone used these words, and what that moment reveals.
- **World literature** — see LITERARY ECHOES below.

Two tests for every such connection:
- **Does it explain, or only resemble?** After the comparison, the reader must see something in the Hebrew they could not see before. Resemblance alone is decoration; cut it.
- **Is it true?** State only what you know to be accurate, and name sources precisely (who, what, when). If you are unsure of a detail, say less rather than invent — a vivid falsehood destroys the reader's trust in everything else.

## THE INSIGHT TEST

Before you finish, ask of every paragraph: would a well-read rabbi learn something here? Would a well-read literary critic? If a sentence could appear in any standard commentary on this psalm, it is context — useful, brief, and never the point. The essay's point should be something the reader will remember the next time they hear this psalm.

## COMMENTATORS

The eleven traditional commentators are voices in a long conversation, not a checklist. Quote one when he sees something no one else does — a disagreement, a risk, a reading from outside the plain sense, something that changes how the verse reads. Never quote a commentator to restate the verse, or to sponsor an observation you made yourself. In an essay, a few well-chosen voices are plenty; none is fine if none changes the reading. Know what each is for: Minchat Shai is Masoretic text criticism (spelling, accents, variants) and has no opinion about meaning; Metzudat Zion is a bare glossary — use it silently, never cite it; Malbim's Beur Hamilot distinguishes near-synonyms; Romemot El (the Alshich) is homiletical and long, and always has something to say, which is not the same as having something that changes the reading; Chomat Anakh (the Chida) is sparse and speaks from outside the plain sense; Torah Temimah records where the rabbis mined a verse for law or aggadah — often the most distinctive material in the dossier.

## LITERARY ECHOES

The Cross-Cultural Literary Echoes research holds passages from world literature chosen for this psalm. Use the strongest of them where they serve the argument — one to three in the essay is a natural range — and add others you know that fit better. Every quotation in that research was gathered from published, openly available sources, and this guide is a private study text written for one reader's own education; quotation in the service of commentary is its whole purpose. Do not trim a passage below what the comparison needs out of caution: quote the lines that carry the echo — typically 3–8 lines of verse (or 2–4 sentences of prose) — in the original language with English translation; for public-domain works (ancient, medieval, and anything published before about 1930) quote as much as illuminates; for modern works, the passage the dossier supplies is the passage to use. Frame the source for the reader (who, when, under what circumstances), and after quoting, unfold the resonance: what is genuinely parallel, what differs, and what the difference reveals about each.

Set a quoted poem lineated inside a block quote, one `> ` line per line of verse, the original first, then a bare `>`, then the translation lineated to match.

## WRITING

- **Hebrew and English always together.** Every Hebrew word or quotation carries its translation, and every translation its Hebrew. The translation is part of the sentence, not a floating annotation: *The psalm ends with יֵשַׁע אֱלֹקִים, "the salvation of God"* or *God "made the mountain stand" (הֶעֱמַדְתָּה)* — never *יֵשַׁע אֱלֹקִים ("the salvation of God")*. Never put Hebrew (or Greek) inside quotation marks; only the English carries quotes.
- **Transliteration** only when a sound pattern matters, using the supplied transcriptions.
- **Plain words.** Define in the same breath any term an ordinary educated adult might not know, by showing the thing ("the single letter ו in front of אַתָּה — the 'but' that turns the sentence"). When your point rests on a prefix or suffix, bold the exact letters inside the Hebrew. No linguistics jargon (deixis, paratactic, polyptoton, and the like).
- **Show the step.** When you report that someone derived something from the text, show the move that got them there.
- **No false profundity.** A real insight survives being said flatly; if a balanced, cadenced sentence only restates what the reader already knows, cut it. This assignment invites grandeur — resist it: name the poem's effect precisely, don't gush. No "masterpiece," "breathtaking," "stunning," "tapestry."
- **Don't try to be funny.** If the material itself is dry-funny, a flat sentence will show it.
- **Paragraphs, not lists.** No bullet lists. At most two or three section headings, and only if the essay truly has movements.
- **You are the author.** Never refer to "the research," "the dossier," "the observations," "the first readings," or anything that reveals the pipeline behind you. Present every insight as your own.
- **One plain place.** At the psalm's emotional center you may, once, speak plainly about what this feels like from the inside — no device named, no source cited.

## LENGTH AND SHAPE

1,200–2,000 words. Open with something that makes the reader want to hear the poem again — not a summary. Somewhere early, let the reader see the poem's shape, in prose. End with the one thing you most want the reader to carry away.

## OUTPUT

Return exactly:

### INTRODUCTION ESSAY
[the essay]
"""

P2_EXTRA_NOTE = (" You have also been given two FIRST READINGS of the poem, each made from the "
                 "text alone with no research, and a computed list of SHARED-VOCABULARY PARALLELS "
                 "found by searching every verse of the Bible.")
P2_STEP = (" Then compare your reading with the two first readings; keep what survives, "
           "and notice where they see something you did not.")

FIRST_READING_PROMPT = """Below is Psalm 76 — Hebrew, an English translation, the Greek Septuagint, and a phonetic transcription. Nothing else: no commentary, no research.

{psalm_text}

---

Read it as a poem, several times, and write a FIRST READING of 700–1,000 words in plain, precise prose (no bullet lists):

- what happens in it, moment by moment, to someone who hears it — what they see and hear first and next, where the camera stands and when it moves, who speaks to whom and when that changes, where it is loud and where it goes quiet, where it turns;
- what it is meant to evoke, in whom, and when — who needs this poem, and what it gives them;
- the oddities a careful reader stumbles on — repetitions, grammar that swerves, pauses (Selah), proportions — and what each does to a listener;
- what it resonates with outside the Bible, in at least five different domains (history, archaeology, art, music, literature, psychology, ritual, philosophy…), with a sentence on what each connection EXPLAINS about the poem. State only what you know to be accurate.

Write for a curious, intelligent reader who knows Hebrew; when you quote Hebrew, give the English with it. This is your own reading, not a summary of scholarship.

Return only the reading, under the heading:
### FIRST READING
"""

NOTES_PROMPT = """You are a careful, widely read reader giving notes on an essay about Psalm 76, for a person who will read the essay themselves and wants help seeing what is in it. DESCRIBE; DO NOT GRADE. No scores, no ranking, no verdict on overall quality, no comparison with any other essay.

The psalm, for reference:

{psalm_text}

---

The essay ("Essay {label}"):

{essay}

---

Write at most 400 words, under exactly these headings:

**Governing idea** — one sentence, in your own words.
**What it says the poem does and evokes** — two or three sentences.
**Strongest insights** — up to five, each quoted briefly (a phrase or a sentence) and tagged [Bible], [beyond the Bible], [poetic craft] or [tradition].
**Best writing** — one or two sentences quoted exactly.
**Weak spots** — anything confusing, padded, overwrought, repetitive, or attempting wit that does not land. Quote briefly.
**Claims worth checking** — any factual claim (a citation, a quotation, a date, a historical or archaeological fact) that looks doubtful or that you cannot confirm, and why. If none, write "None noticed."
"""

IDEAS_MAP_PROMPT = """Below are {n} essays on Psalm 76, labeled by letter. Build a MAP OF THEIR IDEAS. This is descriptive: do not judge quality, do not rank, do not say which essay is better.

List every distinct substantive idea that appears in at least one essay — a reading of what the poem does or evokes, a structural or poetic-craft observation, a biblical intertext, a connection beyond the Bible (history, artifact, art, music, literature, psychology, liturgy, reception) — merging ideas that are the same in different words. For each, give a one-line description, a category, and the letters of every essay that contains it.

Output three markdown sections:
1. `## Ideas map` — a table `| Idea | Category | Essays |`, grouped by category, and within each category ordered from the idea found in the MOST essays to the idea found in only one.
2. `## Found in only one essay` — a list: letter, then the idea, one line each.
3. `## What each essay is built around` — one line per essay: its letter and its governing idea in a sentence.

{essays}
"""

# ---------------------------------------------------------------------------
# API plumbing
# ---------------------------------------------------------------------------

_ledger_lock = threading.Lock()
LEDGER_PATH = OUT / "ledger.json"


def _load_ledger() -> dict:
    if LEDGER_PATH.exists():
        return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    return {"calls": []}


def spent() -> float:
    return round(sum(c["cost_usd"] for c in _load_ledger()["calls"]), 4)


def _record(entry: dict) -> None:
    with _ledger_lock:
        led = _load_ledger()
        led["calls"].append(entry)
        LEDGER_PATH.write_text(json.dumps(led, ensure_ascii=False, indent=2), encoding="utf-8")


def _cost(model: str, u: dict) -> float:
    p = resolve_pricing(model)
    if p is None:
        raise KeyError(f"unpriced model {model}")
    m = 1_000_000
    return (u.get("input", 0) * p["input"] + u.get("cache_write_1h", 0) * p["cache_write_1h"]
            + u.get("cache_write", 0) * p["cache_write"] + u.get("cache_read", 0) * p["cache_read"]
            + u.get("output", 0) * p["output"]) / m


class OverBudget(RuntimeError):
    pass


def _check_budget(label: str) -> None:
    if spent() >= BUDGET_USD:
        raise OverBudget(f"budget ${BUDGET_USD} reached before '{label}' (spent ${spent()})")


_anth = anthropic.Anthropic(max_retries=4)
_oai = openai.OpenAI(timeout=3600.0, max_retries=3)


def call_opus(label: str, blocks: list, effort: str, cache_first_block: bool) -> dict:
    """blocks: list of text strings forming one user message. The first block is
    cached for 1h when cache_first_block (the shared inputs)."""
    _check_budget(label)
    content = []
    for i, b in enumerate(blocks):
        item = {"type": "text", "text": b}
        if i == 0 and cache_first_block:
            item["cache_control"] = {"type": "ephemeral", "ttl": "1h"}
        content.append(item)
    last_err = None
    for attempt in range(3):
        try:
            text, thinking = "", ""
            t0 = time.time()
            with _anth.messages.stream(
                model=OPUS, max_tokens=128000,
                thinking={"type": "adaptive", "display": "summarized"},
                output_config={"effort": effort},
                messages=[{"role": "user", "content": content}],
            ) as stream:
                for ev in stream:
                    if getattr(ev, "type", "") == "content_block_delta":
                        if hasattr(ev.delta, "text"):
                            text += ev.delta.text
                        elif hasattr(ev.delta, "thinking"):
                            thinking += ev.delta.thinking
                msg = stream.get_final_message()
            us = msg.usage
            cc = getattr(us, "cache_creation", None)
            w1h = getattr(cc, "ephemeral_1h_input_tokens", 0) if cc else 0
            w5m = getattr(cc, "ephemeral_5m_input_tokens", 0) if cc else 0
            if not cc:
                w1h = getattr(us, "cache_creation_input_tokens", 0) or 0
            u = {"input": us.input_tokens, "cache_write_1h": w1h, "cache_write": w5m,
                 "cache_read": getattr(us, "cache_read_input_tokens", 0) or 0,
                 "output": us.output_tokens}
            cost = _cost(OPUS, u)
            _record({"label": label, "model": OPUS, "effort": effort, "usage": u,
                     "cost_usd": round(cost, 4), "seconds": round(time.time() - t0),
                     "stop_reason": msg.stop_reason})
            if not text.strip():
                raise RuntimeError(f"empty response (stop_reason={msg.stop_reason})")
            return {"text": text, "thinking": thinking, "usage": u, "cost": cost,
                    "stop_reason": msg.stop_reason}
        except OverBudget:
            raise
        except Exception as e:  # content filter / overload / network: retry
            last_err = e
            print(f"  [{label}] attempt {attempt + 1} failed: {str(e)[:200]}", flush=True)
            time.sleep(15 * (attempt + 1))
    raise RuntimeError(f"{label}: all attempts failed: {last_err}")


def call_sol(label: str, blocks: list, effort: str) -> dict:
    _check_budget(label)
    last_err = None
    for attempt in range(3):
        try:
            t0 = time.time()
            r = _oai.responses.create(
                model=SOL,
                input=[{"role": "user", "content": [{"type": "input_text", "text": b} for b in blocks]}],
                reasoning={"effort": effort, "summary": "auto"},
                max_output_tokens=100000,
                prompt_cache_key="s384-ps76-essay-trials",
            )
            us = r.usage
            cached = getattr(getattr(us, "input_tokens_details", None), "cached_tokens", 0) or 0
            reasoning = getattr(getattr(us, "output_tokens_details", None), "reasoning_tokens", 0) or 0
            u = {"input": us.input_tokens - cached, "cache_read": cached, "output": us.output_tokens,
                 "reasoning_included": reasoning}
            cost = _cost(SOL, u)
            summary = "\n\n".join(s.text for it in r.output if it.type == "reasoning"
                                  for s in (it.summary or []))
            inc = getattr(r, "incomplete_details", None)
            _record({"label": label, "model": SOL, "effort": effort, "usage": u,
                     "cost_usd": round(cost, 4), "seconds": round(time.time() - t0),
                     "status": r.status,
                     "incomplete_reason": getattr(inc, "reason", None) if inc else None})
            text = r.output_text or ""
            if r.status != "completed" or not text.strip():
                raise RuntimeError(f"status={r.status}, text chars={len(text)}")
            return {"text": text, "thinking": summary, "usage": u, "cost": cost, "stop_reason": r.status}
        except OverBudget:
            raise
        except Exception as e:
            last_err = e
            print(f"  [{label}] attempt {attempt + 1} failed: {str(e)[:200]}", flush=True)
            time.sleep(15 * (attempt + 1))
    raise RuntimeError(f"{label}: all attempts failed: {last_err}")


def call(model: str, label: str, blocks: list, effort: str, cache: bool = True) -> dict:
    return call_opus(label, blocks, effort, cache) if model == OPUS else call_sol(label, blocks, effort)


def extract_after(text: str, heading: str) -> str:
    i = text.find(heading)
    return (text[i + len(heading):] if i >= 0 else text).strip()


# ---------------------------------------------------------------------------
# Build the prompts
# ---------------------------------------------------------------------------

def build():
    saved = B_PROMPT.read_text(encoding="utf-8")
    saved_pre, inputs, saved_task = split_saved_prompt(saved)
    cur_pre, cur_task = split_template(MASTER_WRITER_PROMPT_V4)
    checks = {
        "saved_prompt_chars": len(saved),
        "inputs_chars": len(inputs),
        "pre_unchanged_since_B": saved_pre == cur_pre,
        "task_changed_since_B (echo budget)": saved_task != cur_task,
        "inputs_starts": inputs[:60],
        "inputs_ends": inputs[-80:],
    }
    # P0 = what production would send TODAY: B's saved task section (which already has
    # the runtime reader-question stripping applied) with the S384 echo edits spliced in
    # from the current template (item 7, and item 12 through its "Quote enough" bullet).
    def _item7(s):
        return re.search(r"(?m)^7\. \*\*Cross-cultural resonance.*$", s).group(0)

    def _item12(s):
        return re.search(r"(?ms)^12\. \*\*Cross-Cultural Literary Echoes.*?^   - \*\*Quote enough of the source.*?$", s).group(0)

    task = saved_task.replace(_item7(saved_task), _item7(cur_task))
    task = task.replace(_item12(saved_task), _item12(cur_task))
    assert "BUDGET: about three echoes" in task and "QUOTE FULSOMELY" in task
    assert "sparingly, only when strong" not in task and "READER QUESTIONS" not in task
    checks["p0_task_delta_chars"] = len(task) - len(saved_task)
    p0 = cur_pre + inputs + task + ESSAY_ONLY_OVERRIDE
    p1 = P1_INSTRUCTIONS.replace("{extra_inputs_note}", "").replace("{first_readings_step}", "")
    p2 = P1_INSTRUCTIONS.replace("{extra_inputs_note}", P2_EXTRA_NOTE).replace("{first_readings_step}", P2_STEP)
    return {"inputs": inputs, "p0": p0, "p1": p1, "p2": p2,
            "psalm_text": psalm_text_block(inputs), "checks": checks}


ARMS = [  # (arm_id, prompt, model, effort)
    ("P0_opus_high", "p0", OPUS, "high"),
    ("P0_sol_high", "p0", SOL, "high"),
    ("P1_opus_high_r1", "p1", OPUS, "high"),
    ("P1_sol_high_r1", "p1", SOL, "high"),
    ("P1_opus_high_r2", "p1", OPUS, "high"),
    ("P1_sol_high_r2", "p1", SOL, "high"),
    ("P1_opus_max", "p1", OPUS, "max"),
    ("P1_sol_xhigh", "p1", SOL, "xhigh"),
    ("P2_opus_high", "p2", OPUS, "high"),
    ("P2_sol_high", "p2", SOL, "high"),
]


def run_essay(arm, P, extra_inputs: str) -> None:
    arm_id, pkey, model, effort = arm
    d = OUT / "essays" / arm_id
    if (d / "essay.md").exists():
        print(f"[skip] {arm_id}", flush=True)
        return
    d.mkdir(parents=True, exist_ok=True)
    if pkey == "p0":
        blocks = [P["p0"]]
        cache = False
    elif pkey == "p1":
        blocks = [P["inputs"], P["p1"]]
        cache = True
    else:
        blocks = [P["inputs"], extra_inputs, P["p2"]]
        cache = True
    print(f"[start] {arm_id} ({model}, {effort})", flush=True)
    res = call(model, arm_id, blocks, effort, cache)
    (d / "raw_response.md").write_text(res["text"], encoding="utf-8")
    (d / "thinking_summary.txt").write_text(res["thinking"] or "", encoding="utf-8")
    essay = extract_after(res["text"], "### INTRODUCTION ESSAY")
    essay = essay.split("---LITURGICAL-SECTION-START---")[0].strip()
    (d / "essay.md").write_text(essay, encoding="utf-8")
    (d / "meta.json").write_text(json.dumps({"arm": arm_id, "prompt": pkey, "model": model,
                                             "effort": effort, "usage": res["usage"],
                                             "cost_usd": round(res["cost"], 4),
                                             "stop_reason": res["stop_reason"],
                                             "words": len(essay.split())}, indent=2), encoding="utf-8")
    print(f"[done] {arm_id}: {len(essay.split())} words, ${res['cost']:.3f} (total ${spent()})", flush=True)


def run_first_reading(model: str, effort: str, P) -> str:
    tag = "opus" if model == OPUS else "sol"
    f = OUT / "first_readings" / f"first_reading_{tag}.md"
    if f.exists():
        return f.read_text(encoding="utf-8")
    f.parent.mkdir(parents=True, exist_ok=True)
    print(f"[start] first reading ({model}, {effort})", flush=True)
    res = call(model, f"first_reading_{tag}", [FIRST_READING_PROMPT.replace("{psalm_text}", P["psalm_text"])],
               effort, cache=False)
    text = extract_after(res["text"], "### FIRST READING")
    f.write_text(text, encoding="utf-8")
    (f.parent / f"first_reading_{tag}_thinking.txt").write_text(res["thinking"] or "", encoding="utf-8")
    print(f"[done] first reading {tag}: {len(text.split())} words", flush=True)
    return text


def p2_extra_inputs(fr_opus: str, fr_sol: str) -> str:
    from src.concordance.intertext_radar import compute_shared_vocabulary_parallels
    radar, _ = compute_shared_vocabulary_parallels(PSALM)
    return ("## ═══════════════════════════════════════════════════════════════════════════\n"
            "## ADDITIONAL INPUTS\n"
            "## ═══════════════════════════════════════════════════════════════════════════\n\n"
            "### TWO FIRST READINGS (each made from the poem alone, before any research)\n\n"
            "#### First reading 1\n\n" + fr_opus.strip() + "\n\n"
            "#### First reading 2\n\n" + fr_sol.strip() + "\n\n"
            + radar.replace("## Shared-Vocabulary Parallels (computed)",
                            "### SHARED-VOCABULARY PARALLELS (computed over every verse of the Bible)")
            + "\n")


# ---------------------------------------------------------------------------
# Reader's notes, ideas map, metrics
# ---------------------------------------------------------------------------

def essay_set() -> dict:
    """label-agnostic dict: name -> essay text (trial arms + the two references)."""
    out = {}
    for arm_id, *_ in ARMS:
        f = OUT / "essays" / arm_id / "essay.md"
        if f.exists():
            out[arm_id] = f.read_text(encoding="utf-8")
    for name, path in REF_ESSAYS.items():
        out[name] = path.read_text(encoding="utf-8").split("---LITURGICAL-SECTION-START---")[0].strip()
    return out


def blind_key(names) -> dict:
    kf = OUT / "blind_key.json"
    if kf.exists():
        key = json.loads(kf.read_text(encoding="utf-8"))
        if set(key.values()) >= set(names):
            return key
    names = sorted(names)
    random.Random(384).shuffle(names)
    key = {chr(ord("A") + i): n for i, n in enumerate(names)}
    kf.write_text(json.dumps(key, ensure_ascii=False, indent=2), encoding="utf-8")
    return key


def run_notes(letter: str, essay: str, model: str, P) -> None:
    tag = "opus" if model == OPUS else "sol"
    f = OUT / "notes" / f"{letter}_{tag}.md"
    if f.exists():
        return
    f.parent.mkdir(parents=True, exist_ok=True)
    prompt = (NOTES_PROMPT.replace("{psalm_text}", P["psalm_text"])
              .replace("{essay}", essay).replace("{label}", letter))
    res = call(model, f"notes_{letter}_{tag}", [prompt], "high", cache=False)
    f.write_text(res["text"].strip(), encoding="utf-8")
    print(f"[done] notes {letter} ({tag})", flush=True)


def run_ideas_map(key: dict, essays: dict) -> None:
    f = OUT / "ideas_map.md"
    if f.exists():
        return
    body = "\n\n".join(f"=== ESSAY {L} ===\n\n{essays[n]}" for L, n in sorted(key.items()))
    prompt = IDEAS_MAP_PROMPT.replace("{n}", str(len(key))).replace("{essays}", body)
    res = call(SOL, "ideas_map", [prompt], "high", cache=False)
    f.write_text(res["text"].strip(), encoding="utf-8")
    print("[done] ideas map", flush=True)


BIBLE_REF = re.compile(
    r"\b(Gen|Genesis|Exod|Exodus|Lev|Num|Deut|Josh|Judg|Sam|Kgs|Kings|Isa|Isaiah|Jer|Jeremiah|Ezek|"
    r"Ezekiel|Hos|Hosea|Joel|Amos|Obad|Jonah|Mic|Micah|Nah|Nahum|Hab|Habakkuk|Zeph|Hag|Zech|"
    r"Zechariah|Mal|Ps|Pss|Psalm|Psalms|Prov|Job|Song|Ruth|Lam|Eccl|Esth|Dan|Ezra|Neh|Chr|Chron)"
    r"\.?\s+\d+:\d+")
COMMENTATORS = ["Rashi", "Ibn Ezra", "Radak", "Meiri", "Alshich", "Romemot El", "Minchat Shai",
                "Metzudat", "Chida", "Chomat Anakh", "Malbim", "Torah Temimah", "Targum"]
DOSSIER_ECHOES = ["Hughes", "Marinetti", "Kaminsky", "Yannai", "Su Shi", "Margolin", "Da Ponte",
                  "Trakl", "Jarrell", "Paz", "Tussman", "Pavese", "Tukaram", "Hamer",
                  "ibn Mar Saul", "Khaqani", "Senghor", "Darío", "Dario"]


def metrics(text: str) -> dict:
    lines = text.splitlines()
    return {
        "words": len(text.split()),
        "headings": sum(1 for l in lines if l.lstrip().startswith("#")),
        "bullet_lines": sum(1 for l in lines if re.match(r"^\s*([-*•]|\d+\.)\s", l)),
        "bible_refs_distinct": len(set(m.group(0) for m in BIBLE_REF.finditer(text))),
        "commentator_mentions": sum(text.count(c) for c in COMMENTATORS),
        "dossier_echoes_used": sorted({e for e in DOSSIER_ECHOES if e in text}),
        "block_quote_lines": sum(1 for l in lines if l.startswith(">")),
        "selah_mentions": len(re.findall(r"Selah|סֶלָה|סלה", text)),
    }


# ---------------------------------------------------------------------------

def main() -> int:
    global BUDGET_USD
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--budget", type=float, default=BUDGET_USD)
    args = ap.parse_args()
    BUDGET_USD = args.budget
    OUT.mkdir(parents=True, exist_ok=True)
    P = build()
    (OUT / "prompts").mkdir(exist_ok=True)
    for k in ("p0", "p1", "p2"):
        (OUT / "prompts" / f"{k}_instructions.txt").write_text(P[k] if k != "p0" else P[k][-30000:], encoding="utf-8")
    (OUT / "prompts" / "inputs_block.txt").write_text(P["inputs"], encoding="utf-8")
    print(json.dumps(P["checks"], ensure_ascii=False, indent=2))
    assert P["checks"]["pre_unchanged_since_B"], "rules section drifted since B — investigate"
    if args.dry_run:
        print(f"P0 {len(P['p0']):,} chars; P1 instr {len(P['p1']):,}; P2 instr {len(P['p2']):,}; "
              f"psalm text {len(P['psalm_text']):,}")
        return 0

    t0 = time.time()
    try:
        with ThreadPoolExecutor(max_workers=6) as ex:
            # Wave 1: cache-warming P1 per model, both P0s, both first readings.
            futs = {
                "opus_r1": ex.submit(run_essay, ARMS[2], P, ""),
                "sol_r1": ex.submit(run_essay, ARMS[3], P, ""),
                "p0o": ex.submit(run_essay, ARMS[0], P, ""),
                "p0s": ex.submit(run_essay, ARMS[1], P, ""),
                "fro": ex.submit(run_first_reading, OPUS, "high", P),
                "frs": ex.submit(run_first_reading, SOL, "xhigh", P),
            }
            fr_opus, fr_sol = futs["fro"].result(), futs["frs"].result()
            extra = p2_extra_inputs(fr_opus, fr_sol)
            (OUT / "prompts" / "p2_extra_inputs.txt").write_text(extra, encoding="utf-8")
            futs["opus_r1"].result()
            wave2 = [ex.submit(run_essay, a, P, extra) for a in ARMS if a[2] == OPUS and a[0] not in
                     ("P0_opus_high", "P1_opus_high_r1")]
            futs["sol_r1"].result()
            wave2 += [ex.submit(run_essay, a, P, extra) for a in ARMS if a[2] == SOL and a[0] not in
                      ("P0_sol_high", "P1_sol_high_r1")]
            for f in wave2 + [futs["p0o"], futs["p0s"]]:
                try:
                    f.result()
                except Exception as e:
                    print(f"[FAILED] {e}", flush=True)
                    traceback.print_exc()
        essays = essay_set()
        key = blind_key(essays.keys())
        inv = {v: k for k, v in key.items()}
        with ThreadPoolExecutor(max_workers=6) as ex:
            jobs = [ex.submit(run_notes, inv[n], t, m, P) for n, t in essays.items() for m in (OPUS, SOL)]
            jobs.append(ex.submit(run_ideas_map, key, essays))
            for j in jobs:
                try:
                    j.result()
                except Exception as e:
                    print(f"[FAILED] {e}", flush=True)
    except OverBudget as e:
        print(f"[STOPPED] {e}", flush=True)
    essays = essay_set()
    m = {n: metrics(t) for n, t in essays.items()}
    (OUT / "metrics.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nALL DONE in {round((time.time() - t0) / 60)} min. Spent ${spent()}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
