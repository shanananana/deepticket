#!/usr/bin/env bash
# 从 Keep a Changelog 格式 CHANGELOG 提取指定 tag 的 Release 标题与正文。
# 用法: extract_changelog_release.sh v0.1.2 [CHANGELOG.md]
set -euo pipefail

TAG="${1:?tag required, e.g. v0.1.2}"
FILE="${2:-CHANGELOG.md}"
VERSION="${TAG#v}"

if [[ ! -f "$FILE" ]]; then
  echo "ERROR: changelog not found: $FILE" >&2
  exit 1
fi

BODY="$(awk -v ver="$VERSION" '
  $0 ~ "^## \\[" ver "\\]" { capture=1; next }
  capture && /^## \[/ { exit }
  capture && /^---$/ { exit }
  capture { print }
' "$FILE")"

if [[ -z "${BODY//[[:space:]]/}" ]]; then
  echo "ERROR: no section ## [$VERSION] in $FILE" >&2
  exit 1
fi

TITLE_LINE="$(printf '%s\n' "$BODY" | awk '
  /^### Added$/ { in_added=1; next }
  in_added && /^- \*\*/ {
    gsub(/^- \*\*/, "", $0)
    gsub(/\*\*.*/, "", $0)
    gsub(/:.*/, "", $0)
    print $0
    exit
  }
')"

if [[ -n "$TITLE_LINE" ]]; then
  TITLE="${TAG} — ${TITLE_LINE}"
else
  TITLE="${TAG}"
fi

printf 'TITLE=%s\n' "$TITLE"
printf 'BODY<<EOF\n%s\nEOF\n' "$BODY"
