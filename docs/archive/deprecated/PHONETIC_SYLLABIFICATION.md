# Hebrew Syllabification in the Psalms Commentary Pipeline

**Date**: 2025-10-21  
**Purpose**: Document the syllabification rules and implementation

---

## Overview

The `PhoneticAnalyst` now includes automatic syllabification based on reconstructed Biblical Hebrew phonology. This enables advanced prosodic analysis in the commentary.

---

## Syllabification Rules

Based on **Gesenius' Hebrew Grammar §26-27** and **Joüon-Muraoka §27**.

### Rule 1: Every Syllable Has One Vowel
The vowel is the **nucleus** of the syllable. Hebrew does not permit diphthongs or syllables without vowels.

**Vowels counted:** a, ā, e, ē, i, ī, o, ō, u, ū, ə

### Rule 2: Every Syllable Begins with a Consonant
Hebrew strongly prefers consonant onsets. Word-initial vowels are rare and typically have an implied glottal stop (alef or ayin).

**Example:** אֱלֹהִים (*elōhīm*) begins with ֱ (hatef segol), but the alef provides the onset.

### Rule 3: Open Syllables Preferred
When possible, syllables remain **open** (CV pattern) rather than closed (CVC).

**Example:** שָׁלוֹם = `shā-lōm` (not *`shāl-ōm`*)

### Rule 4: Geminated Consonants Split
When a consonant is geminated (dagesh forte), it is **ambisyllabic** — it closes one syllable and opens the next.

**Example:** חַנּוּן = `khan-nūn` (not *`kha-nūn`* or *`khann-ūn`*)

Phonemes: [kh, a, n, n, ū, n]
Syllables: [kh, a, n] + [n, ū, n]
└─ Closes Opens ─┘


### Rule 5: Final Consonants Close
Word-final consonants always close the final syllable.

**Example:** מֶלֶךְ = `me-lekh` (final *kh* closes second syllable)

---

## Syllable Patterns

### CV (Open Syllable)
**Pattern:** Consonant + Vowel  
**Hebrew:** שָׁ in שָׁלוֹם  
**Transcription:** `shā` in `shā-lōm`  
**Frequency:** Very common (preferred pattern)

### CVC (Closed Syllable)
**Pattern:** Consonant + Vowel + Consonant  
**Hebrew:** לֶךְ in מֶלֶךְ  
**Transcription:** `lekh` in `me-lekh`  
**Frequency:** Common, especially word-finally

### V (Vowel-Only)
**Pattern:** Vowel alone (word-initial)  
**Hebrew:** Initial ֱ in אֱלֹהִים  
**Transcription:** `e` in `e-lō-hīm`  
**Frequency:** Rare (usually has weak consonant)

---

## Complete Examples

### Example 1: תְּהִלָּה (*təhillāh*, "praise")

**Phonemes:** `[t, ə, h, i, l, l, ā, h]`

**Syllabification:**
1. Start: `t` (consonant)
2. Add `ə` (vowel) → nucleus found
3. Look ahead: `h` (consonant), then `i` (vowel)
4. Pattern: V-C-V → close before consonant
   - **Syllable 1:** `[t, ə]` = `tə`
5. Start new: `h` (consonant)
6. Add `i` (vowel) → nucleus found
7. Look ahead: `l`, then `l` (GEMINATION!)
8. Split gemination: add first `l` to current, start next with second `l`
   - **Syllable 2:** `[h, i, l]` = `hil`
9. Current: `[l]` (from split)
10. Add `ā` (vowel) → nucleus found
11. Look ahead: `h` (final consonant)
12. Add `h` to close
    - **Syllable 3:** `[l, ā, h]` = `lāh`

**Result:** `tə-hil-lāh`

---

### Example 2: בְּרֵאשִׁית (*bərēshīt*, "in the beginning")

**Phonemes:** `[b, ə, r, ē, sh, ī, t]`

**Syllabification:**
1. `b` (consonant)
2. `ə` (vowel) → nucleus
3. Look ahead: `r` (consonant), `ē` (vowel)
4. Pattern: V-C-V → close before
   - **Syllable 1:** `[b, ə]` = `bə`
