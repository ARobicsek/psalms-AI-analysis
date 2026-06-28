# Deep Web Research Files

This directory stores Gemini Deep Research outputs for individual psalms.

## Naming Convention

Files should be named:
```
psalm_NNN_deep_research.txt
```

Where `NNN` is the zero-padded psalm number (e.g., `psalm_017_deep_research.txt`).

## How to Create

1. Go to [NotebookLM](https://notebooklm.google.com/) or [Gemini](https://gemini.google.com/)
2. Select "Deep Research" mode
3. Use the prompt from `docs/prompts_reference/deep_research_prompt.md` (substitute the psalm number)
4. Copy the output to a text file with the naming convention above
5. Save to this directory

## Integration

The pipeline's Research Assembler will automatically:
- Look for a deep research file for the current psalm
- Include it in the research bundle if found
- Remove it if the bundle exceeds character limits
- Track whether it was used in the pipeline stats

The final Word documents will indicate "Deep Web Research: Yes/No" in the Methodological Summary.
