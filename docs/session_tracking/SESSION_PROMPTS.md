# Session Prompts

Use these prompts at the **start** and **end** of each development session to maintain project continuity.

---

## Session START Prompt (for Gemini or any non-Claude-Code LLM)

Claude Code auto-loads `CLAUDE.md` — no start prompt needed. For Gemini, copy-paste:

```
I'm starting a new development session on the Psalms AI Analysis project.

**Project location:** C:\Users\ariro\OneDrive\Documents\Psalms

**Please read `CLAUDE.md` in the project root before we begin.** It contains the current session number, recent work, quick commands, and key directories.

**Read these ONLY if needed for today's task:**
- `docs/session_tracking/scriptReferences.md` — When you need to find a specific script
- `docs/architecture/TECHNICAL_ARCHITECTURE_SUMMARY.md` — When you need to understand system architecture
- `docs/session_tracking/IMPLEMENTATION_LOG.md` — When you need details on a past session
- `docs/session_tracking/PROJECT_STATUS.md` — Pipeline phases, active features, databases

**Today's goal:**
```

---

## Session END Prompt

Copy and paste when finishing a session:

```
We're wrapping up this session. Please update the session documentation, then commit your work.

**1. Update CLAUDE.md** in TWO places:
- **Line 3**: Update session number (increment by 1) and date
- **Recent Work Summary**: Replace the OLDEST of the 5 entries with a new 3-line entry for this session AT THE TOP (keep only 5)

**2. Update IMPLEMENTATION_LOG.md** — Add this session's entry at the TOP:
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

**3. Update scriptReferences.md** if you created or significantly modified any scripts.

**4. Confirm what was accomplished** in a brief summary for my records.
```

---

## Archive Note

Historical sessions are archived in:
- Sessions 1-149: `docs/archive/documentation_cleanup/IMPLEMENTATION_LOG_sessions_1-149_2025-12-04.md`
- Sessions 150-199: `docs/archive/documentation_cleanup/IMPLEMENTATION_LOG_sessions_150-199_2026-01-12.md`
- Sessions 241-299: `docs/archive/documentation_cleanup/IMPLEMENTATION_LOG_sessions_241-299_2026-03-18.md`
