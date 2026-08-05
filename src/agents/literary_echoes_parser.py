"""
Literary Echoes — structured parsing, merging, and deterministic reconstruction.

This module holds everything about the literary-echoes documents that does NOT
require an API call. It exists because Session 374 found that the old LLM-driven
"Pass 4 reconstruction" was silently truncating finished documents: psalms 69-72
lost 40-84% of their verified echoes, every one of them ending mid-quotation,
none of them anywhere near `max_completion_tokens`. The model simply stopped, and
nothing checked `finish_reason`.

The fix is structural, not a bigger token budget: a document assembled by string
manipulation cannot stop early. So the pipeline now
  * parses Pass 1 / Pass 2 markdown into `EchoEntry` records with stable IDs,
  * asks Pass 3 for a machine-readable verdict PER ENTRY (keyed by that ID), and
  * rebuilds the final document here, in Python.

A second, quieter benefit: Pass 4's instruction 7 was "do not substantively alter
surviving ones", which is unenforceable when a model is regenerating the whole
document from scratch. Here it is enforced by construction — analysis prose is
copied byte-for-byte and only a quotation block or heading the verifier explicitly
corrected is ever substituted.

Nothing in this module imports an SDK; it is all pure functions over strings, so
`tests/test_literary_echoes_parser.py` can cover the failure modes directly.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------

_CLUSTER_RE = re.compile(r"^###[ \t]+(?!#)(.*)$", re.MULTILINE)
_ENTRY_RE = re.compile(r"^####[ \t]+(?!#)(.*)$", re.MULTILINE)

# "### Psalm 72:4-5 — The King as Rain" -> verse spec "72:4-5", first verse 4.
_VERSE_RE = re.compile(r"(\d+)\s*:\s*(\d+)")

# Scaffolding Pass 4 used to strip in prose. Both are cognitive-forcing devices
# for the generator, not reader-facing content.
_DEFAULT_BYPASSED_RE = re.compile(
    r"^[ \t]*\*+[ \t]*Default bypassed:.*?$\n?", re.MULTILINE | re.IGNORECASE
)
_REPLACES_RE = re.compile(
    r"^[ \t]*\*{0,2}[ \t]*REPLACES:[ \t]*(.+?)[ \t]*\*{0,2}[ \t]*$",
    re.MULTILINE | re.IGNORECASE,
)

# A horizontal rule used as an inter-cluster separator in the source documents.
# We re-emit our own, so the parsed bodies must not keep theirs.
_HRULE_RE = re.compile(r"^[ \t]*-{3,}[ \t]*$", re.MULTILINE)

# The author is everything up to the first comma on the "#### " line, with any
# markdown emphasis stripped. Mirrors the long-standing exclusion-scan regex so
# the ledger and the old behaviour agree on what counts as an author name.
_AUTHOR_RE = re.compile(r"^([^,\n*]+?)\s*,")

_VERIFICATION_MARKERS = "✅⚠️❌🔄⚠"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class EchoEntry:
    """One `#### Author, *Work*` block plus its quotation and analysis."""

    entry_id: str
    source: str  # "pass_1_gemini" | "pass_1_opus" | "pass_2"
    cluster_key: str  # normalised verse spec, e.g. "72:4"
    cluster_sort: Tuple[int, int]
    cluster_heading: str  # full "### ..." heading text (without the "### ")
    cluster_preamble: str  # psalm quotation block for the cluster
    heading: str  # full "#### ..." line text (without the "#### ")
    body: str  # quotation block + analysis, verbatim
    replaces: Optional[str] = None  # raw "Author, *Work* for Psalm N:x" text

    @property
    def author(self) -> str:
        m = _AUTHOR_RE.match(self.heading.strip())
        name = m.group(1) if m else self.heading.strip()
        return name.strip(" *_")

    @property
    def author_key(self) -> str:
        return normalise_author(self.author)

    @property
    def quotation_block(self) -> str:
        """The leading run of '>' lines — what Pass 3 actually verifies."""
        lines, out = self.body.split("\n"), []
        started = False
        for line in lines:
            if line.lstrip().startswith(">"):
                started = True
                out.append(line)
            elif started and not line.strip():
                out.append(line)
            elif started:
                break
        return "\n".join(out).strip()

    def render(self) -> str:
        return f"#### {self.heading}\n{self.body}".rstrip()


@dataclass
class ParsedDocument:
    entries: List[EchoEntry] = field(default_factory=list)
    preamble: str = ""  # dropped audit paragraph, kept for the run log


@dataclass
class Verdict:
    """A machine-readable Pass 3 result for exactly one entry."""

    entry_id: str
    verdict: str  # "verified" | "corrected" | "rejected"
    corrected_heading: Optional[str] = None
    corrected_quotation_block: Optional[str] = None
    reason: str = ""

    @property
    def is_rejection(self) -> bool:
        return self.verdict == "rejected"


# ---------------------------------------------------------------------------
# Author normalisation + ledger
# ---------------------------------------------------------------------------


def normalise_author(name: str) -> str:
    """Fold an author name to a comparison key.

    Accents are stripped because the same poet arrives spelled both ways across
    models and passes (Cesar/César Vallejo, Odon/Ödön von Horvath); without the
    fold the ledger would treat them as two people and the de-duplication that
    the Second Echo Principle depends on would quietly leak.
    """
    if not name:
        return ""
    decomposed = unicodedata.normalize("NFKD", name)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    stripped = stripped.replace("’", "'").replace("`", "'")
    stripped = re.sub(r"[^a-z0-9' ]+", " ", stripped.lower())
    return re.sub(r"\s+", " ", stripped).strip()


def extract_authors(text: str) -> List[str]:
    """Every author named by a `#### ` heading, in document order."""
    out = []
    for m in _ENTRY_RE.finditer(text):
        am = _AUTHOR_RE.match(m.group(1).strip())
        name = (am.group(1) if am else m.group(1)).strip(" *_")
        if name:
            out.append(name)
    return out


class AuthorLedger:
    """Corpus-wide record of which authors have been used in which psalms.

    Replaces the old "scan the 4 most recently modified files" exclusion, which
    could only ever prevent *adjacent* repetition. Over 150 psalms that is the
    wrong horizon: the Second Echo Principle is a claim about the whole series,
    and a per-document cap cannot see the corpus. Measured over the 24 psalms
    built by this pipeline, 12 authors were already at 4 appearances and 22 more
    at 3, with the reuse curve steepening as the shared pool of "major author
    with a verifiable original-language quotation" gets consumed.

    The ledger is rebuilt from the canonical files on every run rather than
    maintained incrementally, so a hand-edited or deleted file can never leave it
    permanently out of step with reality.
    """

    def __init__(self, entries: Optional[Dict[str, dict]] = None):
        self.authors: Dict[str, dict] = entries or {}

    @classmethod
    def build(cls, echoes_dir: Path, exclude_psalm: Optional[int] = None) -> "AuthorLedger":
        ledger = cls()
        if not echoes_dir.exists():
            return ledger
        files = []
        for path in echoes_dir.glob("psalm_*_literary_echoes.txt"):
            m = re.search(r"psalm_(\d+)_literary_echoes", path.name)
            if not m:
                continue
            number = int(m.group(1))
            if exclude_psalm is not None and number == exclude_psalm:
                continue
            try:
                files.append((path.stat().st_mtime, number, path))
            except OSError:
                continue
        files.sort(key=lambda t: t[0], reverse=True)

        for rank, (_mtime, number, path) in enumerate(files):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for name in dict.fromkeys(extract_authors(text)):
                key = normalise_author(name)
                if not key:
                    continue
                rec = ledger.authors.setdefault(
                    key, {"display": name, "psalms": [], "most_recent_rank": rank}
                )
                if number not in rec["psalms"]:
                    rec["psalms"].append(number)
                rec["most_recent_rank"] = min(rec["most_recent_rank"], rank)
        return ledger

    def recent(self, window: int) -> List[str]:
        """Authors appearing in any of the `window` most recently written files."""
        names = [
            rec["display"]
            for rec in self.authors.values()
            if rec.get("most_recent_rank", 10**9) < window
        ]
        return sorted(names, key=str.casefold)

    def overused(self, threshold: int, limit: int = 120) -> List[str]:
        """Authors already used in >= `threshold` psalms, worst offenders first.

        `limit` caps how many names are injected into the prompt. Without it this
        list grows without bound across 150 psalms and eventually costs more in
        input tokens than the diversity it buys.
        """
        scored = [
            (len(rec["psalms"]), rec["display"])
            for rec in self.authors.values()
            if len(rec["psalms"]) >= threshold
        ]
        scored.sort(key=lambda t: (-t[0], t[1].casefold()))
        return [name for _count, name in scored[:limit]]

    def count_for(self, name: str) -> int:
        rec = self.authors.get(normalise_author(name))
        return len(rec["psalms"]) if rec else 0

    def to_dict(self) -> dict:
        return {
            "author_count": len(self.authors),
            "authors": {
                key: {"display": rec["display"], "psalms": sorted(rec["psalms"])}
                for key, rec in sorted(self.authors.items())
            },
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
        )


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _normalise_verse(heading: str) -> Tuple[str, Tuple[int, int]]:
    m = _VERSE_RE.search(heading)
    if not m:
        return heading.strip().casefold(), (10**6, 0)
    chapter, verse = int(m.group(1)), int(m.group(2))
    return f"{chapter}:{verse}", (chapter, verse)


def _split_on(pattern: re.Pattern, text: str) -> Tuple[str, List[Tuple[str, str]]]:
    """Split `text` at each match, returning (preamble, [(heading, body), ...])."""
    matches = list(pattern.finditer(text))
    if not matches:
        return text, []
    preamble = text[: matches[0].start()]
    sections = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append((m.group(1).strip(), text[m.end() : end]))
    return preamble, sections


def _take_trailing_replaces(text: str) -> Tuple[str, Optional[str]]:
    """Pull a REPLACES marker off the end of a block.

    The Pass 2 prompt says a replacement entry "begins" with the marker, which in
    practice puts it on the line above the `####` heading — i.e. at the tail of
    whatever block precedes it. Leading markers are handled separately because
    models place it both ways.
    """
    found = None
    for m in _REPLACES_RE.finditer(text):
        found = m.group(1).strip()
    if found is None:
        return text, None
    return _REPLACES_RE.sub("", text).rstrip() + "\n", found


def _clean_body(body: str) -> str:
    body = _HRULE_RE.sub("", body)
    body = _DEFAULT_BYPASSED_RE.sub("", body)
    return body.strip("\n").rstrip() + "\n" if body.strip() else ""


def parse_document(text: str, source: str, id_prefix: str) -> ParsedDocument:
    """Parse one pass's markdown into `EchoEntry` records.

    `id_prefix` must be unique per source so that entries from two Pass-1
    generators can be merged without colliding.
    """
    doc = ParsedDocument()
    if not text or not text.strip():
        return doc

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    doc_preamble, clusters = _split_on(_CLUSTER_RE, text)
    doc.preamble = doc_preamble.strip()

    counter = 0
    for cluster_heading, cluster_body in clusters:
        cluster_key, cluster_sort = _normalise_verse(cluster_heading)
        preamble, entries = _split_on(_ENTRY_RE, cluster_body)

        preamble = _DEFAULT_BYPASSED_RE.sub("", preamble)
        preamble, pending_replaces = _take_trailing_replaces(preamble)
        preamble = _HRULE_RE.sub("", preamble).strip("\n").rstrip()

        for heading, body in entries:
            # A REPLACES marker can also lead the body rather than trail the
            # previous block; check both so neither placement is lost.
            leading = _REPLACES_RE.search(body[:400]) if body else None
            if leading is not None:
                pending_replaces = pending_replaces or leading.group(1).strip()
                body = body[: leading.start()] + body[leading.end() :]

            body, trailing_replaces = _take_trailing_replaces(body)
            counter += 1
            doc.entries.append(
                EchoEntry(
                    entry_id=f"{id_prefix}{counter:02d}",
                    source=source,
                    cluster_key=cluster_key,
                    cluster_sort=cluster_sort,
                    cluster_heading=cluster_heading,
                    cluster_preamble=preamble,
                    heading=heading,
                    body=_clean_body(body),
                    replaces=pending_replaces,
                )
            )
            pending_replaces = trailing_replaces

    return doc


# ---------------------------------------------------------------------------
# Merging
# ---------------------------------------------------------------------------


def merge_pass1_variants(
    primary: Sequence[EchoEntry],
    secondary: Sequence[EchoEntry],
    per_cluster_cap: int = 2,
) -> List[EchoEntry]:
    """Interleave two independent Pass-1 generations, one model at a time.

    The Second Echo Principle asks the generator to push past the first names
    that surface — but a single model can only push past its OWN reflexes, and
    two frontier models trained on different corpora surface different first
    echoes. Running Pass 1 twice and merging attacks that at the root.

    The merge is deliberately NOT a union. A union would double the entry count,
    and since Pass 3 now verifies per entry, it would double the most expensive
    pass in the pipeline. Instead each cluster alternates between the two models,
    so what changes is the provenance mix rather than the volume.

    The per-cluster ceiling is `max(per_cluster_cap, <primary entries in that
    cluster>)`. The floor term is not decoration: measured over the 26 psalms
    this pipeline has built, 21 Pass-1 clusters carried 3+ entries, so a flat cap
    of 2 would have silently deleted 23 perfectly good echoes — reintroducing, in
    the merge step, exactly the kind of quiet content loss this rewrite exists to
    remove. With the floor, a cluster can never come out smaller than the primary
    generator alone would have produced, and a cluster only the secondary model
    found still contributes up to `per_cluster_cap` entries of its own.

    Author de-duplication is global, not per-cluster, because the "no author
    appears twice" rule is document-wide.
    """
    by_cluster: Dict[str, Dict[str, List[EchoEntry]]] = {}
    order: List[str] = []
    for entries, side in ((primary, "primary"), (secondary, "secondary")):
        for entry in entries:
            slot = by_cluster.setdefault(entry.cluster_key, {"primary": [], "secondary": []})
            if entry.cluster_key not in order:
                order.append(entry.cluster_key)
            slot[side].append(entry)

    merged: List[EchoEntry] = []
    seen_authors: set = set()
    for cluster_key in sorted(order, key=lambda k: by_cluster[k]["primary"][0].cluster_sort
                              if by_cluster[k]["primary"] else by_cluster[k]["secondary"][0].cluster_sort):
        slot = by_cluster[cluster_key]
        queues = [list(slot["primary"]), list(slot["secondary"])]
        # Never yield fewer entries than the primary generator alone would have.
        cap = max(per_cluster_cap, len(slot["primary"]))
        taken = 0
        turn = 0
        # Alternate primary/secondary; when one side is exhausted the other
        # fills the remaining capacity, so a cluster only one model found still
        # comes through whole.
        while taken < cap and (queues[0] or queues[1]):
            queue = queues[turn % 2]
            turn += 1
            if not queue:
                continue
            entry = queue.pop(0)
            if entry.author_key in seen_authors:
                continue
            seen_authors.add(entry.author_key)
            merged.append(entry)
            taken += 1
    return merged


def apply_replacements(entries: Sequence[EchoEntry]) -> Tuple[List[EchoEntry], List[str]]:
    """Honour Pass 2's `REPLACES:` markers by dropping the superseded entry."""
    replaced_keys = {}
    for entry in entries:
        if entry.replaces:
            am = _AUTHOR_RE.match(entry.replaces.strip())
            name = (am.group(1) if am else entry.replaces).strip(" *_")
            key = normalise_author(name)
            if key:
                replaced_keys[key] = entry.entry_id

    kept, notes = [], []
    for entry in entries:
        target = replaced_keys.get(entry.author_key)
        if target is not None and target != entry.entry_id:
            notes.append(f"{entry.entry_id} ({entry.author}) replaced by {target}")
            continue
        kept.append(entry)
    return kept, notes


