#!/bin/bash
# setup_workers.sh - Scaffolds Kanban Worker profiles for Abelion Research

set -e

# Default profile to clone from (assumes 'enami-asa' or 'default')
SOURCE_PROFILE="enami-asa"

echo "Setting up Kanban Worker Profiles (cloning from $SOURCE_PROFILE)..."

# 1. Engineering Division
echo "Creating worker-engineer..."
hermes profile create worker-engineer --clone-from "$SOURCE_PROFILE" --description "Engineering Division. Focuses on writing code, debugging, linting, testing, and fixing software architecture issues. Use this profile for any technical implementation or code refactoring tasks." || echo "Profile worker-engineer already exists or failed."

# 2. Research Division
echo "Creating worker-research..."
hermes profile create worker-research --clone-from "$SOURCE_PROFILE" --description "Research Division. Focuses on web search, documentation reading, summarization, and compiling research notes into markdown files. Use this profile for information gathering and analysis tasks." || echo "Profile worker-research already exists or failed."

# 3. QA / Security Division
echo "Creating worker-qa..."
hermes profile create worker-qa --clone-from "$SOURCE_PROFILE" --description "QA and Security Division. Focuses on code review, security audits, secret redaction checks, and testing infrastructure. Use this profile to verify the integrity and safety of code." || echo "Profile worker-qa already exists or failed."

echo "Setup complete. Run 'hermes kanban assignees' to verify."
