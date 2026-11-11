#!/bin/sh
# 작업 폴더에서 바뀐 파일을 한 번에 자동 커밋한다.
# 사용: sh auto-commit.sh [폴더]   (폴더를 안 주면 CLAUDE_PROJECT_DIR → 현재 폴더 순)
# - 바뀐 파일이 없으면 아무것도 하지 않는다.
# - 병합·리베이스 중이거나 다른 Git 작업이 진행 중이면 건너뛴다.
# - .gitignore에 있는 파일은 커밋하지 않는다.
# - 원격 저장소로 push하지 않는다.
# 선택 환경변수: AUTO_COMMIT_TRAILER  커밋 끝에 붙일 줄 (예: "Co-Authored-By: ...")
#               AUTO_COMMIT_QUIET=1  성공 메시지를 출력하지 않음
DIR="${1:-${CLAUDE_PROJECT_DIR:-$(pwd)}}"
cd "$DIR" 2>/dev/null || exit 0
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

GITDIR="$(git rev-parse --git-dir)"
if [ -e "$GITDIR/MERGE_HEAD" ] || [ -d "$GITDIR/rebase-merge" ] || \
   [ -d "$GITDIR/rebase-apply" ] || [ -e "$GITDIR/index.lock" ]; then
  exit 0
fi

[ -z "$(git status --porcelain)" ] && exit 0

if [ -z "$(git config user.name)" ] || [ -z "$(git config user.email)" ]; then
  printf '{"systemMessage": "자동 커밋을 건너뛰었어요: git 사용자 이름·이메일이 설정되지 않았어요"}\n'
  exit 0
fi

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
NOTE="AI 작업이 끝날 때 git-auto-commit 스킬이 만든 커밋"

if [ -n "$AUTO_COMMIT_TRAILER" ]; then
  git commit -q -m "$SUBJECT" -m "$BODY" -m "$NOTE" -m "$AUTO_COMMIT_TRAILER" || exit 0
else
  git commit -q -m "$SUBJECT" -m "$BODY" -m "$NOTE" || exit 0
fi

[ "$AUTO_COMMIT_QUIET" = "1" ] || printf '{"systemMessage": "자동 커밋했어요 (파일 %s개)"}\n' "$N"
exit 0
