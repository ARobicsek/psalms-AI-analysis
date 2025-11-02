#!/bin/bash
# Remove API key line from .claude/settings.local.json

if [ -f .claude/settings.local.json ]; then
    # Remove the line containing the API key export
    sed -i '/export ANTHROPIC_API_KEY=/d' .claude/settings.local.json
    git add .claude/settings.local.json
fi
