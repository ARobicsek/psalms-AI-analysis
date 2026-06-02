"""
Distinctive-root selection for concordance searches.

Session 350: The concordance was being driven almost exclusively by multi-word
*collocations* lifted verbatim from a verse. Those rarely recur anywhere else in
Tanakh, so ~76% of searches returned only the source verse itself or nothing
(measured across Psalms 54-58). The concordance's real value is tracing a single
*distinctive root/lexeme* across the corpus — that is what surfaces non-obvious
intertexts (e.g. פלג -> Gen 10-11 Babel; ימיש -> Exod 13:22) that single-word
BDB/Klein lookups and an LLM's training data do not already supply.

This module picks, from a lexical insight (its exact phrase plus the analyst's
morphological variants), the single most *distinctive* content word worth tracing
on its own — "distinctive" being operationalised as Tanakh frequency: rare enough
to be meaningful, common enough to actually recur.

Session 351: the caller now passes `librarian.lemma_frequency` as `frequency_fn`, so
distinctiveness is measured on the BHSA-derived lemma (all inflections counted as one)
rather than the surface form, and the chosen word is resolved to its lemma at search
time (see src/concordance/search.py `_resolve_lemma`). The earlier "deliberately
conservative, no prefix stripping" caveat no longer applies — prefix/suffix stripping
is now exact via morphology.
"""

import re
from typing import Callable, List, Optional, Tuple

# Hebrew letter range and diacritics
_HEB_LETTERS = r'א-ת'
_DIACRITICS = re.compile(r'[֑-ׇ]')
_NON_LETTERS = re.compile(rf'[^{_HEB_LETTERS}]')

# Function words / particles and very common words that are never worth tracing
# as a standalone root. The frequency cap below already filters most high-frequency
# words; this list catches short, semantically empty forms that can slip under the
# cap in a specific consonantal spelling, plus the BDB "avoid" list of common nouns.
STOPLIST = {
    # particles / pronouns / prepositions that survive word-splitting
    'לא', 'את', 'כי', 'אשר', 'כל', 'על', 'אל', 'מן', 'אם', 'או', 'גם', 'רק',
    'אך', 'הן', 'הנה', 'זה', 'זאת', 'מה', 'מי', 'לי', 'לו', 'לך', 'בו', 'בה',
    'כן', 'עד', 'יש', 'אין', 'הוא', 'היא', 'הם', 'אני', 'אתה', 'נא', 'אז',
    'יהוה', 'אלהים', 'אדני', 'אלה',
    # BDB common-noun avoid list (only worth tracing in unusual collocation, not alone)
    'יום', 'איש', 'ארץ', 'שמים', 'לב', 'יד', 'עין', 'פה', 'דרך', 'אדם', 'בן',
    'עם', 'דבר', 'בית', 'שם',
    # very common verbs
    'היה', 'אמר', 'עשה', 'נתן', 'בוא', 'הלך', 'ראה', 'ידע', 'נשא',
}


def to_consonantal(word: str) -> str:
    """Strip vowels/cantillation and any non-letter chars, returning bare consonants."""
    if not word:
        return ''
    word = word.replace('־', ' ')  # maqqef -> space (handled by caller's split)
    word = _DIACRITICS.sub('', word)
    word = _NON_LETTERS.sub('', word)
    return word


def _is_candidate(consonantal: str) -> bool:
    """A word is a root-trace candidate if it has >=3 letters and is not a stopword."""
    return len(consonantal) >= 3 and consonantal not in STOPLIST


def candidate_words(phrase: str, variants: Optional[List[str]] = None) -> List[str]:
    """
    Collect distinct single-word consonantal candidates from a phrase and its variants.

    Phrase words and any single-word variants are pooled. Multi-word variants are
    ignored (we only trace single roots here). Order preserved, deduplicated.
    """
    out: List[str] = []
    seen = set()

    def _add(raw: str):
        # Split on whitespace AFTER converting maqqef to space
        for piece in to_consonantal(raw).split() if ' ' in raw else [to_consonantal(raw)]:
            piece = piece.strip()
            if piece and _is_candidate(piece) and piece not in seen:
                seen.add(piece)
                out.append(piece)

    for w in (phrase or '').replace('־', ' ').split():
        _add(w)
    for v in (variants or []):
        # only single-word variants contribute a root candidate
        if len((v or '').replace('־', ' ').split()) == 1:
            _add(v)
    return out


def select_distinctive_roots(
    phrase: str,
    variants: Optional[List[str]],
    frequency_fn: Callable[[str], int],
    min_freq: int = 2,
    max_freq: int = 120,
    top_n: int = 1,
) -> List[Tuple[str, int]]:
    """
    Pick the most distinctive single root(s) from a lexical insight to trace alone.

    "Distinctive" = lowest Tanakh frequency within [min_freq, max_freq]:
      - freq < min_freq (hapax, =1): occurs only at the source -> no external value,
        skipped (the word's rarity is already captured by BDB/Klein).
      - freq > max_freq: too common (e.g. divine names, particles) -> floods/conflates.

    Args:
        phrase: exact phrase from the lexical insight
        variants: analyst-supplied morphological variants (may contain the bare root)
        frequency_fn: maps a consonantal word -> its Tanakh occurrence count
        min_freq, max_freq: distinctiveness window
        top_n: how many roots to return (rarest first)

    Returns:
        List of (consonantal_root, frequency), rarest first, length <= top_n.
    """
    scored: List[Tuple[str, int]] = []
    for cand in candidate_words(phrase, variants):
        try:
            freq = frequency_fn(cand)
        except Exception:
            continue
        if min_freq <= freq <= max_freq:
            scored.append((cand, freq))
    # Session 351: rank by TRUE (lemma) frequency — rarest = most distinctive. When
    # `frequency_fn` is lemma-based (librarian.lemma_frequency), a rare conjugated form
    # like אַרְחִיק scores its lexeme's real frequency rather than a deceptively low surface
    # count, so the old "prefer 3-letter forms" length bucket is no longer needed; word
    # length is kept only as a deterministic tie-break.
    scored.sort(key=lambda t: (t[1], len(t[0])))
    # dedupe preserving order
    result: List[Tuple[str, int]] = []
    seen = set()
    for word, freq in scored:
        if word not in seen:
            seen.add(word)
            result.append((word, freq))
        if len(result) >= top_n:
            break
    return result
