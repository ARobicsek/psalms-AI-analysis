# Session Prompts

Use these prompts at the **start** and **end** of each development session to maintain project continuity.

---

## 🚀 Session START Prompt

Copy and paste to your LLM at the beginning of each session:

```
I'm starting a new development session on the Psalms AI Analysis project.

**Project location:** C:\Users\ariro\OneDrive\Documents\Psalms

**Please read this file before we begin:**
- `docs/session_tracking/PROJECT_STATUS.md` — Current session number, active features, recent work, quick commands, key directories

**Read these ONLY if needed for today's task:**
- `docs/session_tracking/scriptReferences.md` — When you need to find a specific script
- `docs/architecture/TECHNICAL_ARCHITECTURE_SUMMARY.md` — When you need to understand system architecture
- `docs/session_tracking/IMPLEMENTATION_LOG.md` — When you need details on a past session

**Today's goal:** 
```

---

## ✅ Session END Prompt

Copy and paste when you're finishing a session:

```
We're wrapping up this session. Please update the session documentation, then commit your work.

**1. Update IMPLEMENTATION_LOG.md** — Add this session's entry at the TOP:
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

**2. Update PROJECT_STATUS.md** in TWO places:
- **Header (line 3)**: Update "Last Updated" date and session number
- **Recent Work Summary**: Replace the OLDEST of the 5 entries with a new entry for this session AT THE TOP (keep only 5)

**3. Update scriptReferences.md** if you created or significantly modified any scripts.

**4. Confirm what was accomplished** in a brief summary for my records.
```

---

## Archive Note

Historical sessions are archived in:
- Sessions 1-149: `docs/archive/documentation_cleanup/IMPLEMENTATION_LOG_sessions_1-149_2025-12-04.md`
- Sessions 150-199: `docs/archive/documentation_cleanup/IMPLEMENTATION_LOG_sessions_150-199_2026-01-12.md`