def drop_malformed(entries: Sequence[EchoEntry]) -> Tuple[List[EchoEntry], List[str]]:
    """Discard entries that are not actually comparisons.

    A generator can emit its deliberation as prose inside the document instead of
    keeping it internal. Session 374 measured this on Claude Sonnet 5 at
    `effort=low`, which produced headings like

        #### Gwendolyn Brooks - not eligible (American, but let me choose properly)

    followed by "I'll replace with a verified fit:", and a quotation block whose
    attribution line read "Actually let me choose a securely recalled Waits
    passage instead." Parsed naively, that puts a fabricated author and the
    model's self-talk into the writer's dossier.

    The test is structural rather than a phrase blacklist: a real entry has a
    quotation block and some analysis under it. Anything else is scaffolding that
    happened to start with `####`.
    """
    kept, notes = [], []
    for entry in entries:
        block = entry.quotation_block
        if not block:
            notes.append(f"{entry.entry_id} ({entry.author}) dropped: no quotation block")
            continue
        if len(entry.body) - len(block) < 60:
            notes.append(f"{entry.entry_id} ({entry.author}) dropped: no analysis under the quotation")
            continue
        kept.append(entry)
    return kept, notes


def dedupe_authors(entries: Sequence[EchoEntry]) -> Tuple[List[EchoEntry], List[str]]:
    """Enforce 'no author appears twice', keeping the first occurrence."""
    seen, kept, notes = set(), [], []
    for entry in entries:
        if entry.author_key in seen:
            notes.append(f"{entry.entry_id} ({entry.author}) dropped as a duplicate author")
            continue
        seen.add(entry.author_key)
        kept.append(entry)
    return kept, notes


