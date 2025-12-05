#!/usr/bin/env bash
set -euo pipefail

changelog_file="$(mktemp)"
cz bump --allow-no-commit --yes --changelog-to-stdout --git-output-to-stderr > "$changelog_file"

git push origin main
sleep 1
git push --tags
sleep 1
gh release create "$(cz version -p)" --verify-tag -t "Release $(cz version -p)" -F "$changelog_file"
rm "$changelog_file"
