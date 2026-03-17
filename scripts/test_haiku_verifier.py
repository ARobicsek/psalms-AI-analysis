"""
Haiku-Based Citation Verifier — Prototype Exploration (Session 310)

Tests whether Claude Haiku 4.5 can:
  1. Identify Hebrew quotations that claim to be direct biblical citations
  2. After DB lookup, judge whether mismatches are real errors or false positives

Usage:
    python scripts/test_haiku_verifier.py 41
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import anthropic
from dotenv import load_dotenv

load_dotenv()

from src.data_sources.tanakh_database import TanakhDatabase
from src.utils.scripture_verifier import (
    _resolve_book_name,
    _normalize_hebrew,
    _strip_to_consonants,
    _HEBREW_WORD_RE,
    MIN_HEBREW_WORDS,
)

# Haiku 4.5 pricing (per million tokens)
HAIKU_PRICING = {
    "input": 0.80,
    "output": 4.00,
}
HAIKU_MODEL = "claude-haiku-4-5-20251001"


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in dollars."""
    return (
        (input_tokens / 1_000_000) * HAIKU_PRICING["input"]
        + (output_tokens / 1_000_000) * HAIKU_PRICING["output"]
    )


# -------------------------------------------------------------------------
# Step 1: Ask Haiku to identify all Hebrew quotations with citations
# -------------------------------------------------------------------------

STEP1_SYSTEM = """You are a Hebrew scripture citation extractor. You read scholarly psalm commentary and identify instances where the author quotes a PHRASE (3+ words) of Hebrew text and attributes it to a specific biblical verse via a parenthetical citation like (Ex 20:7) or (Gen 27:36).

IMPORTANT RULES:
- ONLY extract quotations of 3+ Hebrew words that are paired with a parenthetical biblical reference
- Do NOT extract single-word definitions or glosses (e.g. דָּל meaning "depleted")
- Do NOT extract Hebrew words that are from the psalm being discussed (self-references)
- Do NOT extract liturgical/piyyut Hebrew that happens to appear near a biblical citation in a different clause
- Be precise: if Hebrew text is from a piyyut and a biblical reference appears in the NEXT sentence, those are NOT connected

CRITICAL: Copy the Hebrew text EXACTLY as it appears in the document, character for character.
Do NOT correct, fix, or normalize the Hebrew in any way. If the author wrote a word
incorrectly or omitted a word, copy it exactly as written. The whole point of this
extraction is to verify whether the author quoted correctly — if you "fix" the quote,
we cannot detect errors.

For each quotation, output a COMPACT JSON object: {"h":"<hebrew>","r":"<ref>","t":"d|p|l|a|e"}
Types: d=direct_quote, p=partial_quote, l=liturgical, a=allusion, e=editorial_mention

Output ONLY a JSON array. Keep it compact — no extra whitespace, no context field."""

STEP1_USER = """Identify all Hebrew scripture quotations with their biblical citations in this psalm commentary. Output ONLY a JSON array — no other text.

{text}"""


# -------------------------------------------------------------------------
# Step 2: Ask Haiku to judge matches after DB lookup
# -------------------------------------------------------------------------

STEP2_SYSTEM = """You are a Hebrew scripture verification judge. You receive pairs of (quoted Hebrew, actual verse from database) and determine whether there is a genuine citation error.

For each pair, output a JSON object with:
- "index": the pair number (1-based)
- "verdict": one of:
  - "GENUINE_ERROR" — the quoted text materially misrepresents the cited verse (dropped words, wrong form, garbled text)
  - "FALSE_POSITIVE" — the mismatch is expected (liturgical adaptation, deliberate paraphrase, allusion, partial quote that is acknowledged)
  - "MINOR" — a trivial difference (vowel pointing, maqaf vs space, divine name form) that doesn't constitute a real error
- "explanation": 1-2 sentences explaining your reasoning
- "correction": if GENUINE_ERROR, provide the corrected Hebrew text; otherwise null

Consider:
- A missing word from the middle of a quote IS a genuine error
- Using a different conjugation (e.g. עֲקָבַנִי vs וַיַּעְקְבֵנִי) IS a genuine error if the text claims to quote directly
- Liturgical/piyyut texts that adapt biblical wording are NOT errors
- Partial quotes that honestly present a fragment (not dropping words from the middle) are NOT errors
- If the commentary says something like "parallel to" or "similar formula" rather than quoting, it's NOT an error"""

STEP2_USER = """Judge these {count} quotation-vs-actual pairs. Output ONLY a JSON array.

{pairs}"""


def run_step1(client: anthropic.Anthropic, text: str) -> tuple:
    """Step 1: Ask Haiku to identify all Hebrew quotations with citations."""
    print("\n--- STEP 1: Haiku identifies citations ---")

    start = time.time()
    response = client.messages.create(
        model=HAIKU_MODEL,
        max_tokens=8192,
        system=STEP1_SYSTEM,
        messages=[{"role": "user", "content": STEP1_USER.format(text=text)}],
    )
    elapsed = time.time() - start

    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    cost = estimate_cost(input_tokens, output_tokens)

    print(f"  Time: {elapsed:.1f}s")
    print(f"  Tokens: {input_tokens:,} in / {output_tokens:,} out")
    print(f"  Cost: ${cost:.4f}")

    # Parse response
    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)

    try:
        citations = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  ERROR parsing JSON: {e}")
        print(f"  Raw response (first 500 chars): {raw[:500]}")
        citations = []

    print(f"  Found {len(citations)} citations")

    return citations, {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": cost,
        "elapsed": elapsed,
    }


