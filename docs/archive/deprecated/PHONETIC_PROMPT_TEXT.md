# Complete Phonetic Transcription Prompt Text

**Ready-to-use prompt text for insertion into the Micro Analyst**

---

## Insert Location

**File**: `c:\Users\ariro\OneDrive\Documents\Psalms\src\agents\micro_analyst.py`

**Prompt**: `DISCOVERY_PASS_PROMPT`

**Position**: After the "DISCOVERY TASK:" section and before "OUTPUT FORMAT:"

---

## Exact Text to Insert

```python
---

## PHONETIC TRANSCRIPTION TASK

For each verse, provide an ACCURATE PHONETIC TRANSCRIPTION of the Hebrew text.

**Why this matters**: Downstream editors (Synthesizer and Master Editor) need accurate phonetic data to avoid errors like claiming "soft f" when the text has a hard "p" (פּ with dagesh), or "sh" when it's actually "kh" (ך final khaf). Your transcriptions will be the authoritative source for all phonetic commentary.

### Transcription System

Use this simplified IPA-like system for accessibility:

**CONSONANTS**:

| Hebrew | With Dagesh | Without Dagesh | Final Form | Notes |
|--------|-------------|----------------|------------|-------|
| ב | **b** | **v** | - | bet/vet |
| ג | **g** | **g** | - | gimel |
| ד | **d** | **d** | - | dalet |
| ה | **h** | **h** | - | he |
| ו | **v** | - | - | vav |
| ז | **z** | - | - | zayin |
| ח | **kh** | - | - | chet (guttural) |
| ט | **t** | - | - | tet |
| י | **y** | - | - | yod |
| כ | **k** | **kh** | **kh** (ך) | kaf/khaf |
| ל | **l** | - | - | lamed |
| מ | **m** | - | **m** (ם) | mem |
| נ | **n** | - | **n** (ן) | nun |
| ס | **s** | - | - | samekh |
| ע | **'** | - | - | ayin (glottal) |
| פ | **p** | **f** | **f** (ף) | pe/fe |
| צ | **ts** | - | **ts** (ץ) | tsade |
| ק | **k** | - | - | qof |
| ר | **r** | - | - | resh |
| שׁ | **sh** | - | - | shin |
| שׂ | **s** | - | - | sin |
| ת | **t** | **t** | - | tav |

**VOWELS**:

| Vowel | Symbol | Transcription | Example |
|-------|--------|---------------|---------|
| Patakh, Qamets | ַ◌ ָ◌ | **a** | בַּיִת = ba-yit |
| Tsere, Segol | ֵ◌ ֶ◌ | **e** | מֶלֶךְ = me-lekh |
| Khiriq | ִ◌ | **i** | דִּין = din |
| Kholam | ֹ◌ וֹ | **o** | קוֹל = kol |
| Qibbuts, Shureq | ֻ◌ וּ | **u** | רוּחַ = ru-akh |
| Vocal Shewa | ְ◌ | **e** | בְּרֵאשִׁית = be-re-shit |
| Silent Shewa | ְ◌ | (silent) | יִשְׂרָאֵל = yis-ra-el |
| Khatef Patakh | ֲ◌ | **a** | אֲנִי = a-ni |
| Khatef Segol | ֱ◌ | **e** | אֱלֹהִים = e-lo-him |
| Khatef Qamets | ֳ◌ | **o** | חֳלִי = kho-li |

**FORMATTING RULES**:

1. **Syllable breaks**: Use hyphens
   - Example: פּוֹתֵחַ = `po-te-akh` (3 syllables)

2. **Maqqef** (word joiner ־): Treat joined words as single unit with hyphens
   - Example: אֶת־יָדֶךָ = `et-ya-de-kha` (not `et ya-de-kha`)

3. **Divine name** (יְהוָה): Transcribe as pronounced liturgically
   - Use: `a-do-nai` (standard)
   - Alternative: `[YHVH]` if you want to mark it explicitly

4. **Doubled consonants** (dagesh forte): Double the letter
   - Example: חַנּוּן = `khan-nun` (נ doubled)
   - Example: תְּהִלָּה = `te-hil-la` (ל doubled)

5. **Silent shewa**: Don't transcribe
   - Example: יִשְׂרָאֵל = `yis-ra-el` (not `yis-re-ra-el`)

### Critical Examples (Study These Carefully)

**Example 1**: פּוֹתֵחַ אֶת־יָדֶךָ

**Transcription**: `po-te-akh et-ya-de-kha`

**Key phonetic features**:
- **פּ** with dagesh = hard **p** (NOT soft "f")
- **ח** final = guttural **kh**
- **ך** final khaf = **kh** (NOT "sh")
- Maqqef joins אֶת־יָדֶךָ as single unit

**Wrong transcriptions to avoid**:
- ❌ `fo-te-akh` (פּ is **p**, not **f**)
- ❌ `po-te-ash` (ח is **kh**, not **sh**)
- ❌ `et-ya-de-sha` (ך is **kh**, not **sh**)

---

**Example 2**: חַנּוּן וְרַחוּם יְהוָה

**Transcription**: `khan-nun ve-ra-khum a-do-nai`

**Key phonetic features**:
- **ח** = guttural **kh** (NOT plain "h")
- **נּ** doubled (dagesh forte) = **nn**
- **יְהוָה** = divine name = `a-do-nai` (as pronounced)

**Wrong transcriptions to avoid**:
- ❌ `han-nun` (ח is **kh**, not **h**)
- ❌ `khan-un` (נּ is doubled = **nn**)
- ❌ `ye-ho-vah` (use liturgical pronunciation `a-do-nai`)

---

**Example 3**: תְּהִלָּה לְדָוִד

**Transcription**: `te-hil-la le-da-vid`

**Key phonetic features**:
- **תּ** with dagesh = **t**
- **לּ** doubled (dagesh forte) = **ll**
- Syllable breaks: `te-hil-la` (3 syllables), `le-da-vid` (3 syllables)

**Wrong transcriptions to avoid**:
- ❌ `te-hil-a` (לּ is doubled = **ll**)
- ❌ `tehilla` (missing syllable breaks)

---

**Example 4**: וּמַשְׂבִּיעַ לְכׇל־חַי רָצוֹן

**Transcription**: `u-mas-bi-a le-khol-khai ra-tson`

**Key phonetic features**:
- **שׂ** sin (left dot) = **s** (NOT **sh**)
- **בּ** doubled in מַשְׂבִּיעַ = **bb** → `bi`
- **ח** chet = **kh** (guttural)
- **צ** tsade = **ts**
- Maqqef joins לְכׇל־חַי

**Wrong transcriptions to avoid**:
- ❌ `u-mash-bi-a` (שׂ is **s**, not **sh**)
- ❌ `le-khol hai` (חַי = `khai`, ח is **kh**)
- ❌ `ra-tzon` is wrong if written `ra-son` (צ = **ts**)

---

### Common Pitfalls to Avoid

1. **Dagesh distinctions**:
   - פּ (with dot) = hard **p**
   - פ (no dot) = soft **f**
   - Don't confuse these!

2. **Final forms**:
   - ך (final khaf) = **kh** (NOT "sh")
   - ף (final fe) = **f**
   - ץ (final tsade) = **ts**

3. **Shin vs. Sin**:
   - שׁ (right dot) = **sh**
   - שׂ (left dot) = **s**
   - Check the dot position carefully!

4. **Chet vs. He**:
   - ח (chet) = guttural **kh**
   - ה (he) = soft **h**
   - Very different sounds!

5. **Qof vs. Kaf**:
   - ק (qof) = **k** (always hard)
   - כּ (kaf with dagesh) = **k**
   - כ / ך (khaf without dagesh) = **kh**

### Edge Cases

**Divine Names**:
- יְהוָה → `a-do-nai` (standard)
- אֲדֹנָי → `a-do-nai`
- אֱלֹהִים → `e-lo-him`

**Maqqef (word joiners)**:
- אֶת־יָדֶךָ → `et-ya-de-kha` (single unit)
- כׇּל־חַי → `kol-khai` (single unit)
- Do NOT separate with spaces

**Silent Shewa**:
- At beginning: usually vocal → `be-`, `le-`, `ve-`
- After first consonant: usually silent
- When in doubt: include it (`e`)

**Qamets vs. Qamets Khatuf**:
- Both look like ָ◌
- Qamets = **a** (long)
- Qamets Khatuf = **o** (short, in closed unaccented syllables)
- Example: כָּל = `kol` (khatuf), כָּבוֹד = `ka-vod` (qamets)
- When uncertain: use **a** and let context clarify

---

### Include in JSON Output

For each verse in your `verse_discoveries` array, add a `"phonetic"` field containing the complete phonetic transcription of that verse's Hebrew text.

**JSON structure**:
```json
{
  "verse_number": 16,
  "observations": "...",
  "curious_words": [...],
  "poetic_features": [...],
  "figurative_elements": [...],
  "puzzles": [...],
  "lxx_insights": "...",
  "macro_relation": "...",
  "phonetic": "po-te-akh et-ya-de-kha u-mas-bi-a le-khol-khai ra-tson"
}
```

### Quality Checklist

Before submitting your transcription, verify:

- [ ] All dagesh marked correctly (b/v, k/kh, p/f)
- [ ] Final forms transcribed (ך=kh, ף=f, ץ=ts, ם=m, ן=n)
- [ ] Shin (שׁ=sh) vs. Sin (שׂ=s) distinguished
- [ ] Chet (ח=kh) vs. He (ה=h) distinguished
- [ ] Divine name handled (יְהוָה = `a-do-nai`)
- [ ] Maqqef-joined words hyphenated as single unit
- [ ] Syllable breaks marked with hyphens
- [ ] Doubled consonants (dagesh forte) shown as double letters

---
```

