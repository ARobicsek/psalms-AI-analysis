# Sefaria English Text Cleaning Guide

## Overview

This guide provides a comprehensive approach to cleaning English text fetched from Sefaria API. Sefaria text contains various types of footnotes, cross-references, translator notes, and formatting artifacts that need to be removed to produce clean, reader-friendly output.

## Types of Content to Clean

### 1. HTML-Style Footnotes (Most Common)

Sefaria embeds footnotes using HTML tags:

```html
<sup class="footnote-marker">a</sup><i class="footnote">Footnote text here</i>
<sup class="footnote-marker">1</sup><i class="footnote">Reference to azkara</i>
```

**Example in context:**
```
May He receive the tokens<sup class="footnote-marker">a</sup><i class="footnote">Reference to azkara</i> of all
```

### 2. Simple Text Markers

Some footnotes use hyphen and lowercase letter:

```
word.-a
phrase,-b
sentence-c
```

**Examples:**
```
I have fathered you this day.-b
pay homage in good faith,-d lest He be angered
```

### 3. Translator Notes and Commentary

Various types of explanatory notes:

```
Heb. 'afar. Cf. the second note at 2.7.
Lit. 'soil.'
Emendation yields: '...'
Others 'In the beginning God created.'
Cf. Ps. 19.6.
```

### 4. Editorial Notes

Notes about text arrangement:

```
Moved up from v. 24 for clarity
```

### 5. Malformed Text Artifacts

Database duplication issues:

```
*When God began to create*When God began to create Others...
```

### 6. HTML Tags and Entities

Various HTML remnants:

```
<br> (line breaks)
&lt; &gt; &amp; (HTML entities)
<i> <sup> (unclosed tags)
```

## Step-by-Step Cleaning Process

### Phase 1: HTML Tag Removal

1. **Remove footnote markers and content:**
   ```regex
   <sup class="footnote-marker">[^<]+</sup>
   <i class="footnote">[^<]*</i>
   ```

2. **Remove any remaining HTML tags:**
   ```regex
   </?sup[^>]*>
   </?i[^>]*>
   <br\s*/?>
   <[^>]+>
   ```

3. **Convert HTML entities to readable characters:**
   ```
   &lt; → <
   &gt; → >
   &amp; → &
   &quot; → "
   &#39; → '
   ```

### Phase 2: Text-Based Footnote Removal

1. **Remove simple footnote indicators:**
   ```regex
   ([.,;:])?\-[a-z](?=\s|$)
   ```
   - Matches `.-a`, `,-b`, `-c`, etc.
   - Preserves preceding punctuation

### Phase 3: Translator Note Removal

1. **Remove Hebrew language notes:**
   ```regex
   \s+Heb\s*\'[^\']*\'(?:\.|\s+)(?:Cf\.\s*[^\.,]+\.?)?
   \s+Heb\s+[^.,;:]+\.\s*(?:Cf\.\s*[^.,;:]+\.?)?
   ```

2. **Remove literal translation notes:**
   ```regex
   \s+Lit\.\s*\'[^\']*\'\.
   \s+Lit\.\s*\"[^\"]*\"\.
   ```

3. **Remove cross-references:**
   ```regex
   \s+Cf\.\s*[^,.]*\.?
   ```

4. **Remove emendation notes:**
   ```regex
   \s+Emendation[^,.]*\.?
   ```

5. **Remove "Others" translations:**
   ```regex
   \s+Others\s*«[^»]*»\s*
   \s+Others\s*"[^"]*"\s*
   \s+Others\s*'[^']*'\s*
   ```

6. **Remove parenthetical Hebrew notes:**
   ```regex
   \s*\([^)]*Heb[^)]*\)
   ```

### Phase 4: Artifact Cleanup

1. **Fix malformed duplicate patterns:**
   ```regex
   \*([^*]+)\* \1  →  \1
   ```

2. **Remove asterisked notes:**
   ```regex
   \s*\*[^*]+\*\s*
   ```

3. **Fix editorial move notes:**
   ```regex
   \s+[^,.]*\s+Moved up from v\.\s*\d+\s+for clarity
   ```

### Phase 5: Text Normalization

1. **Fix punctuation artifacts:**
   ```regex
   \.+ → .  (multiple periods to single)
   \s+([,.]) → \1  (remove space before punctuation)
   ```

2. **Fix word concatenation issues:**
   ```regex
   (\w)([A-Z][a-z]) → \1 \2  (e.g., "browShall" → "brow Shall")
   ```

