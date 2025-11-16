# Skipgram and Contiguous Phrase Quality Improvement Plan

**Date:** 2025-11-16
**Session Context:** Analysis of top_550_connections_skipgram_dedup_v4.json
**Objective:** Reduce noise and improve signal in phrase matching while preserving legitimately interesting connections

---

## Executive Summary

### Current State
- **43.9% of skipgrams** are formulaic (pure function words, divine names, or liturgical terms)
- **52.4% of contiguous phrases** are formulaic
- **Only 18.2%** of skipgrams have 2+ content words (truly interesting patterns)
- **37.9%** are borderline (1 content word mixed with divine names/function words)

### Key Finding
The current system captures too many patterns that are:
1. **Pure liturgical formulas** (e.g., "מזמור דוד", "נצח דוד") - psalm titles/headers
2. **Divine name + function word** (e.g., "יהוה אל", "כי יהוה") - theologically common but not distinctive
3. **Pure function word combinations** (e.g., "כי את", "אשר לא") - grammatical noise
4. **Borderline patterns** with minimal content (e.g., "ברך יהוה" = "bless YHWH")

---

## Detailed Findings

### Pattern Quality Distribution

#### Skipgrams (2,431 total patterns)
| Category | Count | % | Description |
|----------|-------|---|-------------|
| Borderline (1 content word) | 922 | 37.9% | Minimal content, often with divine names |
| Formulaic - Divine Names | 623 | 25.6% | Pure divine name + function word patterns |
| **Interesting - Multi-Content** | **421** | **17.3%** | **2+ content words - TARGET** |
| Formulaic - Function Only | 318 | 13.1% | Pure grammatical patterns |
| Formulaic - Liturgical | 125 | 5.1% | Psalm titles and liturgical formulas |
| Interesting - Content Focused | 22 | 0.9% | Content without divine names |

#### Contiguous Phrases (1,146 total patterns)
| Category | Count | % |
|----------|-------|---|
| Borderline (1 content word) | 379 | 33.1% |
| Formulaic - Divine Names | 321 | 28.0% |
| Formulaic - Function Only | 228 | 19.9% |
| **Interesting - Multi-Content** | **161** | **14.0%** |
| Formulaic - Liturgical | 52 | 4.5% |
| Interesting - Content Focused | 5 | 0.4% |

### Top Noise Patterns (High Frequency)

#### Skipgrams - Stoplist Candidates
```
יהוה אל      60 appearances  - YHWH + el (divine names)
כי יהוה      31 appearances  - ki + YHWH (because YHWH)
כי אתה       32 appearances  - ki + atah (because you)
אל אל        25 appearances  - el + el (repetition)
נצח דוד      24 appearances  - lamnatzeach david (title)
נצח מזמור דוד 20 appearances  - full title formula
יהוה כי      21 appearances  - YHWH + ki
אל יהוה      21 appearances  - to YHWH
```

#### Contiguous Phrases - Stoplist Candidates
```
כי את        41 appearances  - ki + et (function words)
את יהו       33 appearances  - et + YHWH (object marker)
יהו אל       30 appearances  - YHWH + el
זמור דוד     26 appearances  - mizmor david (title)
יהו אלה      25 appearances  - YHWH + elohim
כל יום       20 appearances  - kol yom (every day)
אל יהו       20 appearances  - to YHWH
```

### Examples of Interesting vs. Noise Patterns

#### NOISE - Divine Name Formulaic
```
יהוה אל (YHWH + el)
  Ps 35:22 "רָאִ֣יתָה יְ֭הֹוָה אַֽל־תֶּחֱרַ֑שׁ"
  Translation: "You have seen, O YHWH, do not be silent"
  Why noise: Pure theological address, extremely common

כי יהוה (because YHWH)
  Ps 69:34 "כִּי־שֹׁמֵ֣עַ אֶל־אֶבְיוֹנִ֣ים יְהֹוָ֑ה"
  Translation: "for YHWH hears the needy"
  Why noise: Common causal phrase, ubiquitous
```

