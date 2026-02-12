#!/usr/bin/env bash
set -euo pipefail

branch="$(git rev-parse --abbrev-ref HEAD)"

if [[ -z "$(git remote)" ]]; then
  echo "No git remote is configured for this repository."
  echo "Current branch: ${branch}"
  exit 0
fi

upstream="$(git for-each-ref --format='%(upstream:short)' "refs/heads/${branch}")"

if [[ -z "${upstream}" ]]; then
  echo "No upstream tracking branch is configured for '${branch}'."
  echo "Available remotes:"
  git remote -v
  exit 0
fi

echo "Fetching latest refs from remotes..."
git fetch --all --prune

read -r behind ahead < <(git rev-list --left-right --count "${upstream}...HEAD")

echo "Branch: ${branch}"
echo "Upstream: ${upstream}"
echo "Behind upstream by: ${behind} commit(s)"
echo "Ahead of upstream by: ${ahead} commit(s)"

if [[ "${behind}" -eq 0 && "${ahead}" -eq 0 ]]; then
  echo "Status: In sync with upstream."
elif [[ "${behind}" -gt 0 && "${ahead}" -eq 0 ]]; then
  echo "Status: Local branch is behind upstream."
elif [[ "${behind}" -eq 0 && "${ahead}" -gt 0 ]]; then
  echo "Status: Local branch is ahead of upstream."
else
  echo "Status: Local and upstream have diverged."
fi