3. **Normalize whitespace:**
   - Replace multiple spaces with single space
   - Trim leading/trailing spaces
   - Normalize newlines (remove excessive blank lines)

## Implementation Example

```python
import re
from html import unescape

def clean_sefaria_english(text: str) -> str:
    """Comprehensive cleaning of Sefaria English text."""

    if not text:
        return text

    # Phase 1: HTML removal
    text = re.sub(r'<sup class="footnote-marker">[^<]+</sup>', '', text)
    text = re.sub(r'<i class="footnote">[^<]*</i>', '', text)
    text = re.sub(r'</?sup[^>]*>', '', text)
    text = re.sub(r'</?i[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)

    # Convert HTML entities
    text = unescape(text)

    # Phase 2: Text-based footnote markers
    text = re.sub(r'([.,;:])?\-[a-z](?=\s|$)', r'\1', text)

    # Phase 3: Translator notes
    text = re.sub(r'\s+Heb\s*\'[^\']*\'(?:\.|\s+)(?:Cf\.\s*[^\.,]+\.?)?', '', text)
    text = re.sub(r'\s+Heb\s+[^.,;:]+\.\s*(?:Cf\.\s*[^.,;:]+\.?)?', '', text)
    text = re.sub(r'\s+Lit\.\s*\'[^\']*\'\.', '', text)
    text = re.sub(r'\s+Lit\.\s*\"[^\"]*\"\.', '', text)
    text = re.sub(r'\s+Cf\.\s*[^,.]*\.?', '', text)
    text = re.sub(r'\s+Emendation[^,.]*\.?', '', text)
    text = re.sub(r'\s+Others\s*«[^»]*»\s*', '', text)
    text = re.sub(r'\s+Others\s*"[^"]*"\s*', '', text)
    text = re.sub(r'\s*\([^)]*Heb[^)]*\)', '', text)

    # Phase 4: Artifact cleanup
    text = re.sub(r'\*([^*]+)\* \1', r'\1', text)
    text = re.sub(r'\s*\*[^*]+\*\s*', ' ', text)
    text = re.sub(r'\s+[^,.]*\s+Moved up from v\.\s*\d+\s+for clarity', '', text)

    # Phase 5: Normalization
    text = re.sub(r'\.+', '.', text)
    text = re.sub(r'\s+([,.])', r'\1', text)
    text = re.sub(r'(\w)([A-Z][a-z])', r'\1 \2', text)

    # Clean whitespace
    lines = text.split('\n')
    lines = [' '.join(line.split()) for line in lines if line.strip()]
    text = '\n'.join(lines)

    return text.strip()
```

## Testing Your Cleaner

Create test cases covering all patterns:

```python
test_cases = [
    # HTML footnotes
    ("May He receive the tokens<sup class=\"footnote-marker\">a</sup><i class=\"footnote\">Reference</i> of all",
     "May He receive the tokens of all"),

    # Simple markers
    ("I have fathered you this day.-b",
     "I have fathered you this day."),

    # Hebrew notes
    ("the dust Heb. 'afar'. from the ground",
     "the dust from the ground"),

    # Cross-references
    ("his work Cf. Ps. 19.6. is complete",
     "his work is complete"),

    # Malformed text
    ("*When God began to create*When God began to create Others",
     "When God began to create Others"),

    # Combined issues
    ("The earth*was formless*was formless Heb. 'tohu'. Cf. Gen 1.2.-a",
     "The earth was formless"),
]
```

## Best Practices

1. **Order matters:** Clean HTML tags before removing patterns that might be inside them
2. **Be conservative:** It's better to leave some artifacts than remove actual content
3. **Test thoroughly:** Create test cases for each pattern you expect to encounter
4. **Preserve formatting:** Keep paragraph breaks and intentional structure
5. **Handle edge cases:** Empty strings, None values, already-clean text
6. **Log transformations:** Keep track of what was removed for debugging

## Advanced Considerations

1. **Selective preservation:** Some footnotes might be valuable for scholarly work
2. **Context-aware cleaning:** Different books might have different footnote patterns
3. **Performance:** For large texts, compile regex patterns once
4. **Unicode handling:** Ensure proper handling of Hebrew characters and right-to-left text
5. **Version differences:** Sefaria might change formats over time

## Maintenance

- Monitor for new footnote patterns
- Update regex patterns as needed
- Keep test cases current
- Document any special cases or exceptions