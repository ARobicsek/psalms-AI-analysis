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
3. Use a prompt like:

```
I'm preparing a scholarly essay on Psalm [NUMBER] for a collection of essays that serve as a reader's guide to the book of psalms. Please assemble a deep research package on this psalm that includes ancient, medieval and modern commentary and debates; ANE scholarship; linguistics, philology, etc. Also include reception, ritual and liturgical use of the psalm or any of its verses or phrases. Also include literary and cultural influence that the psalm or its language has had. Make sure to search widely, but include thetorah.org and Sefaria as well as academic sources. When you return your results please be clear and terse, to minimize tokens. You're not writing the essay; you're assembling the materials for the scholar.
```

4. Copy the output to a text file with the naming convention above
5. Save to this directory

## Integration

The pipeline's Research Assembler will automatically:
- Look for a deep research file for the current psalm
- Include it in the research bundle if found
- Remove it if the bundle exceeds character limits
- Track whether it was used in the pipeline stats

The final Word documents will indicate "Deep Web Research: Yes/No" in the Methodological Summary.
