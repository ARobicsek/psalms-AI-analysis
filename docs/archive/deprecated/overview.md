# The Psalms Commentary Pipeline: A Methodological Overview

**Date**: 2025-10-20
**Version**: 1.0

## 1. Vision & Guiding Principles

This document details the architecture and methodology of the Psalms AI Commentary Pipeline, a system designed to generate scholarly, verse-by-verse commentary for the Book of Psalms. The goal is to produce a final work product, such as `psalm_001_print_ready.md`, that is not merely a summary of existing information but a work of synthetic scholarship.

The project is guided by three core principles:

1.  **Scholarly Rigor**: The output must be grounded in textual evidence, engage with historical and literary context, and reflect the nuances of biblical scholarship. It avoids "LLM-ish breathlessness" (e.g., "breathtaking," "masterpiece") in favor of precise, analytical prose.
2.  **Telescopic Analysis**: The pipeline mimics a human scholarly process by moving from a high-level "forest" view to a detailed "trees" view, and then synthesizing them. This prevents generic, disconnected verse-by-verse paraphrasing.
3.  **Architectural Elegance & Efficiency**: The system is designed to be cost-effective and maintainable. It strategically uses powerful AI models for analysis and deterministic Python scripts for data retrieval, ensuring that financial cost is directly tied to the generation of novel insights.

---

## 2. System Architecture: The Five-Pass Pipeline

The pipeline processes each psalm through a series of specialized agents in a multi-pass architecture. The final analytical step is a `MasterEditor` agent that performs a comprehensive scholarly review and revision, ensuring the final output meets the highest standards of quality and accuracy.

The diagram below illustrates the flow of data and analysis for a single psalm.

```mermaid
graph TD
    subgraph " "
        A[Psalm Text & RAG Context] --> B{Pass 1: MacroAnalyst (Claude 3.5 Sonnet)};
        B -- MacroAnalysis --> C{Pass 2: MicroAnalyst v2 (Claude 3.5 Sonnet)};
        C -- Research Requests --> D[Research Assembler (Python)];
        subgraph "Librarian Agents (Python)"
            D --> D1[BDB & Klein Lexicons];
            D --> D2[Tanakh Concordance];
            D --> D3[Figurative Language DB];
            D --> D4[Classical Commentaries];
        end
        D -- Research Bundle --> E{Pass 3: SynthesisWriter (Claude 3.5 Sonnet)};
        C -- Verse Discoveries & Phonetics --> E;
        B -- MacroAnalysis --> E;
        E -- Draft Commentary --> F{Pass 4: MasterEditor (GPT-5)};
        F -- Final Commentary --> G[Final Formatters (Python)];
        G -- Formatted .md & .docx --> H([Final Outputs]);
    end
```

---

## 3. A Step-by-Step Walkthrough: How a Commentary is Born

Let's trace the journey of a single psalm (e.g., Psalm 29) from raw text to finished commentary.

### Step 0: Data Ingestion & Contextualization

Before any analysis begins, the system gathers all necessary background information.

*   **Source Texts**: The `TanakhDatabase` provides the Masoretic (Hebrew) Text and an English translation. The `SefariaClient` also fetches the Greek Septuagint (LXX) text from the Bolls.life API, which is crucial for textual criticism and understanding early interpretations.
*   **RAG (Retrieval-Augmented Generation) Context**: The `RAGManager` loads three key documents to ground the AI's analysis:
    1.  **Analytical Framework**: A detailed guide on biblical poetics, covering parallelism, imagery, and literary structures. This serves as the AI's "methodology textbook."
    2.  **Psalm Function Database**: A JSON file classifying the psalm's genre (e.g., "Hymn of Praise"), structure, and keywords.
    3.  **Ugaritic Comparisons**: A database of known literary and linguistic parallels between the Psalms and ancient Ugaritic texts, providing crucial Ancient Near Eastern (ANE) context.

### Pass 1: The Forest - MacroAnalyst

*   **Agent**: `MacroAnalyst` (`claude-sonnet-4.5`)
*   **Input**: The complete psalm text (Hebrew, English, LXX) and all RAG context.
*   **Task**: To form a high-level, chapter-wide thesis *before* getting lost in verse-level details.
*   **Prompting Strategy**:
    *   **Persona**: A distinguished biblical scholar like Robert Alter.
    *   **Instructions**: The agent is explicitly told to identify the psalm's emotional arc, structural divisions, poetic architecture, and genre. It must formulate a **specific, non-generic central thesis** in a single sentence.
    *   **Output Format**: It must return a structured JSON object (`MacroAnalysis`) containing its findings, including 5-10 "Questions for Micro-Analysis" to guide the next pass.
