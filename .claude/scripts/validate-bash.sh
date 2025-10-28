#!/bin/bash
COMMAND=$(cat | jq -r '.tool_input.command')

# --- This is the part customized for your project ---
# We block logs, output, python cache/virtual environments, and .git
BLOCKED="logs/|output/|__pycache__|\.git/|venv/|\.venv/|\.env"

if echo "$COMMAND" | grep -qE "$BLOCKED"; then
 echo "ERROR: Blocked directory pattern found in command." >&2
 exit 2
fi