#### NOISE - Liturgical
```
מזמור דוד (psalm of David)
  Appears in 26 psalm pairs
  Why noise: Superscription/title, not substantive content

נצח מזמור דוד (for the director, a psalm of David)
  Appears in 20 psalm pairs
  Why noise: Full title formula
```

#### INTERESTING - Multi-Content
```
לא ידע (not know)
  Ps 35:8 "תְּבוֹאֵ֣הוּ שׁוֹאָה֮ לֹֽא־יֵ֫דָ֥ע" (disaster he does not know)
  Ps 71:15 "כִּ֤י לֹ֖א יָדַ֣עְתִּי סְפֹרֽוֹת" (for I do not know numbers)
  Why interesting: Epistemological theme, theologically significant

ראה עני (see affliction)
  Ps 25:18 "רְאֵ֣ה עׇ֭נְיִי וַעֲמָלִ֑י" (see my affliction and trouble)
  Ps 31:8 "רָ֭אִיתָ אֶת־עׇנְיִ֑י" (you have seen my affliction)
  Why interesting: Divine compassion theme, lament motif

מי נתן שוב גיל (who will give restoration [and] rejoicing)
  Complex theological expression about divine deliverance
  Why interesting: Multiple content words, distinctive theology
```

---

## Proposed Improvements

### Priority 1: Content Word Filtering (HIGHEST IMPACT)

**Rationale:** 43.9% of skipgrams have ZERO content words. This is pure noise.

**Implementation:**
1. **Create Hebrew word classifier** in `src/hebrew_analysis/word_classifier.py`
   - Divine names: יהוה, אלהים, אל, אדני, יה, שדי, etc.
   - Function words: prepositions (ב, ל, מ, על, אל, את, עם, כ), conjunctions (כי, ו, אם, אשר), particles (לא, כל, גם)
   - Liturgical: מזמור, שיר, תפלה, הללויה, סלה, למנצח, דוד, אסף, בני קרח
   - Everything else (length >= 3): content words (verbs, nouns, adjectives)

2. **Add content word filtering to extraction**
   - Modify `skipgram_extractor_v4.py` to track content word count
   - Add field: `content_word_count` to each pattern
   - Add field: `content_word_ratio` (content_words / total_words)

3. **Filtering Thresholds:**
   ```python
   # OPTION A: Conservative (recommended starting point)
   - Contiguous 2-word: require >= 1 content word
   - Contiguous 3+word: require >= 1 content word
   - Skipgram 2-word: require >= 1 content word
   - Skipgram 3+word: require >= 2 content words

   # OPTION B: Aggressive (if still too much noise)
   - Contiguous 2-word: require >= 1 content word
   - Contiguous 3+word: require >= 2 content words
   - Skipgram 2-word: require >= 2 content words (eliminates all 2-word skipgrams without content)
   - Skipgram 3+word: require >= 2 content words
   ```

4. **Implementation Strategy:**
   - Apply filter AFTER extraction, BEFORE scoring
   - Store filtered patterns separately for analysis
   - Track statistics: how many patterns removed, impact on scores

**Expected Impact:**
- Remove ~44% of skipgrams (formulaic patterns with 0 content words)
- Remove ~52% of contiguous phrases (formulaic)
- Preserve 100% of truly interesting multi-content patterns

---

### Priority 2: Pattern Stoplist (TARGETED REMOVAL)

**Rationale:** Some patterns are so common they provide no discriminatory value, even if they have content.

**Implementation:**
1. **Create stoplist file:** `src/hebrew_analysis/data/pattern_stoplist.json`
   ```json
   {
     "version": "1.0.0",
     "last_updated": "2025-11-16",
     "skipgrams": [
       "יהוה אל",
       "כי יהוה",
       "כי אתה",
       "אל אל",
       "נצח דוד",
       "נצח מזמור דוד",
       "מזמור דוד",
       "יהוה כי",
       "אל יהוה",
       "יהוה אלהים",
       "את יהוה",
       "יהוה עש",
       "כל יום",
       "אשר לא",
       "הלל יה",
       "ברך יהוה"
     ],
     "contiguous": [
       "כי את",
       "את יהו",
       "יהו אל",
       "זמור דוד",
       "יהו אלה",
       "כל יום",
       "אל יהו",
       "יהו כי",
       "לו יה",
       "אשר לא"
     ]
   }
   ```

