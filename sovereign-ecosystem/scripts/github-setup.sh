#!/usr/bin/env bash
# One-time setup: authenticate GitHub CLI, upload SSH key, create repo, push.
set -euo pipefail

export PATH="/home/shootle/bin:$PATH"
REPO_DIR="/home/shootle/sovereign-ecosystem"

echo "==> Step 1: Log in to GitHub (browser will open or you'll get a one-time code)"
gh auth login --hostname github.com --git-protocol ssh --web

echo "==> Step 2: Upload SSH public key to your Shootle account"
gh ssh-key add "$HOME/.ssh/github.pub" --title "cursor-wsl-$(hostname)-$(date +%Y%m%d)"

echo "==> Step 3: Create Shootle/sovereign-ecosystem and push"
cd "$REPO_DIR"

REMOTE_URL="git@github.com:Shootle/sovereign-ecosystem.git"
if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE_URL"
else
  git remote add origin "$REMOTE_URL"
fi

if gh repo view Shootle/sovereign-ecosystem >/dev/null 2>&1; then
  echo "Repository already exists on GitHub; pushing local main"
else
  gh repo create sovereign-ecosystem \
    --public \
    --source=. \
    --remote=origin \
    --description "Sovereign ecosystem: telemetry protocol, Zeegate, Bytenergy, Tegalchain bridge"
fi

git push -u origin main

echo "==> Step 4: Verify SSH to GitHub"
ssh -T git@github.com || true

echo
echo "Done. Repository: https://github.com/Shootle/sovereign-ecosystem"
echo
echo "Replit SSH key (add manually in Replit SSH pane):"
cat "$HOME/.ssh/replit.pub"
