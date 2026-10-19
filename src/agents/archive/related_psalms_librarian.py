"""
Related Psalms Librarian

Loads and formats related psalm information from the top connections analysis.
For any given psalm, retrieves matching psalms with their full text and detailed
information about shared roots, contiguous phrases, and skipgrams.

This librarian provides comprehensive context about potentially related psalms
to help the synthesis and editor agents make connections.
"""

import sys
import json
import re
import difflib
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass

# Handle imports for both module and script usage
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.data_sources.tanakh_database import TanakhDatabase
else:
    from ..data_sources.tanakh_database import TanakhDatabase


# --- Doublet detection thresholds (Session 365) ---
# Two verses whose consonantal token sets overlap at or above this Jaccard
# ratio count as the same verse appearing in two psalms.
DOUBLET_VERSE_SIMILARITY = 0.7
# This many near-duplicate verse pairs make the psalm pair a DOUBLET (e.g.
# Ps 108 = Ps 57:8-12 + Ps 60:7-14). Below it, a lone pair is flagged as a
# shared verse only if it clears the higher single-verse bar.
DOUBLET_MIN_VERSES = 2
SINGLE_VERSE_SIMILARITY = 0.8
# Once verses align, a neighboring verse at the same offset joins the doublet
# at this lower bar. Mid-run verses with heavy redaction (divine-name swaps,
# plene/defective spelling) score 0.4-0.65 — e.g. 57:10//108:4 where אדני
# becomes יהוה — and are precisely the variants worth surfacing.
GAP_FILL_SIMILARITY = 0.4
# Verses shorter than this many tokens never participate — otherwise every
# psalm pair sharing a generic superscription (למנצח מזמור לדוד) gets flagged.
MIN_VERSE_TOKENS = 4
# Shared roots beyond this many are listed by name only, without verse
# contexts. The detailed per-root context lines are the bulk of the section
# and the low-IDF tail of them was never used by any downstream agent.
MAX_DETAILED_ROOTS = 10


@dataclass
class RelatedPsalmMatch:
    """Information about a related psalm and its connections."""
    psalm_number: int
    final_score: float
    full_text_hebrew: List[Dict[str, Any]]  # List of {"verse": int, "hebrew": str}
    full_text_english: List[Dict[str, Any]]  # List of {"verse": int, "english": str}
    shared_roots: List[Dict[str, Any]]
    contiguous_phrases: List[Dict[str, Any]]
    skipgrams: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'psalm_number': self.psalm_number,
            'final_score': self.final_score,
            'full_text_hebrew': self.full_text_hebrew,
            'full_text_english': self.full_text_english,
            'shared_roots': self.shared_roots,
            'contiguous_phrases': self.contiguous_phrases,
            'skipgrams': self.skipgrams
        }