2. **Load stoplist in extraction pipeline**
   - Check each pattern against stoplist AFTER deduplication
   - Track separately: `patterns_filtered_by_stoplist`
   - Store filtered patterns for human review

3. **Tuning strategy:**
   - Start with patterns appearing in 20+ psalm pairs
   - Review filtered results after each iteration
   - Add/remove patterns based on false positive analysis

**Expected Impact:**
- Remove highest-frequency noise patterns
- Minimal impact on interesting connections (rare patterns preserved)
- Easy to tune and adjust

---

### Priority 3: IDF Weighting Enhancement (SCORING IMPROVEMENT)

**Rationale:** Current IDF scoring helps but doesn't go far enough. Common words should be penalized more heavily.

**Current Implementation:**
- IDF calculated per root
- Used in scoring but not in filtering
- Modest impact on final scores

**Proposed Enhancement:**
1. **Calculate pattern-level IDF**
   - Not just per root, but per complete pattern
   - Pattern IDF = -log(pattern_frequency / total_patterns)
   - Store in pattern metadata

2. **IDF-based filtering threshold**
   ```python
   # Filter patterns with very low IDF (too common)
   MIN_PATTERN_IDF = 1.5  # Adjustable threshold

   # Example:
   # Pattern appears in 50/550 pairs → IDF = -log(50/550) ≈ 1.0 → FILTERED
   # Pattern appears in 5/550 pairs → IDF = -log(5/550) ≈ 2.0 → KEPT
   ```

3. **Scoring adjustment**
   - Multiply pattern value by IDF weight
   - `adjusted_value = base_value * (pattern_idf / max_idf)`
   - Preserves relative ordering while penalizing common patterns

**Expected Impact:**
- Reduces influence of moderately common patterns
- Complements content word filtering
- Tunable via MIN_PATTERN_IDF threshold

---

### Priority 4: Enhanced Scoring for Multi-Content Patterns (SIGNAL BOOST)

**Rationale:** Patterns with 2+ content words are inherently more interesting. Reward them.

**Implementation:**
1. **Add content bonus to scoring**
   ```python
   def calculate_pattern_value(length, gap_count, content_word_count):
       # Current base values
       if length == 2:
           base = 1.0
       elif length == 3:
           base = 2.0
       else:
           base = 3.0

       # Apply gap penalty (existing)
       gap_penalty = min(0.1 * gap_count, 0.5)
       value = base * (1.0 - gap_penalty)

       # NEW: Content word bonus
       if content_word_count >= 3:
           content_bonus = 1.5  # 50% bonus for 3+ content words
       elif content_word_count == 2:
           content_bonus = 1.25  # 25% bonus for 2 content words
       else:
           content_bonus = 1.0  # No bonus

       return value * content_bonus
   ```

2. **Track content metrics in scores**
   - Add to output: `avg_content_words_per_pattern`
   - Add to output: `content_word_ratio` (for the psalm pair)
   - Use in analysis and ranking

**Expected Impact:**
- Boosts truly interesting multi-content patterns
- Helps distinguish borderline cases
- Makes ranking more semantically meaningful

---

### Priority 5: Gap Penalty Refinement (MINOR TWEAK)

**Rationale:** Current gap penalty (10% per word, max 50%) is reasonable but could be tuned.

**Current Implementation:**
- 10% penalty per gap word
- Maximum 50% penalty
- Applied to skipgrams only

**Proposed Adjustment:**
1. **Consider different penalties for different pattern types**
   ```python
   # Contiguous (gap=0): No penalty (current behavior)
   # 2-word skipgrams: 15% per gap (stricter)
   # 3+word skipgrams: 10% per gap (current)

   # Rationale: 2-word skipgrams are already weak signals
   # If they have large gaps, they're even weaker
   ```

