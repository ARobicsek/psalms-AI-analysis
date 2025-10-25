# Phonetic Transcription Implementation Example

**Practical code examples showing how to integrate phonetic transcriptions into the pipeline**

---

## 1. Schema Update (analysis_schemas.py)

```python
@dataclass
class VerseCommentary:
    """Detailed commentary for a single verse from Pass 2."""
    verse_number: int
    commentary: str  # Full verse-by-verse analysis
    lexical_insights: List[str] = field(default_factory=list)
    figurative_analysis: List[str] = field(default_factory=list)
    thesis_connection: str = ""
    phonetic_transcription: str = ""  # NEW: IPA-like phonetic transcription
```

### Updated to_markdown() method

```python
def to_markdown(self) -> str:
    """Format as markdown for human reading and Pass 3 input."""
    lines = [
        f"# Micro Analysis: Psalm {self.psalm_number}",
        "",
        "## Verse-by-Verse Commentary"
    ]

    for vc in self.verse_commentaries:
        lines.append(f"\n### Verse {vc.verse_number}")

        # NEW: Add phonetic transcription before commentary
        if vc.phonetic_transcription:
            lines.append(f"\n**Phonetic**: `{vc.phonetic_transcription}`\n")

        lines.append(vc.commentary)

        if vc.lexical_insights:
            lines.append("\n**Lexical Insights:**")
            for insight in vc.lexical_insights:
                lines.append(f"- {insight}")

        if vc.figurative_analysis:
            lines.append("\n**Figurative Analysis:**")
            for analysis in vc.figurative_analysis:
                lines.append(f"- {analysis}")

        if vc.thesis_connection:
            lines.append(f"\n**Connection to Thesis:** {vc.thesis_connection}")

    # ... rest of method
```

---

## 2. Micro Analyst Prompt Update (micro_analyst.py)

### Add to DISCOVERY_PASS_PROMPT

Insert this section after "DISCOVERY TASK:" and before "OUTPUT FORMAT:":

