# Session Prompts

Use these prompts at the **start** and **end** of each development session to maintain project continuity.

---

## 🚀 Session START Prompt

Copy and paste to your LLM at the beginning of each session:

```
I'm starting a new development session on the Psalms AI Analysis project.

**Project location:** C:\Users\ariro\OneDrive\Documents\Psalms

**Please read these files before we begin:**
1. `docs/session_tracking/PROJECT_STATUS.md` - Current session number, active features, recent work
2. `docs/session_tracking/IMPLEMENTATION_LOG.md` - Most recent session details
3. `docs/session_tracking/scriptReferences.md` - All 50+ scripts with namespaces & descriptions (READ THIS FIRST when looking for code)

**Key files to know:**
- `CLAUDE.md` - Project summary for LLM context
- `docs/architecture/TECHNICAL_ARCHITECTURE_SUMMARY.md` - System architecture

**After reading, ask me:** "What would you like to work on in Session [N]?"

**Today's goal:** [Describe what you want to accomplish]
```

---

## ✅ Session END Prompt

Copy and paste when you're finishing a session:

```
We're wrapping up this session. Please update the session documentation:

**1. Update IMPLEMENTATION_LOG.md** - Add this session's entry at the TOP:
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
- **Recent Work Summary (after line 55)**: Add a new 3-bullet entry AT THE TOP
- **Active Features (line 22)**: Add any new features if applicable

**3. Update scriptReferences.md** if you created or significantly modified any scripts:
- Add new scripts with namespace, description, and file link
- Update descriptions if functionality changed significantly

**4. Confirm what was accomplished** in a brief summary for my records.
```

---

## Archive Note

Historical sessions are archived in:
- Sessions 1-149: `docs/archive/documentation_cleanup/IMPLEMENTATION_LOG_sessions_1-149_2025-12-04.md`
- Sessions 150-199: `docs/archive/documentation_cleanup/IMPLEMENTATION_LOG_sessions_150-199_2026-01-12.md`