2. **Consider content-based gap tolerance**
   ```python
   # If pattern has 2+ content words, use lighter gap penalty (8%)
   # If pattern has 1 content word, use standard penalty (10%)
   # If pattern has 0 content words, use heavy penalty (15%)
   # (but these should be filtered anyway by Priority 1)
   ```

**Expected Impact:**
- Minor improvement to ranking quality
- More nuanced treatment of skipgrams
- Can be implemented after Priority 1-4

---

## Implementation Roadmap

### Phase 1: Core Filtering (Recommended First)
**Goal:** Remove obvious noise with minimal risk

1. ✅ Create `word_classifier.py` with Hebrew linguistic categories
2. ✅ Modify `skipgram_extractor_v4.py` to add content word analysis
3. ✅ Add filtering logic: require >= 1 content word for all patterns
4. ✅ Re-run extraction and compare statistics
5. ✅ Review samples of filtered patterns (sanity check)

**Files Modified:**
- `src/hebrew_analysis/word_classifier.py` (NEW)
- `scripts/statistical_analysis/skipgram_extractor_v4.py`
- `scripts/statistical_analysis/contiguous_extractor_v4.py`

**Expected Outcome:**
- ~44% reduction in skipgram patterns
- ~52% reduction in contiguous patterns
- Cleaner, more meaningful connection data

### Phase 2: Targeted Stoplist (After Phase 1)
**Goal:** Remove remaining high-frequency formulaic patterns

1. ✅ Create `pattern_stoplist.json` with initial list
2. ✅ Modify extractors to load and apply stoplist
3. ✅ Re-run extraction
4. ✅ Analyze remaining patterns, tune stoplist
5. ✅ Iterate until satisfied

**Files Modified:**
- `src/hebrew_analysis/data/pattern_stoplist.json` (NEW)
- `scripts/statistical_analysis/skipgram_extractor_v4.py`
- `scripts/statistical_analysis/contiguous_extractor_v4.py`

**Expected Outcome:**
- Additional 10-15% reduction in patterns
- Removal of most egregious formulaic noise
- Tunable via JSON file (no code changes needed)

### Phase 3: Scoring Enhancements (After Phase 2)
**Goal:** Improve ranking quality of remaining patterns

1. ✅ Implement pattern-level IDF calculation
2. ✅ Add IDF weighting to scoring
3. ✅ Implement content word bonus in scoring
4. ✅ Re-run scoring on filtered data
5. ✅ Compare Top 500/550 before and after

**Files Modified:**
- `scripts/statistical_analysis/enhanced_scorer_skipgram_dedup_v4.py`

**Expected Outcome:**
- Better ranking of truly interesting patterns
- More meaningful final scores
- Easier to identify high-value connections

### Phase 4: Analysis and Tuning (Ongoing)
**Goal:** Validate improvements and iterate

1. ✅ Compare old vs. new top connections
2. ✅ Spot-check specific psalm pairs (e.g., Ps 25-34)
3. ✅ Measure precision/recall on known interesting pairs
4. ✅ Adjust thresholds based on results
5. ✅ Document findings

**Expected Outcome:**
- Confidence in improvements
- Tuned parameters
- Better understanding of what makes connections interesting

---

## Alternative Approaches (Not Recommended Initially)

### Machine Learning Classifier
**Idea:** Train a model to classify patterns as interesting/noise
**Pros:** Could capture nuanced patterns
**Cons:**
- Requires labeled training data (significant manual effort)
- Overkill for current problem
- Less interpretable than rule-based approach

**Recommendation:** Defer until rule-based approaches exhausted

### Part-of-Speech Tagging
**Idea:** Use full POS tagging to identify verbs, nouns, etc.
**Pros:** More precise than word lists
**Cons:**
- Requires external Hebrew POS tagger
- ETCBC data might have POS info but complex to use
- Current word list approach likely 90% accurate