*   **Result**: A `MacroAnalysis` object. For Psalm 29, this included the thesis that the psalm is a "liturgical polemic that systematically transfers Baal's storm-god attributes to YHWH."

### Pass 2: The Trees - MicroAnalyst v2 (Discovery & Research)

*   **Agent**: `MicroAnalystV2` (`claude-sonnet-4.5`)
*   **Input**: The `MacroAnalysis` from Pass 1, plus all source texts and RAG context.
*   **Task**: This agent was redesigned to be **curiosity-driven**. Instead of proving the macro-thesis, its job is to read each verse with "fresh eyes" and identify what is interesting, puzzling, or poetically significant. This critical design choice prevents confirmation bias.
*   **Process**:
    1.  **Discovery Pass**: It first examines each verse to note linguistic puzzles, surprising imagery, and poetic devices.
    2.  **Research Request Generation**: Based *only* on its discoveries, it generates a detailed JSON object of research requests for the Librarian agents. For Psalm 29, this resulted in 31 lexicon requests, 7 concordance searches, 11 figurative language checks, and 4 commentary requests.
*   **Prompting Strategy**:
    *   **Persona**: A curious, detail-oriented scholar.
    *   **Instructions**: The prompt emphasizes noticing "puzzles, surprises, and clever poetic choices" and explicitly instructs the agent to keep the macro-thesis in its "peripheral vision only." It must justify each research request.
*   **Result**: Two key outputs:
    1.  `MicroAnalysis`: A lightweight object containing the verse-by-verse "discoveries."
    2.  `Research Request`: A structured JSON file to be consumed by the Research Assembler.

### The Research Phase: The Librarian Agents (Deterministic Python)

The `ResearchAssembler` coordinates four "librarian" agents. These are pure Python scripts that make no LLM calls. This is a core architectural decision to ensure data retrieval is fast, cheap, and 100% accurate.