---

## Updated JSON Output Format

The existing JSON output format should be updated to include the `"phonetic"` field:

```python
OUTPUT FORMAT: Return ONLY valid JSON:

{
  "verse_discoveries": [
    {
      "verse_number": 1,
      "observations": "Quick summary of what's interesting/curious in this verse (2-4 sentences). Focus on discoveries, not analysis.",
      "curious_words": ["תְּהִלָּה", "הַמֶּלֶךְ"],  // Hebrew words worth investigating
      "poetic_features": ["unique psalm title", "personal + royal address"],
      "figurative_elements": ["God as personal king - intimate monarchy"],
      "puzzles": ["Why unique title 'תְּהִלָּה' rather than מִזְמוֹר?"],
      "lxx_insights": "LXX uses Αἴνεσις (aínesis, praise) for תְּהִלָּה",
      "macro_relation": "Establishes divine kingship theme from thesis but with personal intimacy",
      "phonetic": "te-hil-la le-da-vid a-ro-mim-kha e-lo-hai ham-me-lekh va-a-va-re-kha shim-kha le-o-lam va-ed"  // NEW FIELD
    },
    {
      "verse_number": 2,
      "observations": "...",
      "curious_words": [...],
      "poetic_features": [...],
      "figurative_elements": [...],
      "puzzles": [...],
      "lxx_insights": "...",
      "macro_relation": "...",
      "phonetic": "be-khol-yom a-va-re-khe-ka va-a-ha-le-la shim-kha le-o-lam va-ed"
    },
    ... (continue for all {verse_count} verses)
  ],
  "overall_patterns": [
    "Acrostic structure with missing nun verse - possibly intentional given 'falling ones' in v.14",
    "Progressive expansion: personal (vv.1-2) → generational (vv.4-7) → universal (vv.8-21)",
    "Repeated 'all/every' (kol) appearing 17 times - creates universality drumbeat"
  ],
  "interesting_questions": [
    "Why does the psalm use the unique title 'תְּהִלָּה' rather than standard מִזְמוֹר?",
    "What is the significance of the missing nun verse in the acrostic?",
    "How does universal divine compassion (v.9) reconcile with destruction of the wicked (v.20)?"
  ],
  "research_priorities": [
    "LEXICON: Focus on unique praise vocabulary (תְּהִלָּה), rare words (עֱזוּז, חֵקֶר), royal terminology cluster",
    "CONCORDANCE: Track 'all/every' (כֹּל) usage pattern, 'forever and ever' formula",
    "FIGURATIVE: Hand imagery (v.16), pouring forth metaphor (v.7)",
    "COMMENTARY: LXX addition in v.13, ketiv/qere in v.6, missing nun verse traditions"
  ]
}

Return ONLY the JSON object, no additional text.
```

