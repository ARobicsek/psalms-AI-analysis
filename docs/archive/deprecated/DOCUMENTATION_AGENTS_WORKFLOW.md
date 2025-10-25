# Documentation Maintenance Agentic Workflow
**Date**: 2025-10-24
**Purpose**: Automated documentation cleanup and maintenance system

---

## Overview

This document defines the **agentic workflow** for documentation consolidation and ongoing maintenance. Instead of manually editing 133 files, we use specialized AI agents to work in parallel, reducing effort from ~10 hours to 4-6 hours.

---

## Agent Definitions

### 🤖 Agent 1: Documentation Auditor
**Specialty**: Finding redundancy, conflicts, and outdated information

**Capabilities**:
- Scan all .md files in project
- Identify duplicated content (>40% similarity)
- Flag conflicting information (e.g., different pipeline descriptions)
- Check last-modified dates vs. current phase
- Generate audit report

**Tools**: Glob, Grep, Read

**When to Use**:
- Monthly documentation review
- Before major consolidation
- After completing major feature (5+ sessions)

**Example Invocation**:
```
Task: "Audit all markdown documentation for redundancy and conflicts.
Report any documents describing different pipeline architectures,
conflicting phase numbers, or outdated status information.
Use 'very thorough' mode."
```

---

### 🤖 Agent 2: Content Consolidator
**Specialty**: Merging multiple documents into single source of truth

**Capabilities**:
- Read multiple related documents
- Extract unique content from each
- Identify overlapping sections
- Merge into consolidated document
- Preserve all information (zero loss)
- Generate before/after comparison

**Tools**: Read, Write, Edit

**When to Use**:
- Consolidating topic clusters (e.g., 8 phonetic docs → 1)
- Merging session summaries
- Creating unified reference guides

**Example Invocation**:
```
Task: "Consolidate these 8 phonetic documents into a single
PHONETIC_SYSTEM.md reference guide. Preserve all unique content,
remove duplicates, organize logically. Provide mapping showing
where each original section went."
```

---

### 🤖 Agent 3: Archive Organizer
**Specialty**: Moving historical/completed docs to organized archive

**Capabilities**:
- Identify session-specific documents
- Determine completion status (is feature implemented?)
- Create archive folder structure
- Move files with git-safe operations
- Generate INDEX.md for archived files
- Update cross-references

**Tools**: Bash (git mv), Read, Write

**When to Use**:
- After completing consolidation plan
- Quarterly cleanup
- When docs/ folder > 50 files

**Example Invocation**:
```
Task: "Move all SESSION_*_SUMMARY.md and SESSION_*_PLAN.md files
to docs/archive/sessions/. Create an INDEX.md in that folder
listing all files with dates and brief descriptions.
Use 'git mv' to preserve history."
```

---

### 🤖 Agent 4: Cross-Reference Updater
**Specialty**: Finding and updating broken or outdated links

**Capabilities**:
- Scan all .md files for markdown links
- Check if linked files exist
- Find references to moved/renamed files
- Update links to new locations
- Generate link validation report

**Tools**: Glob, Grep, Read, Edit

**When to Use**:
- After archiving documents
- After renaming files
- Monthly link validation

**Example Invocation**:
```
Task: "Find all references to ARCHITECTURE.md across all markdown files.
Update them to point to TECHNICAL_ARCHITECTURE_SUMMARY.md instead.
Report which files were updated."
```

---

### 🤖 Agent 5: Status Synchronizer
**Specialty**: Keeping status documents (README, PROJECT_STATUS) current

**Capabilities**:
- Read IMPLEMENTATION_LOG.md for latest session
- Extract current phase, progress %, recent accomplishments
- Update README.md development status section
- Update PROJECT_STATUS.md with latest metrics
- Ensure consistency across status docs

**Tools**: Read, Edit

**When to Use**:
- After each session (automated)
- Before publishing/sharing project
- Monthly accuracy check

**Example Invocation**:
```
Task: "Read IMPLEMENTATION_LOG.md Sessions 20-21. Update README.md
development status to reflect Phase 4, 85% complete, and latest
accomplishments. Ensure PROJECT_STATUS.md matches."
```

---

### 🤖 Agent 6: New Doc Creator
**Specialty**: Generating new documentation from templates/existing content