# ---------------------------------------------------------------------------
# Verdicts + reconstruction
# ---------------------------------------------------------------------------


def parse_verdict(raw: str, entry_id: str) -> Verdict:
    """Read one verifier response into a `Verdict`, failing safe.

    Fail-safe means: anything we cannot parse becomes `verified`, i.e. the entry
    survives untouched. That direction is deliberate. The bug this whole rewrite
    exists to fix was silent content LOSS, so a malformed verifier response must
    never be able to delete a real echo — at worst it leaves one unverified,
    which the run log records.
    """
    blob = _extract_json_object(raw)
    if blob is None:
        return Verdict(entry_id=entry_id, verdict="verified", reason="unparseable verifier response")
    try:
        data = json.loads(blob)
    except (ValueError, TypeError):
        return Verdict(entry_id=entry_id, verdict="verified", reason="invalid JSON from verifier")
    if not isinstance(data, dict):
        return Verdict(entry_id=entry_id, verdict="verified", reason="verifier returned non-object")

    verdict = str(data.get("verdict", "verified")).strip().lower()
    if verdict not in {"verified", "corrected", "rejected"}:
        verdict = "verified"

    def _clean(value) -> Optional[str]:
        if not isinstance(value, str) or not value.strip():
            return None
        text = value.strip()
        for marker in _VERIFICATION_MARKERS:
            text = text.replace(marker, "")
        return text.strip() or None

    heading = _clean(data.get("corrected_heading"))
    if heading:
        heading = re.sub(r"^#+\s*", "", heading).strip()
    block = _clean(data.get("corrected_quotation_block"))

    if verdict == "corrected" and not heading and not block:
        # "Corrected" with nothing to substitute is just "verified" with a note.
        verdict = "verified"

    return Verdict(
        entry_id=entry_id,
        verdict=verdict,
        corrected_heading=heading,
        corrected_quotation_block=block,
        reason=str(data.get("reason", "")).strip(),
    )