---

## Testing the Prompt

### Test Input: Psalm 145:16

**Hebrew**: פּוֹתֵחַ אֶת־יָדֶךָ וּמַשְׂבִּיעַ לְכׇל־חַי רָצוֹן

### Expected Output (partial)

```json
{
  "verse_number": 16,
  "observations": "The image of God 'opening his hand' is intimate and generous. מַשְׂבִּיעַ (satisfying) and רָצוֹן (desire/will) suggest abundant provision beyond mere survival. Every living being receives satisfaction of desires, not just needs.",
  "curious_words": ["פּוֹתֵחַ", "מַשְׂבִּיעַ", "לְכׇל־חַי", "רָצוֹן"],
  "poetic_features": ["intimate hand imagery", "universal scope with כׇל"],
  "figurative_elements": ["divine hand as source of abundance", "satisfied desire as divine gift"],
  "puzzles": [],
  "lxx_insights": "LXX ἀνοίγεις τὴν χεῖρά σου (anoígeis tēn cheîrá sou, you open your hand)",
  "macro_relation": "Generous divine provision contrasts with human royal neglect - central to caring kingship thesis",
  "phonetic": "po-te-akh et-ya-de-kha u-mas-bi-a le-khol-khai ra-tson"
}
```

### Verification

✅ **פּ** with dagesh → `p` (not `f`)
✅ **ח** chet → `kh` (not `h`)
✅ **ך** final khaf → `kh` (not `sh`)
✅ **שׂ** sin → `s` (not `sh`)
✅ Maqqef properly handled: `et-ya-de-kha`, `le-khol-khai`
✅ Syllable breaks clear: `po-te-akh`, `u-mas-bi-a`, `ra-tson`

---

## Success Criteria

The phonetic transcription is successful if:

1. ✅ All dagesh distinctions are accurate (p/f, b/v, k/kh)
2. ✅ Final forms are correct (ך=kh, ף=f, ץ=ts)
3. ✅ Shin/sin are distinguished (שׁ=sh, שׂ=s)
4. ✅ Chet/he are distinguished (ח=kh, ה=h)
5. ✅ Divine names are handled appropriately
6. ✅ Maqqef-joined words are hyphenated as units
7. ✅ Syllable breaks are clearly marked
8. ✅ Doubled consonants are shown (dagesh forte)
9. ✅ Downstream agents can make accurate phonetic claims
10. ✅ Master Editor catches phonetic errors when they occur

---

## Implementation Notes

- **Complexity**: Moderate — requires careful attention to Hebrew phonology
- **Error prevention**: High value — prevents factual errors in commentary
- **User benefit**: Provides educational phonetic data for readers
- **Scalability**: Works for all 150 Psalms once implemented
- **Dependencies**: None — pure addition to existing pipeline