**Capabilities**:
- Scan codebase to understand structure
- Extract information from existing docs
- Follow templates for consistent format
- Generate comprehensive new documents
- Cross-reference related docs

**Tools**: Read, Write, Bash (for code scanning)

**When to Use**:
- Creating QUICK_START.md
- Creating DEVELOPER_GUIDE.md
- Creating GLOSSARY.md
- Generating new reference guides

**Example Invocation**:
```
Task: "Create a DEVELOPER_GUIDE.md by scanning the src/ directory
structure. Document where to find each agent, explain the difference
between librarian and AI agents, and provide a code organization overview.
Use existing docs for context."
```

---

### 🤖 Agent 7: Consistency Validator
**Specialty**: Ensuring no conflicting information remains

**Capabilities**:
- Extract key facts from all docs (pipeline architecture, costs, phases)
- Compare across documents
- Flag inconsistencies
- Generate consistency report
- Suggest which source should be canonical

**Tools**: Glob, Grep, Read

**When to Use**:
- After major consolidation
- Before project release
- Quarterly validation

**Example Invocation**:
```
Task: "Check all documentation for pipeline descriptions. Verify they
all describe the same 4-pass architecture. Flag any that mention
5 passes, Critic Agent, or Final Polisher. Report conflicts."
```

---

## Workflow Execution Plans

### 🔄 Workflow 1: Initial Consolidation (One-Time)
**Goal**: Clean up existing mess, establish single source of truth

**Duration**: 4-6 hours (using agents)

```
PHASE 1: CRITICAL FIXES (30 minutes, parallel)
├── Agent 5: Update README.md status
├── Agent 5: Update CONTEXT.md phase reference
├── Agent 6: Create QUICK_START.md
└── Agent 4: Add deprecation notices to ARCHITECTURE.md

PHASE 2: CONSOLIDATION (2 hours, sequential)
├── Agent 2: Consolidate 8 phonetic docs → PHONETIC_SYSTEM.md
├── Agent 2: Reduce NEXT_SESSION_PROMPT.md (1485 → 300 lines)
└── Agent 2: Merge overview.md content into CONTEXT.md

PHASE 3: ARCHIVING (1 hour, parallel)
├── Agent 3: Move session docs to archive/sessions/
├── Agent 3: Move bug fix docs to archive/bug_fixes/
└── Agent 3: Move deprecated docs to archive/deprecated/

PHASE 4: NEW DOCS (2 hours, parallel)
├── Agent 6: Create DEVELOPER_GUIDE.md
├── Agent 6: Create GLOSSARY.md
└── Agent 6: Create PIPELINE_DIAGRAM.md

PHASE 5: VALIDATION (30 minutes, sequential)
├── Agent 4: Update cross-references
├── Agent 7: Validate consistency
└── Agent 4: Check for broken links

Total: ~6 hours with agents (vs. 10+ hours manual)
```

---

### 🔄 Workflow 2: Post-Session Maintenance (Automated)
**Goal**: Keep docs current after each development session

**Duration**: 5-10 minutes

**Trigger**: After completing a development session

```
AUTOMATED WORKFLOW:
1. Agent 5: Read latest session from IMPLEMENTATION_LOG.md
2. Agent 5: Update README.md if phase/status changed
3. Agent 5: Update PROJECT_STATUS.md with metrics
4. Agent 7: Quick consistency check (pipeline description)
5. Generate: Maintenance report

IF session added major feature:
6. Agent 1: Audit for new redundancy
7. Suggest: Documentation updates needed
```

**Implementation**:
```bash
# After each session, run:
python scripts/update_documentation_status.py
```

---

### 🔄 Workflow 3: Monthly Documentation Review
**Goal**: Prevent documentation drift

**Duration**: 30 minutes

**Trigger**: First Monday of each month

```
MONTHLY REVIEW:
1. Agent 1: Full documentation audit
   - Check for redundancy
   - Flag outdated information
   - Identify orphaned files

2. Agent 7: Consistency validation
   - Pipeline descriptions match
   - Cost estimates current
   - Phase numbers consistent

3. Agent 4: Link validation
   - All markdown links work
   - No broken references

4. Agent 3: Archive check
   - Can any historical docs be deleted?
   - Is archive/ organized?

5. Generate: Monthly documentation health report
```

