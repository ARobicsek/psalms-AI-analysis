# Session Documentation Prompt

This file contains two prompts:
1. **Session START Prompt** - Use at the beginning of each session
2. **Session END Prompt** - Use at the end of each session

---

## Session START Prompt

**Instructions**:
1. First, take 5 minutes to follow the "Quick Context Gathering" below
2. Then fill out the rest of this prompt with the information you found
3. This ensures you start each session with full awareness of project state

### Current Session Context

**Session Number**: ___ (from SESSION HISTORY section)
**Date**: [Today's date]
**Previous Session**: Session ___ (see RECENT WORK SUMMARY)
**Last Working On**: [What was done in the most recent session]
**Current Project Phase**: [from EXECUTIVE SUMMARY]

### Session Goals

1. **Primary Goal**: [Main objective for this session]
2. **Secondary Goals**:
   - [Goal 2]
   - [Goal 3]
   - [Goal 4]

### Quick Context Gathering (5 minutes)

**Step 1: Open PROJECT_STATUS.md**
- Location: `docs/session_tracking/PROJECT_STATUS.md`

**Step 2: Review These Sections**

**Executive Summary (Top)**:
- Current phase: Are we still in "Pipeline Production"?
- Current session number: ___ (update this)

**Current System State**:
- Pipeline phases: Any status changes (✅🟠❌)?
- Active Features: Any new features added?
- Known Limitations: Any new limitations or ones that might affect this session?

**Recent Work Summary (Last 5 sessions)**:
- What was done in the most recent session?
- Any patterns or recurring issues?
- Features that were recently implemented

**Feature Documentation** (if working on specific features):
- Find the relevant feature section (Core, Research, Pipeline, Document)
- Review current implementation details
- Check for any "In Progress" or known issues

**Session History**:
- Find the last session number to determine current session number
- Briefly scan recent detailed sessions for related work

### Prerequisites Check

After reviewing PROJECT_STATUS.md:
- [ ] Understand current project phase and status
- [ ] Identified any blocking issues from "Known Limitations"
- [ ] Noted any recent changes that might affect current work
- [ ] Checked if any features are "In Progress" that need completion

### Session Plan

1. **Step 1**: [First action to take]
   - Expected outcome: [What should be accomplished]
   - Potential issues: [What might go wrong]

2. **Step 2**: [Second action to take]
   - Expected outcome: [What should be accomplished]
   - Potential issues: [What might go wrong]

3. **Step 3**: [Third action to take]
   - Expected outcome: [What should be accomplished]
   - Potential issues: [What might go wrong]

### Success Criteria

Session will be considered successful if:
- [ ] Primary goal is achieved
- [ ] At least ___ secondary goals are completed
- [ ] All changes are tested and working
- [ ] Documentation is updated if needed
- [ ] Code is committed with clear message





### Notes for Session End

**Things to remember for documentation**:
- [Key decisions made]
- [Files modified]
- [New patterns discovered]
- [Issues encountered and resolved]

---

## Session END Prompt

---

## Session Documentation Update

Please update the PROJECT_STATUS.md file to reflect today's work session. Follow this structured format:

### 1. Add Session to Section 3: Recent Work Summary

Add a brief 3-bullet point entry for the new session:

```markdown
### Session XXX (YYYY-MM-DD): [Session Title]
- [Key achievement 1 - what changed]
- [Key achievement 2 - what was fixed/implemented]
- [Key achievement 3 - impact/result]
```

**Rules**:
- Focus on what changed, not full technical details
- Keep bullets concise and action-oriented
- Reference detailed section for more info

### 2. Add Detailed Session Entry

Add to Section 5 (Session History) in the appropriate subsection:

**For Sessions 200+ (Full Details)**:
```markdown
#### Session XXX (YYYY-MM-DD): [Session Title]
**Objective**: [Brief statement of the session's goal]

**Problems Identified**:
- [Problem 1]
- [Problem 2]

**Solutions Implemented**:
1. [Solution 1 with technical details]
2. [Solution 2 with technical details]

**Files Modified**:
- `path/to/file.py` - [brief description of changes]
```

**For Sessions 1-199 (Concise Summaries)**:
Update the appropriate phase summary with the new session's contribution.

### 3. Update Executive Summary

If applicable, update these sections:
- **Current Phase**: If phase has changed
- **Progress Summary**:
  - Update "Current Session" number
  - Add new features to "Active Features" list

### 4. Update Current System State

If applicable, update:
- **Pipeline Phases**: Change status indicators (✅🟠❌)
- **Active Features**: Add new features or move to documentation
- **Known Limitations**: Add or remove limitations

### 5. Update Feature Documentation

If session introduced a new feature or significantly changed an existing one:

**For New Features**:
Add to appropriate subsection with this format:

```markdown
#### [Feature Name] (Session XXX) ✅
[Brief description of the feature and its purpose]
[Key implementation details]
[Usage instructions if applicable]
```

**For Feature Updates**:
Add to existing feature description with update details.

### 6. Update Reference Materials

If applicable:
- **Quick Commands**: Add new command examples
- **Directory Structure**: Add new directories if created
- **Database Status**: Update if schema changed

### 7. Maintain Organization Rules

**Always follow these rules**:

1. **Maintain chronological order**:
   - Section 3: Add new session to TOP of "Recent Work Summary"
   - Section 5: Add new session to BOTTOM of appropriate subsection

2. **Keep section lengths balanced**:
   - If Section 3 exceeds 5 sessions, move oldest to Section 5
   - Always maintain exactly 5 sessions in "Recent Work Summary"

3. **Update table of contents** if adding new major sections

4. **Preserve formatting consistency**:
   - Use ✅🟠❌ emojis for status indicators
   - Maintain consistent heading levels (### for main sections, #### for subsections)
   - Use code blocks for file paths and commands

5. **Check for duplication**:
   - Remove redundant information between sections
   - Ensure features aren't documented in multiple places
   - Update superseded information appropriately

### 8. Final Review Checklist

Before finishing:
- [ ] Table of contents links are correct
- [ ] Session numbers are sequential and correct
- [ ] No duplicate information between sections
- [ ] All new files mentioned are correctly listed
- [ ] Status indicators are updated appropriately
- [ ] "Last Updated" date at top reflects today's date
- [ ] Executive summary accurately reflects current state

### Example Template for Copy-Paste

```markdown
### Session XXX (YYYY-MM-DD): [Session Title]
- [Brief achievement 1]
- [Brief achievement 2]
- [Brief achievement 3]

#### Session XXX (YYYY-MM-DD): [Session Title]
**Objective**: [Goal]

**Problems Identified**:
- [Problem 1]

**Solutions Implemented**:
1. [Solution 1]

**Files Modified**:
- `path/to/file.py` - [description]
```

---

**Remember**: The goal is to maintain a document that is:
1. **Quick to scan** for current status
2. **Easy to navigate** for specific information
3. **Complete** without being redundant
4. **Consistent** in format and organization