def lookup_verses(citations: list, db_path: str) -> list:
    """Look up actual verse text from tanakh.db for each citation."""
    db = TanakhDatabase(Path(db_path))
    pairs = []

    for i, cit in enumerate(citations):
        ref_str = cit.get("ref", "")
        hebrew = cit.get("hebrew", "")
        cit_type = cit.get("type", "unknown")

        # Parse reference
        ref_match = re.match(
            r'((?:1|2|I{1,2})?\s*[A-Za-z]+(?:\s+of\s+[A-Za-z]+)?)\s+(\d+):(\d+)',
            ref_str
        )
        if not ref_match:
            continue

        raw_book = ref_match.group(1).strip()
        chapter = int(ref_match.group(2))
        verse_num = int(ref_match.group(3))

        db_book_name = _resolve_book_name(raw_book)
        if db_book_name is None:
            continue

        verse_obj = db.get_verse(db_book_name, chapter, verse_num)
        actual = verse_obj.hebrew if verse_obj else "[NOT FOUND IN DB]"

        # Check if the Hebrew is substantial enough to verify
        word_count = len(_HEBREW_WORD_RE.findall(hebrew))

        pairs.append({
            "index": i + 1,
            "ref": ref_str,
            "type": cit_type,
            "quoted_hebrew": hebrew,
            "actual_hebrew": actual,
            "word_count": word_count,
            "context": cit.get("context", ""),
        })

    db.close()
    return pairs


def run_step2(client: anthropic.Anthropic, pairs: list) -> tuple:
    """Step 2: Ask Haiku to judge matches."""
    # Only send pairs that are direct/partial quotes with enough words
    verifiable = [
        p for p in pairs
        if p["type"] in ("direct_quote", "partial_quote")
        and p["word_count"] >= MIN_HEBREW_WORDS
        and p["actual_hebrew"] != "[NOT FOUND IN DB]"
    ]

    if not verifiable:
        print("\n--- STEP 2: No verifiable quotations found ---")
        return [], {"input_tokens": 0, "output_tokens": 0, "cost": 0, "elapsed": 0}

    print(f"\n--- STEP 2: Haiku judges {len(verifiable)} quotation-vs-actual pairs ---")

    # Pre-filter: skip pairs where normalized quoted is a substring of actual
    needs_judgment = []
    auto_passed = 0
    for p in verifiable:
        norm_q = _normalize_hebrew(p["quoted_hebrew"])
        norm_a = _normalize_hebrew(p["actual_hebrew"])
        cons_q = _strip_to_consonants(p["quoted_hebrew"])
        cons_a = _strip_to_consonants(p["actual_hebrew"])

        if norm_q in norm_a or cons_q in cons_a:
            auto_passed += 1
        else:
            needs_judgment.append(p)

    print(f"  Auto-passed (substring match): {auto_passed}")
    print(f"  Need Haiku judgment: {len(needs_judgment)}")
    for p in needs_judgment:
        print(f"    - {p['ref']}: {p['quoted_hebrew'][:50]}...")

    if not needs_judgment:
        return [], {"input_tokens": 0, "output_tokens": 0, "cost": 0, "elapsed": 0}

    # Format pairs for Haiku
    pair_text = ""
    for j, p in enumerate(needs_judgment, 1):
        pair_text += f"\nPair {j}:\n"
        pair_text += f"  Reference: {p['ref']}\n"
        pair_text += f"  Type: {p['type']}\n"
        pair_text += f"  Context: {p['context']}\n"
        pair_text += f"  Quoted Hebrew: {p['quoted_hebrew']}\n"
        pair_text += f"  Actual verse text: {p['actual_hebrew']}\n"

    start = time.time()
    response = client.messages.create(
        model=HAIKU_MODEL,
        max_tokens=8192,
        system=STEP2_SYSTEM,
        messages=[{"role": "user", "content": STEP2_USER.format(
            count=len(needs_judgment), pairs=pair_text
        )}],
    )
    elapsed = time.time() - start

    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    cost = estimate_cost(input_tokens, output_tokens)

    print(f"  Time: {elapsed:.1f}s")
    print(f"  Tokens: {input_tokens:,} in / {output_tokens:,} out")
    print(f"  Cost: ${cost:.4f}")

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)

    try:
        judgments = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  ERROR parsing JSON: {e}")
        print(f"  Raw response (first 500 chars): {raw[:500]}")
        judgments = []

    # Attach the original pair info to each judgment
    for j in judgments:
        idx = j.get("index", 0) - 1
        if 0 <= idx < len(needs_judgment):
            j["ref"] = needs_judgment[idx]["ref"]
            j["quoted_hebrew"] = needs_judgment[idx]["quoted_hebrew"]
            j["actual_hebrew"] = needs_judgment[idx]["actual_hebrew"]

    return judgments, {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": cost,
        "elapsed": elapsed,
    }