---

### 🔄 Workflow 4: Quarterly Deep Clean
**Goal**: Major consolidation if needed

**Duration**: 1-2 hours

**Trigger**: End of quarter or after 10+ sessions

```
QUARTERLY DEEP CLEAN:
1. Agent 1: Comprehensive audit
   - Full redundancy scan
   - Identify all conflicts
   - Check accuracy vs. codebase

2. Agent 2: Consolidate new redundancy
   - If new topic has 3+ docs, consolidate

3. Agent 3: Archive historical content
   - Move completed session docs
   - Clean up old bug fixes

4. Agent 6: Update major docs
   - Refresh TECHNICAL_ARCHITECTURE_SUMMARY.md if needed
   - Update GLOSSARY.md with new terms

5. Agent 7: Final validation
   - Ensure single source of truth maintained

6. Generate: Quarterly documentation report
```

---

## Agent Invocation Examples

### Example 1: Consolidating Phonetic Docs

**Using Task Tool with general-purpose agent**:

```
Invoke: Task (subagent_type: general-purpose)

Prompt:
"I need you to consolidate 8 phonetic documentation files into a single
PHONETIC_SYSTEM.md reference guide. This is a WRITING task.

FILES TO CONSOLIDATE:
- docs/PHONETIC_TRANSCRIPTION_DESIGN.md (design spec)
- docs/PHONETIC_REFERENCE_GUIDE.md (quick reference)
- docs/PHONETIC_SYLLABIFICATION.md (syllable rules)
- docs/PHONETIC_PROMPT_TEXT.md (prompt text)
- docs/PHONETIC_IMPLEMENTATION_EXAMPLE.md (code examples)
- docs/PHONETIC_PIPELINE_DIAGRAM.md (KEEP SEPARATE - visual)
- docs/PHONETIC_ENHANCEMENT_SUMMARY.md (KEEP SEPARATE - project overview)
- docs/MASTER_EDITOR_PHONETIC_FIX_SUMMARY.md (ARCHIVE - bug fix)

YOUR TASK:
1. Read all 8 files completely
2. Identify unique content in each
3. Create new PHONETIC_SYSTEM.md with structure:
   - Introduction
   - Consonant Reference (charts from REFERENCE_GUIDE)
   - Vowel Reference (charts from REFERENCE_GUIDE)
   - Syllabification Rules (from SYLLABIFICATION.md)
   - Edge Cases & Special Handling (from TRANSCRIPTION_DESIGN)
   - Common Mistakes (from REFERENCE_GUIDE)
   - Pro Tips (from REFERENCE_GUIDE)
   - Examples (select best from all docs)

4. Create mapping doc showing where each original section went

PRESERVE ALL INFORMATION - zero loss consolidation.

Return:
- New PHONETIC_SYSTEM.md file
- Mapping document
- List of files to archive"
```

---

### Example 2: Archiving Session Documents

**Using Task Tool with general-purpose agent**:

```
Invoke: Task (subagent_type: general-purpose)

Prompt:
"I need you to organize and archive all session-specific documentation.

YOUR TASK:
1. Create directory: docs/archive/sessions/
2. Find all files matching: SESSION_*_SUMMARY.md, SESSION_*_PLAN.md
3. For each file:
   - Use 'git mv' to preserve history
   - Move to docs/archive/sessions/
   - Extract date and topic from content

4. Create docs/archive/sessions/INDEX.md with:
   - Table of all archived sessions
   - Columns: Session # | Date | Topic | Filename
   - Sorted chronologically

5. Update IMPLEMENTATION_LOG.md to reference archive location

Return:
- List of files moved
- Generated INDEX.md
- Any broken references found"
```

---

### Example 3: Updating Cross-References

**Using Task Tool with Explore agent**:

```
Invoke: Task (subagent_type: Explore)

Prompt:
"I need you to find and catalog all references to ARCHITECTURE.md
across the project documentation.

YOUR TASK:
1. Search all .md files for references to ARCHITECTURE.md
   - Check markdown links: [text](ARCHITECTURE.md)
   - Check text mentions: 'see ARCHITECTURE.md'
   - Check relative paths: docs/ARCHITECTURE.md

2. For each reference found:
   - Note which file contains it
   - Note the context (which section)
   - Determine if reference should point to TECHNICAL_ARCHITECTURE_SUMMARY.md instead

3. Create report with:
   - Total references found
   - List of files needing updates
   - Recommended replacements

DO NOT modify files - this is a research task.

Return:
- Complete reference catalog
- Recommendation for which refs to update"
```

---

### Example 4: Creating DEVELOPER_GUIDE.md

**Using Task Tool with general-purpose agent**:

```
Invoke: Task (subagent_type: general-purpose)

Prompt:
"I need you to create a comprehensive DEVELOPER_GUIDE.md for this project.
This is a WRITING task.

YOUR TASK:
1. Scan src/ directory to understand code organization:
   - List all subdirectories
   - Identify key Python files
   - Note agent implementations

2. Read existing docs for context:
   - TECHNICAL_ARCHITECTURE_SUMMARY.md (architecture)
   - CONTEXT.md (project overview)
   - README.md (features)

3. Create DEVELOPER_GUIDE.md with sections:
   - Code Organization (src/ structure explained)
   - Agent Locations (where to find macro_analyst.py, micro_analyst.py, etc.)
   - Librarian vs AI Agents (explain distinction)
   - Data Flow (how components connect)
   - Adding a New Agent (step-by-step guide)
   - Testing Procedures (how to validate changes)
   - Common Tasks (examples: modify prompt, add data source, etc.)

4. Use clear, practical examples throughout

Target: 10-15 minute read for new developer.

Return:
- New DEVELOPER_GUIDE.md file"
```

---

### Example 5: Status Synchronization

**Using Task Tool with general-purpose agent**:

```
Invoke: Task (subagent_type: general-purpose)

Prompt:
"I need you to synchronize status information across all documentation
after Sessions 20-21. This is a WRITING task.

YOUR TASK:
1. Read IMPLEMENTATION_LOG.md Sessions 20-21
   - Extract: current phase, progress %, key accomplishments
   - Note: features implemented, files modified

2. Update README.md:
   - Development Status section
   - Change phase from 'Phase 1, Day 1' to current
   - Update progress percentage
   - Update last modified date

3. Update PROJECT_STATUS.md:
   - Add Sessions 20-21 to completed tasks
   - Update metrics (if provided in implementation log)
   - Update 'Last Updated' field

4. Update CONTEXT.md:
   - Fix any references to 'Phase 3' → 'Phase 4'

5. Verify consistency:
   - All three docs show same phase
   - All show same progress %

Return:
- Updated README.md
- Updated PROJECT_STATUS.md
- Updated CONTEXT.md
- Consistency verification report"
```

---

## Automation Scripts

### Script 1: Post-Session Documentation Update

**File**: `scripts/update_documentation_status.py`

```python
#!/usr/bin/env python3
"""
Automated documentation update after each session.
Reads IMPLEMENTATION_LOG.md and updates status docs.
"""

import anthropic
import os
from datetime import date

def update_post_session():
    """Update documentation status after session."""

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Agent task: Read latest session and update status docs
    prompt = f"""
    Today is {date.today()}.

    Read docs/IMPLEMENTATION_LOG.md and find the most recent session entry.

    Extract:
    - Session number
    - Date
    - Current phase
    - Progress percentage
    - Key accomplishments

    Then update:
    1. README.md Development Status section
    2. PROJECT_STATUS.md with latest metrics
    3. CONTEXT.md if phase changed

    Ensure all three documents show consistent information.

    Return a summary of changes made.
    """

    # Would invoke Task tool here
    # For now, this is a template

    print("Documentation status update complete.")

if __name__ == "__main__":
    update_post_session()
```

---

### Script 2: Monthly Documentation Audit

**File**: `scripts/audit_documentation.py`