```python
DISCOVERY_PASS_PROMPT = """You are conducting a QUICK DISCOVERY PASS of Psalm {psalm_number}.

[... existing content ...]

---

## PHONETIC TRANSCRIPTION TASK

For each verse, provide an ACCURATE PHONETIC TRANSCRIPTION of the Hebrew text.

**Why this matters**: Downstream editors need accurate phonetic data to avoid errors like claiming "soft f" when the text has hard "p" (פּ with dagesh), or "sh" when it's "kh" (ך final khaf).

### Transcription System

**Consonants**:
- ב: dagesh = **b**, no dagesh = **v**
- כ: dagesh = **k**, no dagesh = **kh**, final ך = **kh**
- פ: dagesh = **p**, no dagesh = **f**, final ף = **f**
- ח = **kh** (guttural chet)
- שׁ = **sh** (shin), שׂ = **s** (sin)
- צ = **ts** (tsade)
- ק = **k** (qof)
- Other consonants: straightforward (m, n, l, r, z, s, h, y, v)

**Vowels**:
- Patakh (ַ◌), Qamets (ָ◌) = **a**
- Tsere (ֵ◌), Segol (ֶ◌) = **e**
- Khiriq (ִ◌) = **i**
- Kholam (ֹ◌) = **o**, Kholam Male (וֹ) = **ō**
- Qibbuts (ֻ◌) = **u**, Shureq (וּ) = **ū**
- Vocal shewa (ְ◌) = **e**
- Khatef vowels (ֲ◌ = a, ֱ◌ = e, ֳ◌ = o)

**Note on `ו` (Vav):** The system now correctly distinguishes between `ו` as a consonant (`w`) and as a vowel marker (*mater lectionis*). `וֹ` is transcribed as `ō` and `וּ` is transcribed as `ū`.

**Formatting**:
- Syllable breaks: hyphens (`po-te-akh`)
- Maqqef joins words: single hyphen (`et-ya-de-kha`)
- Divine name YHVH: `a-do-nai`
- Doubled consonants (dagesh forte): double letter (`khan-nun`)

### Examples

**Hebrew**: פּוֹתֵחַ אֶת־יָדֶךָ
**Phonetic**: `po-te-akh et-ya-de-kha`
**Key**: פּ with dagesh = **p** (not f), ך final = **kh** (not sh)

**Hebrew**: חַנּוּן וְרַחוּם
**Phonetic**: `khan-nun ve-ra-khum`
**Key**: נּ doubled = **nn**, ח = **kh**

**Hebrew**: תְּהִלָּה לְדָוִד
**Phonetic**: `te-hil-la le-da-vid`
**Key**: לּ doubled = **ll**

Include the full verse transcription in your JSON output for each verse.

---

OUTPUT FORMAT: Return ONLY valid JSON:

{{
  "verse_discoveries": [
    {{
      "verse_number": 1,
      "observations": "Quick summary...",
      "curious_words": ["תְּהִלָּה", "הַמֶּלֶךְ"],
      "poetic_features": ["unique psalm title", "divine kingship"],
      "figurative_elements": ["personal king imagery"],
      "puzzles": ["Why unique title?"],
      "lxx_insights": "LXX translates...",
      "macro_relation": "Supports thesis...",
      "phonetic": "te-hil-la le-da-vid a-ro-mim-kha e-lo-hai ham-me-lekh va-a-va-re-kha shim-kha le-o-lam va-ed"
    }},
    {{
      "verse_number": 2,
      "observations": "...",
      "phonetic": "be-khol-yom a-va-re-khe-ka va-a-ha-le-la shim-kha le-o-lam va-ed",
      ...
    }},
    ... (all {verse_count} verses)
  ],
  "overall_patterns": [...],
  "interesting_questions": [...],
  "research_priorities": [...] 
}}

Return ONLY the JSON object, no additional text.
""".format(
        psalm_number=psalm_number,
        verse_count=self.verse_count # Assuming verse_count is available in this scope
    )
```

### Update _create_micro_analysis()

```python
def _create_micro_analysis(
    self,
    psalm_number: int,
    discoveries: dict
) -> MicroAnalysis:
    """Create MicroAnalysis object from discoveries."""
    # Convert discoveries to VerseCommentary objects
    verse_commentaries = []
    for disc in discoveries.get('verse_discoveries', []):
        vc = VerseCommentary(
            verse_number=disc['verse_number'],
            commentary=disc.get('observations', ''),
            lexical_insights=disc.get('curious_words', []),
            figurative_analysis=disc.get('figurative_elements', []),
            thesis_connection=disc.get('macro_relation', ''),
            phonetic_transcription=disc.get('phonetic', '')  # NEW
        )
        verse_commentaries.append(vc)

    # Create MicroAnalysis
    micro = MicroAnalysis(
        psalm_number=psalm_number,
        verse_commentaries=verse_commentaries,
        thematic_threads=discoveries.get('overall_patterns', []),
        interesting_questions=discoveries.get('interesting_questions', []),
        synthesis_notes="\n".join(discoveries.get('research_priorities', []))
    )

    return micro
```

---

## 3. Synthesis Writer Update (synthesis_writer.py)

### Add helper function

```python
def format_phonetic_section(micro_analysis: MicroAnalysis) -> str:
    """Format phonetic transcriptions for inclusion in prompts."""
    lines = ["## PHONETIC TRANSCRIPTIONS\n"]
    lines.append("*Reference these for accurate phonetic commentary. DO NOT make phonetic claims without consulting these transcriptions.*\n")

    for vc in micro_analysis.verse_commentaries:
        if vc.phonetic_transcription:
            lines.append(f"**Verse {vc.verse_number}**: `{vc.phonetic_transcription}`\n")

    return "\n".join(lines)
```

### Update VERSE_SYNTHESIS_PROMPT