1.  **`BDBLibrarian`**: Fetches definitions from scholarly Hebrew lexicons (the full BDB and Klein) via the Sefaria API. It provides full semantic ranges, etymology (including cognates from other ancient languages), and homograph disambiguation data.
2.  **`ConcordanceLibrarian`**: Searches the project's custom-built, 269,000-word Tanakh concordance. Its key feature is a **morphological variation generator** that expands a search for a root word (e.g., `שמר`, "guard") into ~66 grammatical forms (nouns, verbs, plurals, etc.), ensuring 99%+ recall. It defaults to a "consonantal" search, which ignores vowels, as this is best for thematic analysis.
3.  **`FigurativeLibrarian`**: Queries a pre-existing database of over 2,800 figurative language instances in the Psalms and Pentateuch. It uses word-boundary matching to avoid false positives (e.g., searching "arm" won't match "army").
4.  **`CommentaryLibrarian`**: Fetches excerpts from up to six classical Jewish commentators (Rashi, Ibn Ezra, etc.) for verses flagged as interpretively complex by the `MicroAnalyst`.

The `ResearchAssembler` compiles all this data into a single, comprehensive `ResearchBundle` formatted in Markdown for optimal LLM consumption.

### Pass 3: The Synthesis - SynthesisWriter

*   **Agent**: `SynthesisWriter` (`claude-sonnet-4.5`)
*   **Input**: A complete dossier: `MacroAnalysis`, `MicroAnalysis` (discoveries), and the `ResearchBundle`.
*   **Task**: To write the final, publication-ready commentary. This is the culmination of all prior steps.
*   **Process**:
    1.  **Introduction Essay (800-1200 words)**: The agent first writes a comprehensive introduction. It is explicitly empowered to **critically engage with, revise, or even reject** the initial `MacroAnalysis` thesis based on the full weight of the research.
    2.  **Verse-by-Verse Commentary (150-400+ words/verse)**: For each verse, it synthesizes its own discoveries with the rich data from the `ResearchBundle`.
*   **Prompting Strategy**:
    *   **Persona**: A "distinguished professor of biblical literature" writing for a sophisticated lay audience (e.g., *The New Yorker*).
    *   **Instructions**: The prompt is extremely detailed, providing 11 distinct scholarly angles to explore (Poetics, ANE Parallels, Textual Criticism, Lexical Analysis, etc.). It demands a varied approach, evidence-based claims, and a tone of "measured confidence." It must cite the research data, referencing BDB, LXX variants, and classical commentators.
*   **Result**: A `SynthesisOutput` object containing the complete, polished introduction and verse-by-verse commentary. The quality proved high enough to make the planned `Critic` and `FinalPolisher` passes redundant.

### Pass 4: The Polish - MasterEditor

*   **Agent**: `MasterEditor` (`gpt-5`)
*   **Input**: The complete `SynthesisOutput` from Pass 3, plus the *entire* research dossier (`MacroAnalysis`, `MicroAnalysis`, `ResearchBundle`, phonetic transcriptions, etc.).
*   **Task**: To perform a final, rigorous editorial review and revision, elevating the commentary from "excellent" to "publication-ready."
*   **Process**:
    1.  **Critical Assessment**: The agent first provides a brief editorial assessment, identifying strengths, weaknesses, and missed opportunities.
    2.  **Factual & Phonetic Verification**: A key role is to verify all claims against the research data. For example, it is explicitly instructed to check phonetic claims (e.g., "alliteration of 'f' sounds") against the authoritative phonetic transcriptions from the `MicroAnalyst` to prevent factual errors.
    3.  **Revision & Enhancement**: The agent rewrites the introduction and verse-by-verse commentary to correct errors, deepen the analysis, and refine the prose to the highest scholarly standard.
*   **Prompting Strategy**:
    *   **Persona**: A "MASTER EDITOR and biblical scholar of the highest caliber," akin to Robert Alter or James Kugel.
    *   **Instructions**: The prompt grants full editorial discretion and provides a detailed checklist of 7 review criteria, including Factual Errors, Missed Opportunities, Stylistic Problems, and Argument Coherence. It demands engagement with unusual Hebrew phrases and deep analysis of figurative language.
*   **Result**: The final, master-edited commentary, ready for formatting.

### Step 5: Print-Ready Formatting

*   **Agent**: `CommentaryFormatter` (Python script)
*   **Input**: The final edited commentary from the `MasterEditor` and the psalm number.
*   **Task**: To assemble the final, clean, print-ready Markdown file.
*   **Process**:
    1.  Fetches the canonical Hebrew/English verse text from the database.
    2.  Integrates the introduction and verse-by-verse commentary.
    3.  Applies **divine name modifications** to all Hebrew text, following traditional Jewish practice (e.g., `יהוה` → `ה׳`, `אלהים` → `אלקים`). This is handled by the `DivineNamesModifier` utility.
    4.  Adds a "Methodological & Bibliographical Summary" section, pulling statistics from the `pipeline_stats.json` file to provide a transparent "fingerprint" of the generation process (e.g., models used, research counts, timings).
    5.  Formats the bilingual Hebrew/English verse lines with a Left-to-Right Mark (`\u200e`) and tab characters to ensure correct rendering in word processors.
*   **Result**: The final `psalm_XXX_print_ready.md` file, ready for review or publication.

---

## 4. Key Architectural Decisions & Rationale

The "why" behind the pipeline's design is as important as the "how".

| Decision | Rationale |
| :--- | :--- |
| **Deterministic Python Librarians** | **Cost, Speed, & Accuracy.** Using Python for data retrieval instead of LLMs saves money (~$0.15 per psalm) and time, and eliminates the risk of data hallucination. The "Librarian" role requires perfect accuracy, not intelligence. |
| **Curiosity-Driven Micro-Analysis** | **Prevents Confirmation Bias.** The initial design had the `MicroAnalyst` trying to prove the `MacroAnalyst`'s thesis. The redesign to focus on "discovery" allows the `SynthesisWriter` to challenge the initial thesis if the verse-level evidence points in a different direction, leading to more honest scholarship. |
| **Consonantal Concordance Default** | **Maximizes Relevant Recall.** Hebrew vowel points were added centuries after the text was written. Searching by consonantal root (e.g., `שמר`) finds all instances of a word's theme, regardless of grammatical form, which is more useful for literary analysis than an "exact" search. |
| **Scholar Agent Filters Homographs** | **Preserves Ambiguity & Saves Money.** The `BDBLibrarian` returns all possible meanings for a word (e.g., `רעה` can mean "shepherd" or "evil"). The `SynthesisWriter`, which already has the verse context, is best equipped to select the correct meaning. This is 57% cheaper than adding an extra LLM call in the librarian and allows the writer to spot intentional wordplay. |
| **Markdown for Research Bundles** | **Optimized for LLM Consumption.** LLMs are highly effective at parsing the hierarchical structure (e.g., `##`, `###`) and semantic formatting (`**bold**`, `*italics*`) of Markdown, making it a more efficient and readable format for prompts than raw JSON. |
| **Comprehensive Logging** | **Full Observability.** A dedicated logging utility (`src/utils/logger.py`) with dual-format output (human-readable text, machine-readable JSON) tracks every agent's inputs, queries, and results. This is invaluable for debugging, performance tuning, and ensuring transparency. |

This architecture creates a virtuous cycle: deterministic data retrieval grounds the creative and analytical power of large language models, resulting in a final product that is both scholarly and insightful.

---

## 5. Prompting Philosophy: Crafting a Scholarly Voice

The quality of the final commentary is a direct result of a sophisticated prompting strategy designed to elicit a specific scholarly persona and analytical style.

### The Persona: A Distinguished Biblical Scholar

All analytical agents (`MacroAnalyst`, `SynthesisWriter`) are given a detailed persona:

> "You are a distinguished biblical scholar... akin to figures like Robert Alter, Ellen F. Davis, or James Kugel. Your task is to write for a sophisticated lay audience, such as the readers of *The New Yorker* or *The Atlantic*. Your prose should be scholarly, lucid, and engaging. Your tone is one of measured confidence, not breathless praise."

### Key Prompting Directives

1.  **Show, Don't Tell**: The prompts explicitly forbid effusive, un-analytical praise.
    *   **Instead of**: "The psalm's central innovation lies in its theological revolution..."
    *   **Try**: "The psalm's engine is the sevenfold repetition of imagery X. By taking the familiar motif and transforming it, the poet re-maps the relationship between God and creation."

2.  **Focus on Action and Imagery**: Prompts instruct the AI to describe what the *poet does*. "How do they construct the poem? What world do they build?" This encourages a focus on literary craft.

3.  **Demand for Specificity**: Generic statements are forbidden. The `MacroAnalyst` must produce a single, sharp thesis sentence. The `SynthesisWriter` must ground every claim in textual evidence from the psalm or the research bundle.

4.  **Multi-Angle Analysis**: The `SynthesisWriter` prompt contains a checklist of 11 scholarly angles (Poetics, Textual Criticism, ANE Parallels, etc.) and instructs the agent to vary its approach, ensuring the commentary is multi-dimensional and not repetitive.

5.  **Structured Output**: Agents are required to return their analysis in a structured JSON format, which allows for reliable parsing and data flow between pipeline stages. The prompts include clear examples of the required JSON schema.

6.  **Extended Thinking**: Key analytical agents use an "extended thinking" mode, giving them a larger token budget and more time to reason before producing an answer. The logs show this results in significantly more nuanced and insightful analysis.

By combining a clear persona, strict stylistic guidelines, and a demand for evidence-based analysis, the prompts guide the AI to produce a commentary that is not just a summary of data, but a genuine work of scholarly synthesis.

---

## 6. Data Sources & Scholarly Foundation

The pipeline's credibility rests on the quality of its data sources. It does not rely solely on the LLM's internal knowledge.

| Data Source | Role in Pipeline | Provided By |
| :--- | :--- | :--- |
| **Masoretic Text (Hebrew)** | Primary text for analysis. | `TanakhDatabase` (from Sefaria API) |
| **Septuagint (LXX Greek)** | Crucial for textual criticism and early interpretive history. | Bolls.life API |
| **BDB & Klein Lexicons** | Scholarly definitions, etymology, and semantic ranges. | Sefaria API |
| **Full Tanakh Concordance** | Tracks word/phrase usage across the entire Hebrew Bible. | Custom-built SQLite DB |
| **Figurative Language DB** | 2,800+ pre-analyzed instances of metaphor, simile, etc. | `Pentateuch_Psalms_fig_language.db` |
| **Classical Commentaries** | Provides dialogue with traditional Jewish scholarship. | Sefaria API (Rashi, Ibn Ezra, etc.) |
| **Analytical Framework** | The AI's "textbook" on poetic analysis. | RAG Document |
| **Ugaritic Parallels** | Provides ANE literary and religious context. | RAG Document |
| **Psalm Function DB** | Provides genre and structural information for each psalm. | RAG Document |

This multi-source approach ensures that the AI's analysis is not performed in a vacuum. It is constantly grounded in, and in dialogue with, a rich collection of textual, linguistic, and historical data, mirroring the process of a human scholar.

---

## 7. Conclusion

The Psalms AI Commentary Pipeline is more than a content generation tool; it is an automated scholarly workflow. By breaking down the complex task of writing commentary into discrete, manageable steps—each with its own specialized agent and clear purpose—the system produces a final product of remarkable depth and consistency.

From the initial high-level thesis of the `MacroAnalyst` to the curiosity-driven research of the `MicroAnalyst` and the final, masterful synthesis of the `SynthesisWriter`, the pipeline demonstrates how a structured, multi-agent approach, grounded in high-quality data, can elevate AI-generated text from mere paraphrase to genuine scholarly analysis. The final `print_ready.md` file is the result of this carefully orchestrated collaboration between machine intelligence and a deep, well-curated library of human knowledge.

---

*This document was generated by Gemini Code Assist by analyzing the project's source code and documentation.*