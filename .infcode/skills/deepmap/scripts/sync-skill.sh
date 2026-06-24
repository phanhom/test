#!/bin/bash
# sync-skill.sh — Generate SKILL.md from SKILL.md.template by injecting DEEPMAP_AVAILABLE_REPOS
#
# Usage:
#   cd ~/.agents/skills/deepmap
#   ./scripts/sync-skill.sh
#
# This reads DEEPMAP_AVAILABLE_REPOS from .env and replaces {{AVAILABLE_REPOS}}
# in SKILL.md.template, writing the result to SKILL.md.
# SKILL.md is a generated file — edit SKILL.md.template instead.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$SKILL_DIR/.env"
TEMPLATE_FILE="$SKILL_DIR/SKILL.md.template"
SKILL_FILE="$SKILL_DIR/SKILL.md"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "Error: .env not found at $ENV_FILE" >&2
    exit 1
fi

if [[ ! -f "$TEMPLATE_FILE" ]]; then
    echo "Error: SKILL.md.template not found at $TEMPLATE_FILE" >&2
    echo "Create it from SKILL.md by adding {{AVAILABLE_REPOS}} placeholder." >&2
    exit 1
fi

# Read DEEPMAP_AVAILABLE_REPOS from .env
repos_raw=$(grep "^DEEPMAP_AVAILABLE_REPOS=" "$ENV_FILE" | cut -d'=' -f2- || true)

if [[ -z "$repos_raw" ]]; then
    echo "Warning: DEEPMAP_AVAILABLE_REPOS not found in .env" >&2
    echo "Add it like: DEEPMAP_AVAILABLE_REPOS=owner/repo:desc,owner/repo2:desc2" >&2
    exit 0
fi

# Parse repo list into human-readable format
# Input:  owner/repo:description,owner/repo2:description2
# Output: owner/repo (description), owner/repo2 (description2)
repos_formatted=""
IFS=',' read -ra REPO_ARRAY <<< "$repos_raw"
for repo_spec in "${REPO_ARRAY[@]}"; do
    repo_spec=$(echo "$repo_spec" | xargs) # trim whitespace
    if [[ "$repo_spec" == *":"* ]]; then
        repo_name="${repo_spec%%:*}"
        repo_desc="${repo_spec#*:}"
        # Replace underscores with spaces in description
        repo_desc="${repo_desc//_/ }"
        if [[ -n "$repos_formatted" ]]; then
            repos_formatted="$repos_formatted, "
        fi
        repos_formatted="$repos_formatted$repo_name ($repo_desc)"
    else
        if [[ -n "$repos_formatted" ]]; then
            repos_formatted="$repos_formatted, "
        fi
        repos_formatted="$repos_formatted$repo_spec"
    fi
done

# Generate SKILL.md from template
cp "$TEMPLATE_FILE" "$SKILL_FILE"

# Replace {{AVAILABLE_REPOS}} placeholder
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s|{{AVAILABLE_REPOS}}|$repos_formatted|g" "$SKILL_FILE"
else
    sed -i "s|{{AVAILABLE_REPOS}}|$repos_formatted|g" "$SKILL_FILE"
fi

echo "✅ Generated SKILL.md from template (${#REPO_ARRAY[@]} repos)"
echo "   Repos: $repos_formatted"
echo "   Note: SKILL.md is auto-generated. Edit SKILL.md.template for permanent changes."
