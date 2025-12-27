#!/bin/bash

# This script sets up git, initializes repo, and connects it to GitHub

set -e  # exit if any command fails

# Load credentials
if [ ! -f $HOME/FamilyTree/helper_scripts/github_credentials.env ]; then
  echo "github_credentials.env not found! Create it first."
  exit 1
fi
source $HOME/FamilyTree/helper_scripts/github_credentials.env

# Navigate to project folder
cd $HOME/FamilyTree || exit 1

# Git Initialization
git init

# Set Git config
git config user.name "$GITHUB_USERNAME"
git config user.email "${GITHUB_USERNAME}@users.noreply.github.com"

# Add remote repository
REMOTE_URL="https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"

if git remote | grep -q origin; then
  git remote set-url origin "$REMOTE_URL"
else
  git remote add origin "$REMOTE_URL"
fi

echo "Git initialized and remote configured for $REPO_NAME"