```python
VERSE_SYNTHESIS_PROMPT = """You are writing scholarly verse-by-verse commentary on Psalm {psalm_number}.

[... existing macro analysis, micro discoveries, research bundle sections ...]

---

{phonetic_section}

**PHONETIC ACCURACY GUIDELINES**:

When making claims about sound patterns, rhythm, or phonetic symbolism:
1. **Always consult the phonetic transcriptions above**
2. **Common errors to avoid**:
   - Confusing פּ (hard **p**) with פ (soft **f**)
   - Confusing ך (final khaf = **kh**) with ש (shin = **sh**)
   - Missing dagesh distinctions (b/v, k/kh, p/f)
   - Claiming sounds that aren't actually present

**Example of CORRECT phonetic commentary**:
> "The opening word *potēaḥ* (פּוֹתֵחַ) features the hard plosive **p**, creating a sense of decisive action."

**Example of INCORRECT phonetic commentary** (to avoid):
> "The soft **f** sound creates gentleness." ← WRONG if the text has פּ with dagesh = hard **p**

---

[... rest of prompt ...]
""".format(
        psalm_number=psalm_number,
        macro_analysis=macro_analysis.to_markdown(),
        micro_discoveries=json.dumps(micro_analysis.to_dict(), ensure_ascii=False, indent=2),
        research_bundle=research_bundle.to_markdown(),
        psalm_text=self._format_psalm_text(psalm_number), # Assuming this method exists
        phonetic_section=phonetic_section  # NEW
    )

# Update the synthesize_verses() call:
def synthesize_verses(self, psalm_number: int, macro_analysis: MacroAnalysis,
                      micro_analysis: MicroAnalysis, research_bundle: ResearchBundle) -> str:
    """Synthesize verse-by-verse commentary."""

    # Format phonetic section
    phonetic_section = format_phonetic_section(micro_analysis)

    # Build prompt
    prompt = VERSE_SYNTHESIS_PROMPT.format(
        psalm_number=psalm_number,
        macro_analysis=macro_analysis.to_markdown(),
        micro_discoveries=json.dumps(micro_analysis.to_dict(), ensure_ascii=False, indent=2),
        research_bundle=research_bundle.to_markdown(),
        psalm_text=self._format_psalm_text(psalm_number), # Assuming this method exists
        phonetic_section=phonetic_section  # NEW
    )

    # ... rest of method
```

---

## 4. Master Editor Update (master_editor.py)

### Update MASTER_EDITOR_PROMPT

```python
MASTER_EDITOR_PROMPT = """You are a MASTER EDITOR and biblical scholar of the highest caliber.

[... existing sections ...]

---

{phonetic_section}

---

## YOUR EDITORIAL REVIEW CRITERIA

Review the introduction and verse commentary for these issues:

### 1. FACTUAL ERRORS

**Phonetic Errors** (HIGH PRIORITY):
- Claiming "soft f" when the text has hard "p" (פּ with dagesh)
- Claiming "sh" when the text has "kh" (ך final khaf or ח chet)
- Confusing sin (שׂ = s) with shin (שׁ = sh)
- Missing dagesh distinctions (b/v, k/kh, p/f)
- Making phonetic claims without consulting the phonetic transcriptions

**Phonetic Accuracy Protocol**:
Before approving ANY commentary that discusses sound patterns, verify against the phonetic transcriptions above.

**Example of error to catch**:
❌ WRONG: "The line's sound—the soft f and sh—matches the gentleness."
✅ CORRECT: "The hard plosive **p** in *potēaḥ* followed by the guttural **kh** in *yadekha*..."

**Other factual errors**:
- Biblical errors (e.g., "Jacob had brothers" when he had only one - Esau)
- Misattributions of texts or quotations
- Incorrect historical or cultural claims
- Mistaken grammatical analysis
- Wrong verse references

[... rest of criteria ...]

---

## YOUR TASK: EDITORIAL REVISION

**Stage 1: Critical Analysis**

First, provide a brief editorial assessment (200-400 words):
- What works well in the current draft?
- What are the main weaknesses?
- **Are there any phonetic errors?** Check all sound-pattern claims against transcriptions.
- What specific revisions are needed?
- What insights from research were missed?

[... rest of stages ...]
""".format(
        psalm_number=psalm_number,
        introduction_essay=introduction,
        verse_commentary=verse_commentary,
        research_bundle=research_bundle.to_markdown(),
        psalm_text=psalm_text,
        macro_analysis=macro_analysis.to_markdown(),
        micro_analysis=micro_analysis.to_markdown(),
        phonetic_section=phonetic_section  # NEW
    )

# Update the edit() call:
def edit(self, psalm_number: int, introduction: str, verse_commentary: str,
         research_bundle: ResearchBundle, macro_analysis: MacroAnalysis,
         micro_analysis: MicroAnalysis, psalm_text: str) -> Dict[str, str]:
    """Edit and enhance the commentary."""

    # Format phonetic section
    phonetic_section = format_phonetic_section(micro_analysis)

    # Build prompt
    prompt = MASTER_EDITOR_PROMPT.format(
        psalm_number=psalm_number,
        introduction_essay=introduction,
        verse_commentary=verse_commentary,
        research_bundle=research_bundle.to_markdown(),
        psalm_text=psalm_text,
        macro_analysis=macro_analysis.to_markdown(),
        micro_analysis=micro_analysis.to_markdown(),
        phonetic_section=phonetic_section  # NEW
    )

    # ... rest of method
```

