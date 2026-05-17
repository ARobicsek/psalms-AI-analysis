# The Architecture of the Reader's Guide: A Multi-Agent AI Pipeline

The final verse-by-verse commentary of the Psalms Reader's Guide synthesizes ancient Hebrew philology, medieval Jewish exegesis, structural analysis, and comparative literature into a cohesive, accessible document. Producing this requires managing an immense volume of multilingual data—a task ideally suited for a multi-agent Large Language Model (LLM) pipeline. 

Rather than relying on a single prompt or a solitary AI model, the guide is generated through an orchestrated sequence of specialized AI agents. Each agent is tasked with a narrow scholarly domain, contributing to a massive, centralized "Research Bundle" that routinely exceeds 200,000 characters in length. This bundle is ultimately synthesized into flowing prose by a master drafting model. 

Here is an overview of the specialized agents and processes that constitute the pipeline:

## 1. The Macro Analyst (Structural Analysis)
The pipeline begins by examining the Psalm as a complete architectural unit. The Macro Analyst evaluates the emotional trajectory, identifies the primary genre, and maps the poem's structural divisions. It generates a foundational thesis statement that grounds the subsequent verse-by-verse research.

## 2. The Micro Analyst (Verse Discovery & Philology)
Operating at the atomic level of the text, the Micro Analyst examines individual verses, rare vocabulary, and grammatical nuances. It consults Hebrew lexicons and synthesizes observations from major traditional commentators (such as Rashi, Radak, and Ibn Ezra), ensuring the commentary remains anchored in established exegetical traditions.

## 3. The Figurative Curator
Poetic imagery requires dedicated analysis. The Figurative Curator utilizes a specialized cross-referencing resource to track the use of specific similes, metaphors, and imagery across the entire Tanakh (Hebrew Bible). This allows the commentary to illuminate, for instance, how a "dove" or a "drawn sword" functions rhetorically not just within a single Psalm, but across the broader biblical corpus.

## 4. The Liturgical Librarian
To bridge the ancient text and its living tradition, the Liturgical Librarian tracks the reception history of the Psalm within Jewish prayer. It identifies which verses have been incorporated into daily liturgy, festival prayers, or penitential rites, mapping the trajectory of the text from biblical poetry to communal worship.

## 5. The Related Psalms Librarian
No Psalm exists in isolation. The Related Psalms Librarian analyzes a pre-computed database of textual connections to identify structural and lexical relationships between the target Psalm and others. By tracking shared rare roots, contiguous phrases, and "skipgrams" (words appearing in the same order with gaps), this agent enables the commentary to highlight intentional intertextuality and thematic pairings within the Psalter itself.

## 6. The Literary Echoes Agent
This agent places the Psalm in dialogue with world literature. By scanning across cultural and temporal boundaries, it identifies thematic and structural parallels—from ancient Near Eastern texts and Greek lyric poetry to modern literature. This comparative approach highlights the universal human experiences embedded in the Hebrew text.

## 7. Deep Web Research (Unautomated AI Integration)
While much of the pipeline is fully automated, it incorporates a crucial element of external AI research. Prior to drafting, a state-of-the-art LLM (such as Gemini) is manually prompted to conduct deep web research across academic databases, journals, and resources like Sefaria. This prompt is highly engineered to return findings in a dense, telegraphic style—maximizing information density without filler. This concentrated academic data is then injected directly into the pipeline's Research Bundle alongside the outputs of the automated agents.

## 8. The Master Writer
Once the Research Bundle is compiled—often swelling to over a quarter of a million characters of raw linguistic, historical, and theological data—it is handed to the Master Writer. Through rigorous prompt engineering, this model is instructed to synthesize the data into a flowing, accessible narrative. It must maintain a scholarly yet engaging tone, weaving together root-word analysis, historical context, and literary beauty without reading like a dry encyclopedia entry.

## 9. The Scripture Citation Verifier & Copy Editor
The final stages focus on rigorous quality control. A specialized script, backed by an LLM filter, scans the draft to verify that every biblical citation and cross-reference is accurate, correcting any hallucinations or misquoted text. Finally, the Copy Editor refines the prose, ensures smooth transitions, and formats the output into the final, print-ready document.

---

## Conclusion
The resulting commentary demonstrates the unique capability of orchestrated LLM pipelines in the domain of biblical scholarship. By dividing the labor among specialized agents, the pipeline can hold very large amounts of multilingual data in memory, systematically track imagery across millennia of literature, and synthesize it all into a rigorous and accessible guide.
