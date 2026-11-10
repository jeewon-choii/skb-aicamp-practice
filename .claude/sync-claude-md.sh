#!/bin/sh
# CLAUDE.md 와 CLAUDE.txt 를 같은 내용으로 맞춘다.
# 두 파일 중 더 최근에 수정된 쪽의 내용을 다른 쪽에 복사한다.
DIR="$(cd "$(dirname "$0")/.." && pwd)"
MD="$DIR/CLAUDE.md"
TXT="$DIR/CLAUDE.txt"

if [ -f "$MD" ] && [ ! -f "$TXT" ]; then
  cp -p "$MD" "$TXT"
elif [ -f "$TXT" ] && [ ! -f "$MD" ]; then
  cp -p "$TXT" "$MD"
elif [ -f "$MD" ] && [ -f "$TXT" ]; then
  if ! cmp -s "$MD" "$TXT"; then
    if [ "$TXT" -nt "$MD" ]; then
      cp -p "$TXT" "$MD"
    else
      cp -p "$MD" "$TXT"
    fi
  fi
fi
exit 0