---

## 5. Example JSON Output from Micro Analyst

### Psalm 145 (verses 1, 2, 16 shown)

```markdown  ": [
    {
      "verse_discoveries": [
    {
      "ns": "The title
      "observations": "The titleque' (praise song) is uniqueמ among psalms - most use מר. Theress to God as direct address to God asediately personal 'my God the King' is immediately personal      "curious["תְּהִלָּהַמֶּלֶךְtic_features"],
      "poetic_featuresnal": ["unique title", "personalgur + royal address"],
      "figuralative_elements": ["God as personalng"],
      "puzzles": ["Whytitle תְּהִלָּה   "lxxX uses_insights": "LXX usesaise) for תις (aínesis, praise) for תִלָּה",
      "macros divine kingship theme with personal intim kingship theme with personal intim"phonetic":h lə-dhā-wikhā eō-mim-khā e-lō-hay ham-a-me-lekh wa-aim-khə-khā shim-kh-lām wā-ʿe  },
    {
      dh"
    },
    {2,
      "verse_number": 2,he phrase
      "observations": "The phrase dailyֹם) creates dailytment. Parallel liturgical commitment. Parallele with v.1 butss' to 'b shifts from 'extol/bless' to 'bords":less/praise'.",
      "curious_words":es":־יוֹם"],
      "poetic_features":ric 'forever anithd ever'", "parallelism with
      "figuraily praise asative_elements": ["daily praise aszzles": [], religious discipline"],
      "puzzles": [],ἡμέρανκάστην ἡμέρανor ב (each day) for ב  "וֹם",
      "n": "Personalmacro_relation": "Personalniversal trajectory",
      "phonetic": " commitment expanding to universal trajectory",
      "phonetic": "ā lə wā-ʿedh
    {
      "
    },
    {: 16,
      "verse_number": 16,e image of God 
      "observations": "The image of Godous 'opening his hand' is intimate and generousרָצן (desireest abundant/will) suggest abundantsurvival.",
      "curious_words provision beyond mere survival.",
      "curious_words_features"],
      "poetic_features": ["intimate hand imageryents":"],
      "figurative_elements":asnce", "satisfie source of abundance", "satisfievinezzles": [], gift"],
      "puzzles": [],"lxx_insights":is, youις (anoígeis, youח open) for פּוֹתֵח",
      "macro_ous divine provision contrrelation": "Generous divine provision contretic":asts with human royal neglect",
      "phonetic": lə-khol-khy rā-tsōn"
  
    }
  ],tterns": [
    "Ac
  "overall_patterns": [
    "Acn verserostic structure with missing nun verse → gener",
    "Progressive expansion: personal → generversal",
    "Repeateimes"ol) appearing 17 times"estions
  ],
  "interesting_questionsWhy uniquee 'תְּהִלָstandard psalmּה' instead of standard psalmignation?",
    "Whatng nun verse in is significance of missing nun verse inowssion (v does universal compassion (vn.9) reconcile with destruction.20)ch?"
  ],
  "research "_priorities": [
    ": Focusise vocabulary ( on unique praise vocabulary (ds (עֱ חֵק
    "CONCORDֶר)",
    "CONCORDvery' (ANCE: Track 'all/every' (usage pattern "FIGURmagery, poATIVE: Hand imagery, po ]uring forth metaphor"
  ]
}
```