def main():
    parser = argparse.ArgumentParser(description="Test Haiku-based citation verifier")
    parser.add_argument("psalm", type=int, help="Psalm number to verify")
    parser.add_argument("--db-path", default="database/tanakh.db")
    parser.add_argument("--input-file", type=Path, help="Override input file")
    args = parser.parse_args()

    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    # Load text
    if args.input_file:
        input_file = args.input_file
    else:
        psalm_dir = Path(f"output/psalm_{args.psalm}")
        input_file = psalm_dir / f"psalm_{args.psalm:03d}_print_ready.md"
        if not input_file.exists():
            input_file = psalm_dir / f"psalm_{args.psalm:03d}_copy_edited.md"

    if not input_file.exists():
        print(f"ERROR: File not found: {input_file}")
        return 1

    text = input_file.read_text(encoding="utf-8")
    print(f"Input: {input_file}")
    print(f"Size: {len(text):,} chars / {len(text.splitlines())} lines")

    # Initialize Anthropic client
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    # Step 1: Haiku identifies citations
    citations, step1_stats = run_step1(client, text)

    if not citations:
        print("\nNo citations found. Exiting.")
        return 0

    # Normalize compact keys to full keys
    TYPE_MAP = {"d": "direct_quote", "p": "partial_quote", "l": "liturgical",
                "a": "allusion", "e": "editorial_mention"}
    for c in citations:
        if "h" in c and "hebrew" not in c:
            c["hebrew"] = c.pop("h")
        if "r" in c and "ref" not in c:
            c["ref"] = c.pop("r")
        if "t" in c and "type" not in c:
            c["type"] = TYPE_MAP.get(c.pop("t"), "unknown")

    # Show Step 1 results
    print(f"\n  Citation breakdown:")
    type_counts = {}
    for c in citations:
        t = c.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
    for t, count in sorted(type_counts.items()):
        print(f"    {t}: {count}")

    # Show all identified citations
    print(f"\n  All citations identified by Haiku:")
    for i, c in enumerate(citations, 1):
        print(f"    {i:2d}. [{c.get('type', '?')[:8]:8s}] {c.get('ref', '?'):15s} — {c.get('hebrew', '')[:60]}")

    # Step 1.5: DB lookups
    pairs = lookup_verses(citations, args.db_path)
    print(f"\n  Resolved {len(pairs)} citations to DB lookups")

    # Step 2: Haiku judges mismatches
    judgments, step2_stats = run_step2(client, pairs)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  RESULTS SUMMARY — Psalm {args.psalm}")
    print(f"{'=' * 60}")

    if judgments:
        genuine = [j for j in judgments if j.get("verdict") == "GENUINE_ERROR"]
        false_pos = [j for j in judgments if j.get("verdict") == "FALSE_POSITIVE"]
        minor = [j for j in judgments if j.get("verdict") == "MINOR"]

        print(f"\n  Genuine errors: {len(genuine)}")
        for j in genuine:
            print(f"    - {j.get('ref', '?')}: {j.get('explanation', '')}")
            if j.get("correction"):
                print(f"      Correction: {j['correction']}")

        print(f"\n  False positives: {len(false_pos)}")
        for j in false_pos:
            print(f"    - {j.get('ref', '?')}: {j.get('explanation', '')}")

        print(f"\n  Minor differences: {len(minor)}")
        for j in minor:
            print(f"    - {j.get('ref', '?')}: {j.get('explanation', '')}")
    else:
        print("\n  No mismatches requiring judgment — all quotations matched.")

    # Cost summary
    total_cost = step1_stats["cost"] + step2_stats["cost"]
    total_input = step1_stats["input_tokens"] + step2_stats["input_tokens"]
    total_output = step1_stats["output_tokens"] + step2_stats["output_tokens"]

    print(f"\n  --- COST SUMMARY ---")
    print(f"  Step 1 (identify): {step1_stats['input_tokens']:,} in / {step1_stats['output_tokens']:,} out = ${step1_stats['cost']:.4f}")
    print(f"  Step 2 (judge):    {step2_stats['input_tokens']:,} in / {step2_stats['output_tokens']:,} out = ${step2_stats['cost']:.4f}")
    print(f"  TOTAL:             {total_input:,} in / {total_output:,} out = ${total_cost:.4f}")
    print(f"  Time:              {step1_stats['elapsed'] + step2_stats['elapsed']:.1f}s")
    print(f"{'=' * 60}\n")

    # Also run the existing regex verifier for comparison
    print(f"\n--- COMPARISON: Existing regex verifier ---")
    from src.utils.scripture_verifier import verify_citations, format_verification_report
    regex_issues = verify_citations(text, db_path=args.db_path, psalm_number=args.psalm)
    print(format_verification_report(regex_issues, psalm_number=args.psalm))

    return 0


if __name__ == "__main__":
    sys.exit(main())