def _extract_json_object(raw: str) -> Optional[str]:
    """Pull the first balanced {...} out of a response, ignoring code fences."""
    if not raw:
        return None
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(.+?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    start = text.find("{")
    if start == -1:
        return None
    depth, in_string, escaped = 0, False, False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def apply_verdict(entry: EchoEntry, verdict: Verdict) -> EchoEntry:
    """Substitute only what the verifier explicitly corrected.

    Analysis prose is never regenerated or reworded here — that is the whole
    point of doing reconstruction in Python.
    """
    if verdict.corrected_heading:
        entry.heading = verdict.corrected_heading
    if verdict.corrected_quotation_block:
        old_block = entry.quotation_block
        new_block = verdict.corrected_quotation_block.rstrip()
        if old_block and old_block in entry.body:
            entry.body = entry.body.replace(old_block, new_block, 1)
        else:
            # No recognisable quotation block to swap (rare, malformed source).
            # Prepend rather than discard the correction.
            entry.body = f"{new_block}\n\n{entry.body.lstrip()}"
    return entry


def reconstruct(entries: Sequence[EchoEntry]) -> str:
    """Rebuild the reader-facing document from surviving entries.

    Output shape is byte-compatible with what Pass 4 used to emit: `### Psalm
    N:v — Label` clusters, the psalm quotation once per cluster, `#### Author,
    *Work*` blocks, `---` between clusters, and no verification markers or
    generator scaffolding anywhere.
    """
    if not entries:
        return ""

    grouped: Dict[str, List[EchoEntry]] = {}
    meta: Dict[str, EchoEntry] = {}
    for entry in entries:
        grouped.setdefault(entry.cluster_key, []).append(entry)
        meta.setdefault(entry.cluster_key, entry)

    chunks = []
    for cluster_key in sorted(grouped, key=lambda k: meta[k].cluster_sort):
        head = meta[cluster_key]
        block = [f"### {head.cluster_heading}"]
        if head.cluster_preamble.strip():
            block.append("")
            block.append(head.cluster_preamble.strip())
        for entry in grouped[cluster_key]:
            block.append("")
            block.append(entry.render())
        chunks.append("\n".join(block).rstrip())

    return ("\n\n---\n\n".join(chunks)).strip() + "\n"


__all__ = [
    "AuthorLedger",
    "EchoEntry",
    "ParsedDocument",
    "Verdict",
    "apply_replacements",
    "apply_verdict",
    "dedupe_authors",
    "drop_malformed",
    "extract_authors",
    "merge_pass1_variants",
    "normalise_author",
    "parse_document",
    "parse_verdict",
    "reconstruct",
]
