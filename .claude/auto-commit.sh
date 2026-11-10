#!/bin/sh
# Claude 응답이 끝날 때(Stop hook) 바뀐 파일을 자동으로 커밋한다.
# - 바뀐 파일이 없으면 아무것도 하지 않는다.
# - 병합·리베이스 중이거나 다른 Git 작업이 진행 중이면 건너뛴다.
# - .gitignore에 있는 파일(.venv, .DS_Store, ~$ 임시 파일)은 커밋하지 않는다.
DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$DIR" || exit 0
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

GITDIR="$(git rev-parse --git-dir)"
if [ -e "$GITDIR/MERGE_HEAD" ] || [ -d "$GITDIR/rebase-merge" ] || \
   [ -d "$GITDIR/rebase-apply" ] || [ -e "$GITDIR/index.lock" ]; then
  exit 0
fi

[ -z "$(git status --porcelain)" ] && exit 0

git add -A
N=$(git -c core.quotepath=false diff --cached --name-only | wc -l | tr -d ' ')
[ "$N" = "0" ] && exit 0

NAMES=$(git -c core.quotepath=false diff --cached --name-only | head -3 | \
  while IFS= read -r f; do basename "$f"; done | paste -sd ',' - | sed 's/,/, /g')
if [ "$N" -gt 3 ]; then
  NAMES="$NAMES 외 $((N - 3))개"
fi
SUBJECT="자동 커밋: $(date '+%Y-%m-%d %H:%M') · 파일 ${N}개 ($NAMES)"
BODY="$(git -c core.quotepath=false diff --cached --name-status)"

git commit -q -m "$SUBJECT" -m "$BODY" \
  -m "Claude Code 응답 종료 시 Stop hook(.claude/auto-commit.sh)이 만든 커밋" \
  -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" || exit 0

printf '{"systemMessage": "자동 커밋했어요 (파일 %s개)"}\n' "$N"
exit 0