class RelatedPsalmsLibrarian:
    """
    Retrieves and formats related psalms from the top connections analysis.

    This librarian identifies psalms that have significant word and phrase
    relationships with the psalm being analyzed, providing the synthesis and
    master editor agents with potentially relevant connections.
    """

    def __init__(
        self,
        connections_file: str = "data/analysis_results/top_550_connections_v6.json",
        db: Optional[TanakhDatabase] = None
    ):
        """
        Initialize Related Psalms Librarian.

        Args:
            connections_file: Path to the top connections JSON file
            db: TanakhDatabase instance (creates new if None)
        """
        self.connections_file = Path(connections_file)
        self.db = db or TanakhDatabase()
        self.connections_data = self._load_connections()
        self.logger = None  # Can be set by caller if needed

    def _load_connections(self) -> List[Dict[str, Any]]:
        """Load the connections data from JSON file."""
        if not self.connections_file.exists():
            return []

        with open(self.connections_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_related_psalms(self, psalm_number: int) -> List[RelatedPsalmMatch]:
        """
        Get all related psalms for a given psalm number.

        Args:
            psalm_number: The psalm number to find connections for

        Returns:
            List of RelatedPsalmMatch objects with full psalm text and connection details
        """
        related = []

        for connection in self.connections_data:
            # Check if this psalm is psalm_a or psalm_b in the connection
            if connection['psalm_a'] == psalm_number:
                related_psalm_num = connection['psalm_b']
            elif connection['psalm_b'] == psalm_number:
                related_psalm_num = connection['psalm_a']
            else:
                continue

            # Get the full text of the related psalm
            psalm = self.db.get_psalm(related_psalm_num)
            if not psalm:
                continue

            # Extract Hebrew and English text
            hebrew_text = [{"verse": v.verse, "hebrew": v.hebrew} for v in psalm.verses]
            english_text = [{"verse": v.verse, "english": v.english} for v in psalm.verses]

            # Extract connection details
            # Note: The data structure uses matches_from_a and matches_from_b
            # We need to preserve these as they show where matches occur in each psalm

            match = RelatedPsalmMatch(
                psalm_number=related_psalm_num,
                final_score=connection.get('final_score', 0.0),
                full_text_hebrew=hebrew_text,
                full_text_english=english_text,
                shared_roots=connection.get('deduplicated_roots', []),
                contiguous_phrases=connection.get('deduplicated_contiguous_phrases', []),
                skipgrams=connection.get('deduplicated_skipgrams', [])
            )

            related.append(match)

        # Sort by score (highest first)
        related.sort(key=lambda x: x.final_score, reverse=True)

        # Limit to top 5 most related psalms
        return related[:5]

    def format_for_research_bundle(
        self,
        psalm_number: int,
        related_matches: List[RelatedPsalmMatch],
        max_size_chars: int = 100000,
        include_full_text: bool = False
    ) -> str:
        """
        Format related psalms as markdown for inclusion in research bundle.

        Args:
            psalm_number: The psalm being analyzed
            related_matches: List of related psalm matches
            max_size_chars: Maximum size in characters (default 100KB)
            include_full_text: Whether to include full Hebrew text of related psalms
                             (default False — relationship metadata + shared phrases retained)

        Returns:
            Formatted markdown string
        """
        if not related_matches:
            return ""

        # Detect doublets / near-verbatim shared verses deterministically, so
        # the section can LEAD with the conclusion instead of burying it under
        # thousands of atom-level matches (the Ps 60/108 failure mode).
        doublet_map = self._detect_shared_verses(psalm_number, related_matches)

        # Build the preamble (this is always included)
        preamble = self._build_preamble(psalm_number, related_matches, doublet_map)

        if self.logger:
            self.logger.info(f"Related Psalms formatting for Psalm {psalm_number}: "
                           f"max_size={max_size_chars}, include_full_text={include_full_text}, "
                           f"preamble_size={len(preamble)} chars, "
                           f"doublets={sorted(doublet_map.keys())}")

        # If full text not requested, format all matches compactly
        if not include_full_text:
            md = preamble
            for match in related_matches:
                md += self._format_single_match(psalm_number, match, include_full_text=False,
                                                shared_verse_pairs=doublet_map.get(match.psalm_number))

            # Still respect max_size_chars cap
            if len(md) > max_size_chars:
                md = md[:max_size_chars - 100] + "\n\n*[Section truncated for size]*\n"

            if self.logger:
                self.logger.info(f"Related Psalms final result for Psalm {psalm_number}: "
                               f"size={len(md)} chars (compact, no full texts)")
            return md

        # Full text mode: progressively remove full text sections until under the cap
        psalms_without_full_text = set()

        while True:
            md = preamble

            for match in related_matches:
                has_full_text = match.psalm_number not in psalms_without_full_text
                md += self._format_single_match(psalm_number, match, include_full_text=has_full_text,
                                                shared_verse_pairs=doublet_map.get(match.psalm_number))

            # Check if under cap
            if len(md) <= max_size_chars:
                break

            # Find next psalm to remove full text from (start from last/lowest-scored)
            # related_matches is sorted by score descending, so we remove from the end first
            removed_one = False
            for match in reversed(related_matches):
                if match.psalm_number not in psalms_without_full_text:
                    psalms_without_full_text.add(match.psalm_number)
                    removed_one = True
                    break

            # If we've already removed full text from all psalms and still over cap, stop
            if not removed_one:
                # Add a note that content was truncated
                if len(md) > max_size_chars:
                    md = md[:max_size_chars - 100] + "\n\n*[Section truncated for size]*\n"
                break

        if self.logger:
            self.logger.info(f"Related Psalms final result for Psalm {psalm_number}: "
                           f"size={len(md)} chars (limit={max_size_chars}), "
                           f"psalms_without_full_text={psalms_without_full_text}")

        return md

    def _detect_shared_verses(
        self,
        psalm_number: int,
        related_matches: List[RelatedPsalmMatch]
    ) -> Dict[int, List[Tuple[int, int, float]]]:
        """
        Detect near-verbatim shared verses between the analyzed psalm and each
        related psalm.

        Returns {related_psalm_number: [(verse_here, verse_there, similarity)]}
        containing only pairs worth flagging: either a doublet
        (>= DOUBLET_MIN_VERSES aligned verse pairs) or a single verse clearing
        SINGLE_VERSE_SIMILARITY. Empty dict when the database has no text for
        the analyzed psalm.
        """
        try:
            psalm = self.db.get_psalm(psalm_number)
        except Exception:
            psalm = None
        if not psalm:
            return {}

        analyzed_verses = [{"verse": v.verse, "hebrew": v.hebrew} for v in psalm.verses]

        doublet_map: Dict[int, List[Tuple[int, int, float]]] = {}
        for match in related_matches:
            pairs = self._find_shared_verse_pairs(analyzed_verses, match.full_text_hebrew)
            if len(pairs) >= DOUBLET_MIN_VERSES:
                doublet_map[match.psalm_number] = pairs
            elif len(pairs) == 1 and pairs[0][2] >= SINGLE_VERSE_SIMILARITY:
                doublet_map[match.psalm_number] = pairs
        return doublet_map

    def _tokenize_verse(self, verse_text: str) -> Tuple[List[str], List[str]]:
        """
        Split a pointed Hebrew verse into (display_tokens, consonantal_keys).

        Reads the qere at ketiv/qere sites (drops the parenthesized ketiv,
        unwraps the bracketed qere — same convention as distributional_facts),
        splits maqaf-joined words, and drops paragraph markers ({פ}/{ס}).
        Display tokens keep their pointing; keys are consonantal.
        """
        display: List[str] = []
        keys: List[str] = []
        if not verse_text:
            return display, keys

        for raw in verse_text.split():
            if raw.startswith('{'):
                continue
            # Split maqaf-joined words BEFORE consonantal reduction —
            # _remove_nikud strips the maqaf itself (U+05BE is in its range).
            for part in raw.replace('־', ' ').split():
                if part.startswith('(') and part.endswith(')'):
                    continue  # ketiv — we read the qere
                if part.startswith('[') and part.endswith(']'):
                    part = part[1:-1]
                key = self._remove_nikud(part).strip('()[]')
                if key:
                    display.append(part)
                    keys.append(key)
        return display, keys

    def _find_shared_verse_pairs(
        self,
        verses_a: List[Dict[str, Any]],
        verses_b: List[Dict[str, Any]]
    ) -> List[Tuple[int, int, float]]:
        """
        Align near-duplicate verses between two psalms.

        Returns [(verse_a, verse_b, similarity)] sorted by verse_a, where
        similarity is the Jaccard ratio of consonantal token sets. Each verse
        participates in at most one pair (greedy, best similarity first).
        """
        tok_a = {v['verse']: self._tokenize_verse(v.get('hebrew', '')) for v in verses_a}
        tok_b = {v['verse']: self._tokenize_verse(v.get('hebrew', '')) for v in verses_b}

        candidates = []
        for va, (_, ka) in tok_a.items():
            if len(ka) < MIN_VERSE_TOKENS:
                continue
            set_a = set(ka)
            for vb, (_, kb) in tok_b.items():
                if len(kb) < MIN_VERSE_TOKENS:
                    continue
                set_b = set(kb)
                sim = len(set_a & set_b) / len(set_a | set_b)
                if sim >= DOUBLET_VERSE_SIMILARITY:
                    candidates.append((sim, va, vb))

        candidates.sort(reverse=True)
        used_a, used_b = set(), set()
        pairs: List[Tuple[int, int, float]] = []
        for sim, va, vb in candidates:
            if va in used_a or vb in used_b:
                continue
            used_a.add(va)
            used_b.add(vb)
            pairs.append((va, vb, sim))

        # Gap-fill: extend aligned runs to neighboring verses at the same
        # offset that clear the lower GAP_FILL_SIMILARITY bar. Doublets are
        # contiguous; a verse between (or beside) aligned neighbors that
        # still shares 40%+ of its words is part of the doublet, just more
        # heavily redacted — and those redactions are the interesting part.
        sets_a = {v: set(k) for v, (_, k) in tok_a.items() if k}
        sets_b = {v: set(k) for v, (_, k) in tok_b.items() if k}
        changed = bool(pairs)
        while changed:
            changed = False
            for va, vb, _ in list(pairs):
                for step in (1, -1):
                    na, nb = va + step, vb + step
                    if na in used_a or nb in used_b:
                        continue
                    if na not in sets_a or nb not in sets_b:
                        continue
                    sim = len(sets_a[na] & sets_b[nb]) / len(sets_a[na] | sets_b[nb])
                    if sim >= GAP_FILL_SIMILARITY:
                        used_a.add(na)
                        used_b.add(nb)
                        pairs.append((na, nb, sim))
                        changed = True

        pairs.sort()
        return pairs

    def _compress_pair_runs(
        self,
        psalm_a: int,
        psalm_b: int,
        pairs: List[Tuple[int, int, float]]
    ) -> str:
        """Render aligned verse pairs compactly, e.g. '60:7–14 // 108:7–14'."""
        runs: List[List[int]] = []
        for va, vb, _ in pairs:
            if runs and va == runs[-1][1] + 1 and vb == runs[-1][3] + 1:
                runs[-1][1] = va
                runs[-1][3] = vb
            else:
                runs.append([va, va, vb, vb])

        parts = []
        for a0, a1, b0, b1 in runs:
            if a0 == a1:
                parts.append(f"{psalm_a}:{a0} // {psalm_b}:{b0}")
            else:
                parts.append(f"{psalm_a}:{a0}–{a1} // {psalm_b}:{b0}–{b1}")
        return ", ".join(parts)

    def _diff_verse_pair(
        self,
        disp_a: List[str],
        keys_a: List[str],
        disp_b: List[str],
        keys_b: List[str]
    ) -> Optional[str]:
        """
        Word-level diff of two near-duplicate verses.

        Returns None when consonantally identical; otherwise a compact
        'text_a ↔ text_b; ...' listing of just the differing spans (pointed).
        """
        if keys_a == keys_b:
            return None

        sm = difflib.SequenceMatcher(None, keys_a, keys_b, autojunk=False)
        frags = []
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal':
                continue
            a = " ".join(disp_a[i1:i2]) or "—"
            b = " ".join(disp_b[j1:j2]) or "—"
            frags.append(f"{a} ↔ {b}")
        return "; ".join(frags)

    def _format_doublet_block(
        self,
        analyzing_psalm: int,
        match: RelatedPsalmMatch,
        pairs: List[Tuple[int, int, float]],
        is_doublet: bool
    ) -> str:
        """
        Lead a match entry with the computed conclusion: this psalm pair
        shares whole verses. States the extent, then diffs the variants —
        the two things the atom-level listings cannot say.
        """
        span = self._compress_pair_runs(analyzing_psalm, match.psalm_number, pairs)

        # Re-tokenize the aligned verses for the diffs.
        try:
            psalm = self.db.get_psalm(analyzing_psalm)
            text_a = {v.verse: v.hebrew for v in psalm.verses} if psalm else {}
        except Exception:
            text_a = {}
        text_b = {v['verse']: v.get('hebrew', '') for v in match.full_text_hebrew}

        if is_doublet:
            md = f"#### ⚠ DOUBLET — {len(pairs)} nearly verbatim shared verses ({span})\n\n"
            md += (
                f"Psalm {analyzing_psalm} and Psalm {match.psalm_number} share these verses almost word for word. "
                "This is the most important intra-Psalter fact about this psalm: the finished guide MUST name the "
                "doublet explicitly and engage it — why the same text exists twice, and what each psalm's setting "
                "does to the shared material. The word-level variants below are first-rank material in their own right.\n\n"
            )
        else:
            md = f"#### Near-verbatim shared verse ({span})\n\n"

        md += f"Aligned verses (format: Psalm {analyzing_psalm} text ↔ Psalm {match.psalm_number} text):\n\n"
        for va, vb, sim in pairs:
            disp_a, keys_a = self._tokenize_verse(text_a.get(va, ''))
            disp_b, keys_b = self._tokenize_verse(text_b.get(vb, ''))
            diff = self._diff_verse_pair(disp_a, keys_a, disp_b, keys_b)
            if not keys_a or not keys_b:
                md += f"- {analyzing_psalm}:{va} // {match.psalm_number}:{vb} — {sim:.0%} shared\n"
            elif diff is None:
                md += f"- {analyzing_psalm}:{va} // {match.psalm_number}:{vb} — identical\n"
            else:
                md += f"- {analyzing_psalm}:{va} // {match.psalm_number}:{vb} — variants: {diff}\n"
        md += "\n"

        return md

    def _build_preamble(
        self,
        psalm_number: int,
        related_matches: List[RelatedPsalmMatch],
        doublet_map: Optional[Dict[int, List[Tuple[int, int, float]]]] = None
    ) -> str:
        """Build the preamble section for the Related Psalms Analysis."""
        psalm_numbers = ", ".join([str(m.psalm_number) for m in related_matches])

        md = f"## Related Psalms Analysis\n\n"
        md += f"Psalm {psalm_number} shares word/phrase connections with Psalms {psalm_numbers}.\n\n"

        # Doublets lead the section — a reader (human or model) must not have
        # to reconstruct "these psalms share whole verses" from atom lists.
        for match in related_matches:
            pairs = (doublet_map or {}).get(match.psalm_number)
            if pairs and len(pairs) >= DOUBLET_MIN_VERSES:
                span = self._compress_pair_runs(psalm_number, match.psalm_number, pairs)
                md += (f"**⚠ DOUBLET ALERT**: Psalm {match.psalm_number} shares {len(pairs)} nearly verbatim "
                       f"verses with this psalm ({span}) — see its entry below. "
                       "The guide must engage this relationship explicitly.\n\n")
        md += "**Model diptych** — Ps 25 + 34: both omit Vav stanza, add Pe stanza (→ פדה). "
        md += "Plea (25:22 פְּדֵה מִכֹּל צָרוֹתָיו) → Response (34:7 וּמִכׇּל־צָרוֹתָיו הוֹשִׁיעוֹ). "
        md += "Shared מִי־הָאִישׁ formula (25:12, 34:13), shared vocabulary (יִרְאַת ה׳, עֲנָוִים, טוֹב).\n\n"
        md += "**Your task**: Look for similar structural/thematic/call-and-response dynamics. "
        md += "Go beyond word matches — consider architecture, theme, life events, liturgical function, and meaningful DIFFERENCES. "
        md += "Reject spurious connections; incorporate genuine ones.\n\n"
        md += "---\n\n"

        return md

    def _remove_nikud(self, text: str) -> str:
        """Remove Hebrew vowel points (nikud) and cantillation marks."""
        # Unicode ranges for Hebrew vowel points and cantillation marks
        nikud_pattern = r'[\u0591-\u05C7]'
        return re.sub(nikud_pattern, '', text)

    def _extract_word_context(self, verse_text: str, root: str, context_words: int = 3) -> str:
        """
        Extract a snippet showing the root word with context_words on either side.

        Args:
            verse_text: Full verse text in Hebrew
            root: The root to find in the verse
            context_words: Number of words to show on either side (default 3)

        Returns:
            Snippet with the matched word and surrounding context
        """
        if not verse_text or not root:
            return "..."

        # Split verse into words
        words = verse_text.split()

        # Remove nikud from root for comparison
        root_consonantal = self._remove_nikud(root)

        # Find the first word containing the root (consonantal match)
        matched_index = -1
        for i, word in enumerate(words):
            word_consonantal = self._remove_nikud(word)
            if root_consonantal in word_consonantal:
                matched_index = i
                break

        # If no match found, just return first few words
        if matched_index == -1:
            snippet_words = words[:min(7, len(words))]
            return " ".join(snippet_words) + ("..." if len(words) > 7 else "")

        # Extract context: matched_index ± context_words
        start_idx = max(0, matched_index - context_words)
        end_idx = min(len(words), matched_index + context_words + 1)

        snippet_words = words[start_idx:end_idx]

        # Add ellipsis if truncated
        prefix = "..." if start_idx > 0 else ""
        suffix = "..." if end_idx < len(words) else ""

        return prefix + " ".join(snippet_words) + suffix

    def _format_single_match(
        self,
        analyzing_psalm: int,
        match: RelatedPsalmMatch,
        include_full_text: bool = True,
        shared_verse_pairs: Optional[List[Tuple[int, int, float]]] = None
    ) -> str:
        """Format a single related psalm match.

        Args:
            analyzing_psalm: The psalm number being analyzed
            match: The related psalm match data
            include_full_text: Whether to include the full Hebrew text (for size control)
            shared_verse_pairs: Near-verbatim verse alignments from
                _detect_shared_verses. A doublet (>= DOUBLET_MIN_VERSES pairs)
                replaces the atom-level listings with a headline + variant
                diffs; a single shared verse is flagged above the listings.
        """
        md = f"### Psalm {match.psalm_number} (Connection Score: {match.final_score:.2f})\n\n"

        # Doublet: state the conclusion and stop. Listing shared roots and
        # phrases between a psalm and its own doublet buries the one fact
        # that matters under thousands of trivially-true matches (this is
        # exactly how the Ps 60/108 relationship went unmentioned in a
        # finished guide despite 50K chars of matching atoms).
        if shared_verse_pairs and len(shared_verse_pairs) >= DOUBLET_MIN_VERSES:
            md += self._format_doublet_block(analyzing_psalm, match, shared_verse_pairs, is_doublet=True)
            md += ("*Word/phrase-level shared patterns omitted: these psalms share the verses themselves. "
                   "Analyze the doublet relationship — its extent, its variants, and what each psalm "
                   "does differently with the shared material.*\n\n")
            md += "---\n\n"
            return md

        if shared_verse_pairs:
            md += self._format_doublet_block(analyzing_psalm, match, shared_verse_pairs, is_doublet=False)

        # Filter roots early so we can check if we have any displayable content
        filtered_roots = [r for r in match.shared_roots if r.get('idf', 0) >= 1]

        # Full text of the related psalm (Hebrew only) - conditionally included
        if include_full_text:
            md += f"#### Full Text of Psalm {match.psalm_number}\n\n"

            for verse_data in match.full_text_hebrew:
                verse_num = verse_data['verse']
                hebrew = verse_data['hebrew']

                md += f"**Verse {verse_num}**: {hebrew}\n\n"
        else:
            md += f"*[Full text of Psalm {match.psalm_number} omitted for size - {len(match.full_text_hebrew)} verses]*\n\n"

        # Shared patterns
        md += f"#### Shared Patterns\n\n"

        # Contiguous phrases FIRST
        if match.contiguous_phrases:
            md += f"**Contiguous Phrases** ({len(match.contiguous_phrases)} found):\n\n"
            for phrase in match.contiguous_phrases:
                md += f"- **{phrase.get('hebrew', phrase.get('consonantal', 'N/A'))}** "
                md += f"({phrase.get('length', 0)}-word)\n"

                # Show matches from the analyzed psalm with verse context
                matches_a = phrase.get('matches_from_a', [])
                if matches_a:
                    md += f"  - Psalm {analyzing_psalm if analyzing_psalm < match.psalm_number else match.psalm_number} (×{len(matches_a)}): "
                    verses = []
                    for m in matches_a[:3]:
                        text = m.get('hebrew', m.get('text', 'N/A'))
                        # Truncate if over 100 chars
                        if len(text) > 100:
                            text = text[:100] + "..."
                        verses.append(f"v.{m.get('verse', '?')} {text}")
                    md += ", ".join(verses)
                    md += "\n"

                # Show matches from the related psalm with verse context
                matches_b = phrase.get('matches_from_b', [])
                if matches_b:
                    md += f"  - Psalm {match.psalm_number if analyzing_psalm < match.psalm_number else analyzing_psalm} (×{len(matches_b)}): "
                    verses = []
                    for m in matches_b[:3]:
                        text = m.get('hebrew', m.get('text', 'N/A'))
                        # Truncate if over 100 chars
                        if len(text) > 100:
                            text = text[:100] + "..."
                        verses.append(f"v.{m.get('verse', '?')} {text}")
                    md += ", ".join(verses)
                    md += "\n"

                md += "\n"

        # Skipgrams SECOND
        if match.skipgrams:
            md += f"**Skipgrams** ({len(match.skipgrams)} found):\n\n"
            md += "*Patterns where words appear in the same order but not necessarily adjacent*\n\n"
            for skipgram in match.skipgrams:
                # Use hebrew field from skipgram, fall back to consonantal
                skipgram_display = skipgram.get('hebrew', skipgram.get('matched_hebrew', skipgram.get('consonantal', 'N/A')))
                md += f"- **{skipgram_display}** "
                md += f"({skipgram.get('length', 0)}-word, "
                md += f"{skipgram.get('gap_word_count', 0)} gap)\n"

                # Show matches from the analyzed psalm with verse context
                matches_a = skipgram.get('matches_from_a', [])
                if matches_a:
                    md += f"  - Psalm {analyzing_psalm if analyzing_psalm < match.psalm_number else match.psalm_number} (×{len(matches_a)}): "
                    verses = []
                    for m in matches_a[:2]:
                        # V6 skipgrams use 'full_span_hebrew' not 'hebrew' or 'text'
                        text = m.get('full_span_hebrew', m.get('hebrew', m.get('text', 'N/A')))
                        # Truncate if over 100 chars
                        if len(text) > 100:
                            text = text[:100] + "..."
                        verses.append(f"v.{m.get('verse', '?')} {text}")
                    md += ", ".join(verses)
                    md += "\n"

                # Show matches from the related psalm with verse context
                matches_b = skipgram.get('matches_from_b', [])
                if matches_b:
                    md += f"  - Psalm {match.psalm_number if analyzing_psalm < match.psalm_number else analyzing_psalm} (×{len(matches_b)}): "
                    verses = []
                    for m in matches_b[:2]:
                        # V6 skipgrams use 'full_span_hebrew' not 'hebrew' or 'text'
                        text = m.get('full_span_hebrew', m.get('hebrew', m.get('text', 'N/A')))
                        # Truncate if over 100 chars
                        if len(text) > 100:
                            text = text[:100] + "..."
                        verses.append(f"v.{m.get('verse', '?')} {text}")
                    md += ", ".join(verses)
                    md += "\n"

                md += "\n"

        # Shared roots THIRD (sorted by IDF descending - best matches first).
        # Only the rarest MAX_DETAILED_ROOTS get verse contexts; the common
        # tail is named in one line. Every root ever used downstream came
        # from the rare end; the detailed common tail was pure bulk.
        if filtered_roots:
            # Sort by IDF descending
            sorted_roots = sorted(filtered_roots, key=lambda r: r.get('idf', 0), reverse=True)
            detailed_roots = sorted_roots[:MAX_DETAILED_ROOTS]
            overflow_roots = sorted_roots[MAX_DETAILED_ROOTS:]

            if overflow_roots:
                md += (f"**Shared Roots** ({len(sorted_roots)} found; "
                       f"{len(detailed_roots)} rarest shown with contexts):\n\n")
            else:
                md += f"**Shared Roots** ({len(sorted_roots)} found, sorted by relevance):\n\n"

            for root in detailed_roots:
                md += f"- Root: `{root.get('root', 'N/A')}`\n"

                # Show matches from analyzed psalm with context (matched word ± 3 words)
                matches_a = root.get('matches_from_a', [])
                if matches_a:
                    md += f"  - Psalm {analyzing_psalm if analyzing_psalm < match.psalm_number else match.psalm_number} (×{len(matches_a)}): "
                    snippets = []
                    for m in matches_a[:3]:
                        snippet = self._extract_word_context(m.get('hebrew', m.get('text', '')), root.get('root', ''), 3)
                        snippets.append(f"v.{m.get('verse', '?')} {snippet}")
                    md += ", ".join(snippets)
                    md += "\n"

                # Show matches from related psalm with context
                matches_b = root.get('matches_from_b', [])
                if matches_b:
                    md += f"  - Psalm {match.psalm_number if analyzing_psalm < match.psalm_number else analyzing_psalm} (×{len(matches_b)}): "
                    snippets = []
                    for m in matches_b[:3]:
                        snippet = self._extract_word_context(m.get('hebrew', m.get('text', '')), root.get('root', ''), 3)
                        snippets.append(f"v.{m.get('verse', '?')} {snippet}")
                    md += ", ".join(snippets)
                    md += "\n"

                md += "\n"

            if overflow_roots:
                names = ", ".join(f"`{r.get('root', '?')}`" for r in overflow_roots)
                md += (f"*Also shared ({len(overflow_roots)} more common roots, "
                       f"contexts omitted): {names}*\n\n")

        # If no patterns found at all (shouldn't happen, but just in case)
        if not filtered_roots and not match.contiguous_phrases and not match.skipgrams:
            md += "*No specific patterns documented, but overall connection score suggests potential relationship.*\n\n"

        md += "---\n\n"

        return md


def main():
    """Command-line interface for testing."""
    import argparse

    # Windows consoles default to cp1252, which can't print Hebrew.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    parser = argparse.ArgumentParser(description='Find related psalms')
    parser.add_argument('psalm', type=int, help='Psalm number')
    parser.add_argument('--connections-file',
                       default='data/analysis_results/top_550_connections_v6.json',
                       help='Path to connections file')

    args = parser.parse_args()

    librarian = RelatedPsalmsLibrarian(connections_file=args.connections_file)
    matches = librarian.get_related_psalms(args.psalm)

    if matches:
        print(f"\nFound {len(matches)} related psalms for Psalm {args.psalm}:\n")
        for match in matches:
            print(f"  - Psalm {match.psalm_number}: Score {match.final_score:.2f}")
            print(f"    Contiguous phrases: {len(match.contiguous_phrases)}")
            print(f"    Skipgrams: {len(match.skipgrams)}")

        print("\n" + "="*80)
        print("\nFormatted for research bundle:\n")
        print(librarian.format_for_research_bundle(args.psalm, matches))
    else:
        print(f"\nNo related psalms found for Psalm {args.psalm}")


if __name__ == '__main__':
    main()