5. `r` (consonant)
6. `ē` (vowel) → nucleus
7. Look ahead: `sh` (consonant), `ī` (vowel)
8. Pattern: V-C-V → close before
   - **Syllable 2:** `[r, ē]` = `rē`
9. `sh` (consonant)
10. `ī` (vowel) → nucleus
11. Look ahead: `t` (final consonant)
12. Add `t` to close
    - **Syllable 3:** `[sh, ī, t]` = `shīt`

**Result:** `bə-rē-shīt`

---

### Example 3: חַנּוּן (*khannūn*, "gracious")

**Phonemes:** `[kh, a, n, n, ū, n]`

**Syllabification:**
1. `kh` (consonant)
2. `a` (vowel) → nucleus
3. Look ahead: `n`, then `n` (GEMINATION!)
4. Split: add first `n` to current (closes), start next with second `n`
   - **Syllable 1:** `[kh, a, n]` = `khan`
5. Current: `[n]` (from split)
6. Add `ū` (vowel) → nucleus
7. Look ahead: `n` (final consonant)
8. Add `n` to close
   - **Syllable 2:** `[n, ū, n]` = `nūn`

**Result:** `khan-nūn`

**Prosodic Note:** The geminated nun creates emphasis and weight, appropriate for a theological term of divine mercy.

---

## Use in Commentary

### Meter Analysis
> The three-syllable structure of *təhillāh* (tə-hil-lāh) creates a balanced, rhythmic quality, with the geminated lamed in the second syllable adding weight to the root הלל ("to praise").

### Prosodic Weight
> The word *khannūn* ("gracious") features ambisyllabic gemination (khan-nūn), where the doubled nun adds sonorous emphasis, reinforcing the theological significance of divine compassion.

### Syllable Structure and Meaning
> The flowing, open syllables of *bərēshīt* (bə-rē-shīt, "in the beginning") create a sense of expansiveness and potential, phonetically mirroring the cosmic opening of creation.

### Comparative Analysis
> Unlike the light, open syllables of *shālōm* (shā-lōm, "peace"), the closed final syllable of *melekh* (me-lekh, "king") creates a more grounded, authoritative phonetic quality.

---

## Implementation Details

### Algorithm
The syllabification algorithm in `PhoneticAnalyst._syllabify()` implements these rules using a **vowel-driven approach**:

1. Iterate through phonemes
2. When vowel found (nucleus), determine syllable boundary
3. Check following consonants:
   - Gemination (C₁C₁) → split across boundary
   - CC cluster before vowel → keep cluster together
   - CC cluster before consonant → close with first C
   - Single final C → close syllable

### Output Format
```python
{
  "syllables": [["t", "ə"], ["h", "i", "l"], ["l", "ā", "h"]],
  "syllable_transcription": "tə-hil-lāh"
}
```

### Integration
Syllable data is automatically generated for all verses and passed to:
- `SynthesisWriter` (for prosodic analysis)
- `MasterEditor` (for verification)

---

## Linguistic References

1. **Gesenius' Hebrew Grammar (GKC)** §26-27: "Of the Syllable and the Tone"
2. **Joüon-Muraoka** §27: "Syllabication"
3. **Lambdin, *Introduction to Biblical Hebrew*** §4: "Syllabification"
4. **Khan, *A Short Introduction to the Tiberian Masoretic Bible*** pp. 45-58

---

## Future Enhancements

### Stress Marking
Add primary stress indicators based on:
- Masoretic accent marks (te'amim)
- Milraʿ (final stress) vs. milʿel (penultimate stress) patterns

**Example:** תְּהִלָּה → tə-hil-**LĀH** (stress on final syllable)

### Syllable Weight
Calculate syllable weight (mora count) for metrical analysis:
- Light syllables (CV): 1 mora
- Heavy syllables (CVV, CVC): 2 morae
- Superheavy syllables (CVVC, CVCC): 3 morae

### Metrical Patterns
Identify common metrical patterns in Hebrew poetry:
- Qinah meter (3+2)
- Balanced meter (3+3)
- Asymmetric patterns

---

**This syllabification system enables graduate-level prosodic analysis of Hebrew poetry while remaining accessible to educated lay readers.**