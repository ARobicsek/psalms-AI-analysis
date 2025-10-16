# Session Management Guide

## Purpose
This document defines protocols for maintaining project documentation across work sessions, ensuring continuity and tracking progress.

---

## Session Start Protocol

### 1. Read These Documents First (in order)
- [ ] `docs/CONTEXT.md` - Quick project overview
- [ ] `docs/PROJECT_STATUS.md` - Current task and progress
- [ ] `docs/IMPLEMENTATION_LOG.md` - Recent learnings (last 2-3 entries)

### 2. Session Initialization Prompt

Use this exact prompt when starting a new session:

```
I'm continuing work on the Psalms AI commentary pipeline.

Please read these files in order:
1. docs/CONTEXT.md (project overview)
2. docs/PROJECT_STATUS.md (current status)
3. docs/IMPLEMENTATION_LOG.md (scroll to most recent entry)

Based on PROJECT_STATUS.md, what is the next task I should work on?
```

### 3. Confirm Understanding
The AI assistant should respond by:
- Confirming current phase and day
- Summarizing the next task
- Noting any blockers from PROJECT_STATUS.md
- Referencing recent learnings from IMPLEMENTATION_LOG.md

---

## During Session Protocol

### Document Updates (Continuous)

#### IMPLEMENTATION_LOG.md - Update As You Go
Add entries in real-time for:
- ✅ Key learnings or "aha!" moments
- ✅ Decisions made and their rationale
- ✅ Issues encountered and solutions
- ✅ Useful code snippets
- ✅ Performance metrics

**When to update**:
- Immediately after solving a problem
- When making an architectural decision
- After discovering something surprising
- When completing a meaningful sub-task

#### PROJECT_STATUS.md - Update After Each Task
Update checklist items:
- Mark completed tasks with ✅
- Update progress percentages
- Add/remove blockers
- Update metrics (costs, psalms processed, etc.)

**When to update**:
- After completing each checklist item
- When discovering new blockers
- When processing costs/metrics change

---

## Session End Protocol

### Mandatory End-of-Session Updates

#### 1. IMPLEMENTATION_LOG.md
Add a session summary:

```markdown
### End of Session - [TIME]
**Duration**: [X hours]
**Tasks Completed**:
- [Task 1]
- [Task 2]

**Key Outcomes**:
- [Outcome 1]
- [Outcome 2]

**Decisions Made**:
- [Decision + rationale]

**For Next Session**:
- [ ] [Next immediate task]
- [ ] [Following task]

**Blockers**:
- [Any issues to address]

---
```

#### 2. PROJECT_STATUS.md
Update the following sections:
```markdown
## Current Task
- [x] [Completed items from this session]
- [ ] [Remaining items - update as needed]

## Progress
- Overall: X% complete (updated)
- Current phase: Y% complete (updated)

## Completed
✅ [Add newly completed items here]

## Blockers
[Update any new blockers or remove resolved ones]

## Metrics
- Psalms processed: X/150 (updated)
- Total cost so far: $X.XX (updated)
- Average cost per psalm: $X.XX (calculated)

## Quick Links
- Last session: [TODAY'S DATE, brief topic]
```

#### 3. Git Commit
Always commit at end of session:
```bash
git add .
git commit -m "Day X: [Brief description of work completed]

- [Specific achievement 1]
- [Specific achievement 2]
- [Specific achievement 3]

Next: [Next task from PROJECT_STATUS.md]"
```

---

## Quality Checklist

### Before Ending Session

- [ ] IMPLEMENTATION_LOG.md has entry for today with:
  - Date and session duration
  - Key learnings
  - Decisions with rationale
  - Issues and solutions
  - Next steps

- [ ] PROJECT_STATUS.md reflects current state:
  - Checkboxes updated
  - Progress percentages accurate
  - Metrics current
  - "Last session" updated with today's date

- [ ] ARCHITECTURE.md updated if:
  - New schemas added
  - New functions implemented
  - New patterns established

- [ ] All code changes committed with descriptive message

- [ ] No secrets/API keys in committed files

---

## Document Maintenance Schedule

### Daily (Every Session)
- ✅ IMPLEMENTATION_LOG.md: Add session entry
- ✅ PROJECT_STATUS.md: Update checklists and metrics
- ✅ Git commit with descriptive message

### As Needed
- ⚙️ ARCHITECTURE.md: Add schemas/APIs as implemented
- ⚙️ CONTEXT.md: Update if project scope or approach changes

### Weekly (Every 5 days / End of Phase)
- 📊 PROJECT_STATUS.md: Review phase completion
- 📊 IMPLEMENTATION_LOG.md: Add weekly summary
- 📊 CONTEXT.md: Update cost estimates based on actuals

### End of Project
- 📝 Final summary in IMPLEMENTATION_LOG.md
- 📝 Complete metrics in PROJECT_STATUS.md
- 📝 Usage guide for generated materials

---

## Common Mistakes to Avoid

❌ **Don't**: Start session without reading status docs
✅ **Do**: Always read CONTEXT → PROJECT_STATUS → IMPLEMENTATION_LOG first

❌ **Don't**: Wait until end of session to update logs
✅ **Do**: Update IMPLEMENTATION_LOG as you learn/decide things

❌ **Don't**: Use vague commit messages ("updates", "fixes")
✅ **Do**: Describe what changed and why

❌ **Don't**: Forget to update progress percentages
✅ **Do**: Update percentages after each task completion

❌ **Don't**: Leave blockers unaddressed in status
✅ **Do**: Document blockers immediately and note when resolved

---

## Template Reminders

### Quick Session End Checklist
```
□ Implementation log updated with session summary
□ Project status checklists updated
□ Progress percentages recalculated
□ Metrics updated (if applicable)
□ "Last session" field updated with today's date
□ Git commit with descriptive message
□ No API keys or secrets committed
```

### AI Assistant Session End Prompt
At end of session, use:

```
We're ending this session. Please help me update the project documentation:

1. Review what we accomplished today
2. Generate an IMPLEMENTATION_LOG.md entry for this session
3. Update PROJECT_STATUS.md with:
   - Completed tasks (check boxes)
   - Updated progress percentages
   - New metrics if applicable
   - "Last session" field with today's date
4. Suggest a git commit message describing today's work
```

---

## Why This Matters

**Continuity**: Next session starts where this one left off, no time wasted reconstructing context

**Accountability**: Clear record of progress, decisions, and learnings

**Debugging**: When issues arise, IMPLEMENTATION_LOG shows what changed and when

**Cost Tracking**: Accurate metrics help stay within budget

**Knowledge Transfer**: Anyone (including future you) can understand project state and history

---

*This protocol ensures project momentum and makes every session productive.*
*Treat these updates as part of the work, not optional extras.*