**Recommendation:** Consider if word list approach proves insufficient

### Semantic Clustering
**Idea:** Group related patterns (e.g., all "divine deliverance" patterns)
**Pros:** Could reveal thematic connections
**Cons:**
- Complex implementation
- Requires semantic resources (thesaurus, ontology)
- Premature for current stage

**Recommendation:** Interesting for future research, not for noise reduction

---

## Success Metrics

### Quantitative
- **Noise reduction:** 40-50% reduction in total patterns
- **Precision improvement:** Higher % of multi-content patterns in top connections
- **Distribution shift:** More patterns with 2+ content words in top rankings
- **Stoplist coverage:** <5% of patterns removed by stoplist (most removed by content filter)

### Qualitative
- **Spot checks:** Review 20 random patterns from top 100 - should be substantive
- **Theological review:** Known interesting pairs (e.g., Ps 25-34) maintain high rankings
- **False positive rate:** <10% of remaining patterns are obviously formulaic

### Analysis Outputs
- Generate comparison report: old vs. new top 100
- Pattern quality distribution before/after
- Examples of patterns removed and reasons
- Examples of patterns promoted and reasons

---

## Risk Mitigation

### Risk 1: Over-filtering
**Concern:** Removing patterns that are actually interesting
**Mitigation:**
- Start with conservative thresholds (require only 1 content word)
- Store filtered patterns separately for review
- Iterate based on analysis of false negatives
- Can always relax filters if too strict

### Risk 2: Under-filtering
**Concern:** Still too much noise after improvements
**Mitigation:**
- Multi-phase approach allows incremental tightening
- Stoplist can be expanded iteratively
- Content word threshold can be increased (e.g., require 2 for skipgrams)

### Risk 3: Missed interesting patterns
**Concern:** Some theologically significant patterns use divine names
**Example:** "ברך יהוה" (bless YHWH) appears in 10 pairs - formulaic or interesting?
**Mitigation:**
- Content word bonus helps: "ברך" is a content word (verb)
- Pattern will be kept (has 1 content word)
- Scoring will appropriately weight based on frequency
- Manual review of borderline cases

---

## Next Steps

1. **Review this plan** - Confirm approach and priorities
2. **Phase 1 Implementation** - Build word classifier and content filtering
3. **Test run** - Extract and score on current data with new filters
4. **Analysis** - Compare results, identify issues
5. **Iterate** - Refine filters and thresholds
6. **Phase 2-3** - Implement stoplist and scoring enhancements
7. **Final validation** - Comprehensive review of top connections

---

## Appendix: Pattern Analysis Statistics

### Full Distribution (from linguistic_quality_analysis.py)

**Skipgrams (2,431 total):**
- Borderline (1 content): 922 (37.9%)
- Formulaic divine: 623 (25.6%)
- Interesting multi-content: 421 (17.3%) ← **TARGET PRESERVE**
- Formulaic function: 318 (13.1%)
- Formulaic liturgical: 125 (5.1%)
- Interesting content-focused: 22 (0.9%)

**Contiguous (1,146 total):**
- Borderline (1 content): 379 (33.1%)
- Formulaic divine: 321 (28.0%)
- Formulaic function: 228 (19.9%)
- Interesting multi-content: 161 (14.0%) ← **TARGET PRESERVE**
- Formulaic liturgical: 52 (4.5%)
- Interesting content-focused: 5 (0.4%)

### Top 30 Highest-Frequency Patterns
See analysis scripts output for full lists. Key observations:
- Skipgrams: Top 10 all formulaic (divine names, titles, function words)
- Contiguous: Top 10 all formulaic
- First interesting pattern appears around rank 30-40
- Clear frequency cliff: formulaic = 10-60 appearances, interesting = 1-9 appearances

---

**Document Version:** 1.0
**Analysis Scripts Used:**
- `analyze_skipgram_quality.py`
- `examine_pattern_examples.py`
- `linguistic_quality_analysis.py`

**Data Source:** `data/analysis_results/top_550_connections_skipgram_dedup_v4.json`
