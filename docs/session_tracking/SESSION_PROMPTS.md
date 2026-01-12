# Session Prompts

Use these prompts at the **start** and **end** of each development session to maintain project continuity.

---

## 🚀 Session START Prompt

Copy and paste to your LLM at the beginning of each session:

```
I'm starting a new development session on the Psalms AI Analysis project.

**Quick context:**
- Project location: C:\Users\ariro\OneDrive\Documents\Psalms
- Current status: See docs/session_tracking/PROJECT_STATUS.md
- Recent history: See docs/session_tracking/IMPLEMENTATION_LOG.md

**Please do the following before we begin:**
1. Read PROJECT_STATUS.md to understand:
   - Current session number (update +1 for this session)
   - Active features and their status
   - Recent work summary (last 5 sessions)
   - Any known limitations that might affect today's work

2. Check the IMPLEMENTATION_LOG.md for the most recent session to understand what was just completed.

3. Then ask me: "What would you like to work on in Session [N]?"

**Today's goal:** [Describe what you want to accomplish]
```

---

## ✅ Session END Prompt

Copy and paste when you're finishing a session:

```
We're wrapping up this session. Please update the session documentation:

**1. Update IMPLEMENTATION_LOG.md** - Add this session's entry at the TOP (after the header/archive links, before Session 236):
---
## Session [N] (YYYY-MM-DD): [Brief Title]

**Objective**: [One-line goal]

**Problems Identified** (if any):
- [Problem 1]

**Solutions Implemented**:
1. [What was done]

**Files Modified**:
- `path/to/file.py` - [brief description]
---

**2. Update PROJECT_STATUS.md** in THREE places:
- **Header (lines 3, 21)**: Update "Last Updated" date and "Current Session" number
- **Recent Work Summary (after line 55)**: Add a new 3-bullet entry AT THE TOP of the list (before the previous session)
- **Active Features (line 22)**: Add any new features if applicable

**3. Confirm what was accomplished** in a brief summary for my records.
```

---

## 💡 Tips for Effective Sessions

### Starting Well
- **Be specific** about your goal — "Fix the login bug" is better than "Improve auth"
- **Mention blockers** — If something didn't work last session, say so upfront
- **Share context** — Open relevant files before starting so the LLM can see them

### Ending Well
- **Complete the docs** before ending — it takes 2 minutes and saves future confusion
- **Note unfinished work** — If you stopped mid-task, add it to the session notes
- **Test before closing** — Verify your changes work

### Session Numbering
- Sessions are numbered sequentially (1, 2, 3... currently at 235+)
- Each new conversation = new session number
- Check PROJECT_STATUS.md line 21 for the current number

---

## Quick Reference: Key Files

| File | Purpose |
|------|---------|
| `docs/session_tracking/PROJECT_STATUS.md` | Current state, features, recent work |
| `docs/session_tracking/IMPLEMENTATION_LOG.md` | Detailed session history |
| `docs/architecture/TECHNICAL_ARCHITECTURE_SUMMARY.md` | System architecture overview |
| `CLAUDE.md` | Project summary for LLM context |

---

## Archive Note

Historical sessions are archived in:
- Sessions 1-149: `docs/archive/documentation_cleanup/IMPLEMENTATION_LOG_sessions_1-149_2025-12-04.md`
- Sessions 150-199: `docs/archive/documentation_cleanup/IMPLEMENTATION_LOG_sessions_150-199_2026-01-12.md`