**Key Features in**
-  Transcriptions:**
-Syllable breaks.,  with hyphens (e.g.,ā- ✅tion doubled (לּ →  Gemination doubled (לּ →ha-lləowels marked (ā, ✅ Long vowels marked (ā,ctionis handled (וater lectionis handled (וּ → `ū`)gdistinctions (adkefat distinctions ( כ → `k
}
```

---

## 6. Expected Formatted Output in Synthesis Prompt

```markdown
## PHONETIC TRANSCRIPTIONS

*Reference these for accurate phonetic commentary. DO NOT make phonetic claims without consulting these transcriptions.*

**Verse 1**: `te-hil-la le-da-vid a-ro-mim-kha e-lo-hai ham-me-lekh va-a-va-re-kha shim-kha le-o-lam va-ed`

**Verse 2**: `be-khol-yom a-va-re-khe-ka va-a-ha-le-la shim-kha le-o-lam va-ed`

**Verse 3**: `ga-dol a-do-nai um-hu-lal me-od ve-lig-du-la-to ein khe-ker`

[... verses 4-15 ...]

**Verse 16**: `po-te-akh et-ya-de-kha u-mas-bi-a le-khol-khai ra-tson`

[... verses 17-21 ...]

**PHONETIC ACCURACY GUIDELINES**:

When making claims about sound patterns, rhythm, or phonetic symbolism:
1. **Always consult the phonetic transcriptions above**
2. **Common errors to avoid**:
   - Confusing פּ (hard **p**) with פ (soft **f**)
   - Confusing ך (final khaf = **kh**) with ש (shin = **sh**)
   - Missing dagesh distinctions (b/v, k/kh, p/f)

**Example of CORRECT phonetic commentary**:
> "The opening word *potēaḥ* (פּוֹתֵחַ) features the hard plosive **p**, creating decisive action."

**Example of INCORRECT phonetic commentary** (to avoid):
> "The soft **f** sound creates gentleness." ← WRONG if text has פּ = hard **p**
```

---

## 7. Sample Corrected Master Editor Output

### BEFORE (with phonetic error)

```markdown
**Verse 16**

The intimate image of divine provision reaches climactic expression with God "opening his hand" to satisfy every living thing's desire. The line's sound—the soft f and sh—matches the gentleness of the act it describes, creating phonetic harmony between form and content.
```

### AFTER (phonetically accurate)

```markdown
**Verse 16**

The intimate image of divine provision reaches climactic expression: "פּוֹתֵחַ אֶת־יָדֶךָ" (*potēaḥ et-yadekha*, "opening Your hand"). The verse opens with the hard plosive **p** in *potēaḥ*, suggesting decisive, purposeful action—this is not hesitant charity but confident generosity. The sound then softens into the guttural **kh** of *yadekha* ("Your hand"), creating phonetic movement from authority to intimacy. The verb מַשְׂבִּיעַ (*masbī'a*, "satisfying") introduces the sibilant **s** sound, while רָצוֹן (*ratsōn*, "desire") adds the emphatic **ts**—together these sounds evoke fullness and completion.
```

**Key improvements**:
- ✅ Correctly identifies hard **p** in פּוֹתֵחַ (not soft "f")
- ✅ Correctly identifies **kh** in יָדֶךָ (not "sh")
- ✅ Adds nuanced phonetic analysis based on accurate data
- ✅ Shows phonetic progression (p → kh → s → ts)
- ✅ Connects sound to meaning appropriately

---

## 8. Testing the Implementation

### Test Case 1: Psalm 145:16

**Hebrew**: פּוֹתֵחַ אֶת־יָדֶךָ וּמַשְׂבִּיעַ לְכׇל־חַי רָצוֹן

**Expected Phonetic**: `po-te-akh et-ya-de-kha u-mas-bi-a le-khol-khai ra-tson`

**Test**:
1. Run Micro Analyst on Psalm 145
2. Check JSON output contains accurate `"phonetic"` field for v16
3. Verify Synthesis Writer receives phonetic section
4. Verify Master Editor catches any phonetic errors

### Test Case 2: Psalm 145:8

**Hebrew**: חַנּוּן וְרַחוּם יְהוָה אֶרֶךְ אַפַּיִם וּגְדׇל־חָסֶד

**Expected Phonetic**: `khan-nun ve-ra-khum a-do-nai e-rekh a-pa-yim ug-dol-kha-sed`

**Key features**:
- נּ doubled (dagesh forte) = **nn**
- ח = **kh** (guttural)
- יְהוָה = `a-do-nai` (divine name)
- פּ doubled = **pp** in אַפַּיִם

### Test Case 3: Error Detection

**Intentionally introduce phonetic error** in verse commentary:
> "The soft **f** in *potēaḥ* creates a gentle sound."

**Expected Master Editor Response**:
> **Factual Error Detected**: The commentary incorrectly claims a "soft f" in *potēaḥ* (פּוֹתֵחַ). The phonetic transcription shows `po-te-akh`—the פּ has dagesh, making it a hard **p**, not soft **f**. This must be corrected.

---

## 9. Code Files to Update

### Summary of Files

1. **`src/schemas/analysis_schemas.py`**
   - Add `phonetic_transcription: str = ""` to `VerseCommentary`
   - Update `to_dict()`, `from_dict()`, `to_markdown()`

2. **`src/agents/micro_analyst.py`**
   - Update `DISCOVERY_PASS_PROMPT` with phonetic instructions
   - Update `_create_micro_analysis()` to extract phonetic data

3. **`src/agents/synthesis_writer.py`**
   - Add `format_phonetic_section()` helper
   - Update `VERSE_SYNTHESIS_PROMPT` to include phonetic section
   - Pass phonetic section to prompt

4. **`src/agents/master_editor.py`**
   - Add `format_phonetic_section()` helper (or import from synthesis_writer)
   - Update `MASTER_EDITOR_PROMPT` to include phonetic accuracy checks
   - Pass phonetic section to prompt

---

## 10. Implementation Priority

**HIGH PRIORITY** — This addresses:
1. Factual errors in published commentary
2. Scholarly credibility
3. Educational value for readers
4. Quality control mechanism

**Estimated Effort**: 2-3 hours
- Schema update: 15 minutes
- Micro Analyst prompt: 30 minutes
- Synthesis Writer update: 30 minutes
- Master Editor update: 30 minutes
- Testing: 45 minutes
- Documentation: 30 minutes

**Dependencies**: None (clean addition to existing pipeline)

**Risk**: Low (additive feature, doesn't break existing functionality)

---

## See Also

- **[PHONETIC_SYSTEM.md](PHONETIC_SYSTEM.md)** - Quick reference for phonetic transcription
- **[PHONETIC_TRANSCRIPTION_DESIGN.md](archive/deprecated/PHONETIC_TRANSCRIPTION_DESIGN.md)** - Complete design specification (archived)
- **[TECHNICAL_ARCHITECTURE_SUMMARY.md](TECHNICAL_ARCHITECTURE_SUMMARY.md)** - Overall system architecture