```python
#!/usr/bin/env python3
"""
Monthly documentation health check.
Identifies redundancy, conflicts, and outdated info.
"""

import anthropic
import os

def monthly_audit():
    """Run comprehensive documentation audit."""

    # Agent task: Full documentation scan
    prompt = """
    Perform comprehensive documentation audit:

    1. REDUNDANCY CHECK:
       - Find documents with >40% similar content
       - Identify duplicate sections across files

    2. CONFLICT CHECK:
       - Extract pipeline descriptions from all docs
       - Flag any that differ from canonical (4-pass)
       - Check phase numbers are consistent

    3. STALENESS CHECK:
       - Check last-modified dates vs. current phase
       - Flag docs referencing old phases
       - Identify outdated cost estimates

    4. ORPHAN CHECK:
       - Find files not referenced by any other doc
       - Identify broken links

    Generate comprehensive audit report with prioritized fixes.
    """

    # Would invoke Task tool here

    print("Monthly audit complete. See docs/AUDIT_REPORT.md")

if __name__ == "__main__":
    monthly_audit()
```

---

## Best Practices

### ✅ DO:
- Use agents for tasks affecting 5+ files
- Run parallel agents when tasks are independent
- Always generate before/after comparison reports
- Use git mv for moving files (preserves history)
- Validate links after any reorganization
- Keep audit reports for future reference

### ❌ DON'T:
- Manually edit 10+ files (use agents instead)
- Delete files without archiving first
- Move files without updating cross-references
- Skip validation step after consolidation
- Create new docs without checking for existing ones

---

## Monitoring Documentation Health

### Key Metrics to Track

**Redundancy Score**:
```
Redundancy % = (Duplicate Content Lines / Total Documentation Lines) × 100

Target: < 20%
Current: ~70% (before consolidation)
After: ~15% (after consolidation)
```

**Consistency Score**:
```
Count of conflicting statements about:
- Pipeline architecture
- Phase number
- Development status

Target: 0 conflicts
```

**Maintenance Burden**:
```
Average time to find specific information

Target: < 2 minutes
Indicator: If > 5 minutes, docs need reorganization
```

**Accuracy Score**:
```
% of status documents reflecting current reality

Target: 100%
Check: README.md, PROJECT_STATUS.md, CONTEXT.md
```

---

## Troubleshooting

### Issue: Agent Creates Duplicate Content
**Symptom**: New doc has sections from existing docs

**Solution**:
- Update agent prompt to explicitly check for existing docs
- Require agent to provide content mapping
- Add validation step comparing new vs existing content

---

### Issue: Broken References After Archiving
**Symptom**: Links pointing to archived files

**Solution**:
- Always run Cross-Reference Updater (Agent 4) after archiving
- Use link validation before git commit
- Keep ARCHIVE_INDEX.md with redirect information

---

### Issue: Conflicting Information Persists
**Symptom**: Multiple docs still describe different architectures

**Solution**:
- Run Consistency Validator (Agent 7) after consolidation
- Identify which doc is canonical
- Add deprecation notices to others
- Eventually archive non-canonical versions

---

## Future Enhancements

### Planned Improvements

**1. Automated Session Documentation** (Priority: High)
- After each session, automatically:
  - Extract session summary from conversation
  - Update IMPLEMENTATION_LOG.md
  - Update README.md and PROJECT_STATUS.md
  - No manual documentation needed

**2. Smart Link Resolver** (Priority: Medium)
- Detect broken links on git commit
- Suggest correct targets
- Auto-fix common patterns

**3. Documentation Preview** (Priority: Low)
- Before consolidation, show:
  - What will be merged
  - What will be archived
  - What will be deleted
- Require approval before execution

**4. Diff-Based Change Detection** (Priority: Medium)
- Track git diffs for documentation changes
- Alert if critical docs modified without review
- Maintain changelog for major doc updates

---

## Conclusion

This agentic workflow transforms documentation maintenance from a tedious manual process into an efficient, automated system. By defining specialized agents and clear workflows, we can:

- **Reduce effort**: 10 hours → 4-6 hours for major consolidation
- **Improve consistency**: Automated validation prevents conflicts
- **Maintain accuracy**: Regular audits catch drift early
- **Scale effectively**: Works for 50 files or 500 files

**Next Steps**:
1. Review this workflow document
2. Execute Workflow 1 (Initial Consolidation) using agents
3. Implement automation scripts for ongoing maintenance
4. Schedule monthly reviews using Workflow 3

The key principle: **Let agents do the heavy lifting while you focus on high-level decisions and validation.**
