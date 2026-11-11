---
name: git-auto-commit
description: 작업 폴더를 Git 저장소로 준비하고, AI 작업이 끝날 때마다 바뀐 파일을 자동으로 커밋하도록 설정한다. "자동 커밋 설정해줘", "작업 끝나면 커밋되게 해줘", "git 자동 저장", "변경 기록 남겨줘", "자동 커밋 꺼줘" 요청에 사용한다. 한글 파일명과 한글 커밋 메시지가 깨지지 않게 설정하며, 원격 저장소로 push하지 않는다.
---

# Git 자동 커밋

AI가 파일 작업을 마칠 때마다 바뀐 파일을 하나의 커밋으로 남긴다. 실수로 파일을 덮어써도 이전 버전으로 돌아갈 수 있게 하는 것이 목적이다.

사용자에게는 부드러운 존댓말로 짧게 설명한다. 어려운 말은 처음 한 번 풀어 쓴다. 예: 커밋 → 파일 상태를 저장한 기록, 저장소 → 변경 기록을 보관하는 폴더.

## 스킬 구성

이 스킬은 `SKILL.md` 파일 하나로 되어 있다. 필요한 스크립트와 `.gitignore` 기본값은 맨 아래 **부록**에 원문으로 들어 있다. 설정할 때 부록 내용을 작업 폴더에 파일로 저장해서 쓴다.

| 부록 | 저장할 위치 | 용도 |
|---|---|---|
| 부록 A | `<작업폴더>/.claude/auto-commit.sh` | macOS·Linux·Git Bash용 자동 커밋 스크립트 |
| 부록 B | `<작업폴더>/.claude/auto-commit.ps1` | Windows PowerShell용 자동 커밋 스크립트 (동작 동일) |
| 부록 C | `<작업폴더>/.gitignore` | 커밋하지 않을 파일 목록의 기본값 |

두 스크립트가 하는 일:

- 바뀐 파일이 없으면 아무것도 하지 않는다.
- 병합·리베이스 등 다른 Git 작업이 진행 중이면 건너뛴다.
- git 사용자 이름·이메일이 없으면 커밋하지 않고 안내 메시지만 출력한다.
- `.gitignore`에 적힌 파일은 커밋하지 않는다.
- 커밋 제목 예: `자동 커밋: 2026-11-11 16:30 · 파일 4개 (보고서.xlsx, 요약.md, 표.csv 외 1개)`. 본문에는 바뀐 파일 목록이 들어간다.
- 원격 저장소로 push하지 않는다.
- 환경변수 `AUTO_COMMIT_TRAILER`가 있으면 커밋 끝에 그 줄을 붙인다. `AUTO_COMMIT_QUIET=1`이면 성공 메시지를 출력하지 않는다.

## 1. 현재 상태 확인

먼저 무엇을 확인하는지 알린 뒤 실행한다.

1. 실행 환경(Windows·macOS·Linux)과 작업 폴더 경로를 확인한다.
2. `git --version`으로 Git이 있는지 본다. 없으면 설치를 안내하고 멈춘다. 설치 창이나 비밀번호 입력은 사용자가 직접 하도록 클릭 순서를 알려준다.
3. `git rev-parse --is-inside-work-tree`로 이미 저장소인지 본다.
4. 상위 폴더가 저장소이면(`git rev-parse --show-toplevel`이 작업 폴더와 다르면) 그 사실을 알리고, 상위 저장소를 그대로 쓸지 사용자에게 묻는다.

## 2. 저장소 준비 (처음 한 번)

이미 저장소이고 설정이 되어 있으면 건너뛴다.

1. `git init`
2. 사용자 이름·이메일 확인: `git config user.name`, `git config user.email`. 비어 있으면 사용자에게 어떤 이름·이메일을 쓸지 묻고 **이 저장소에만**(`--global` 없이) 설정한다. 이메일을 임의로 지어내지 않는다.
3. 한글 처리 설정 (이 저장소에만):
   ```
   git config core.quotepath false
   git config i18n.commitEncoding utf-8
   git config i18n.logOutputEncoding utf-8
   ```
   macOS에서는 `git config core.precomposeunicode true`도 추가한다. 한글 파일명이 자음·모음으로 나뉘어 저장되는 문제를 막는다.
4. `.gitignore`가 없으면 부록 C 내용으로 만든다. 있으면 기존 내용을 지우지 말고 빠진 줄만 추가한다.
5. 커밋하기 전에 `git status --porcelain`으로 올라갈 파일을 확인한다. `.env`, 비밀번호·API 키가 든 파일, 매우 큰 파일(수십 MB 이상)이 보이면 사용자에게 알리고 `.gitignore`에 넣을지 묻는다.
6. 첫 커밋: `git add -A` 후 `git commit -m "작업 폴더 첫 기록"`. 커밋된 파일 개수를 알려준다.

## 3. 자동 커밋 연결

부록의 스크립트를 **한 글자도 바꾸지 말고** 작업 폴더 안 고정 위치에 파일로 저장한다. 운영체제에 맞는 것 하나만 저장해도 된다.

- macOS·Linux·Git Bash: 부록 A → `<작업폴더>/.claude/auto-commit.sh`, 저장 후 `chmod +x`
- Windows PowerShell: 부록 B → `<작업폴더>/.claude/auto-commit.ps1`. Windows PowerShell 5.1이 한글을 읽을 수 있게 **UTF-8(BOM 포함)**으로 저장한다.

그다음 실행 환경에 맞는 방법 하나를 고른다.

### A. Claude Code처럼 hook(정해진 순간에 자동 실행되는 명령) 기능이 있는 환경

`<작업폴더>/.claude/settings.json`을 **먼저 읽고**, 기존 내용은 그대로 둔 채 `hooks.Stop` 항목만 추가한다. 이미 같은 명령이 있으면 다시 넣지 않는다.

macOS·Linux:
```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/auto-commit.sh 2>/dev/null || true",
            "timeout": 30,
            "statusMessage": "바뀐 파일 자동 커밋 중"
          }
        ]
      }
    ]
  }
}
```

Windows: `command`를 `powershell -NoProfile -ExecutionPolicy Bypass -File \"%CLAUDE_PROJECT_DIR%\\.claude\\auto-commit.ps1\"`로 바꾼다. Git Bash가 기본 셸이면 macOS용 명령을 그대로 써도 된다.

수정 후 JSON 문법을 검사한다(`jq . settings.json` 또는 `python -m json.tool settings.json`). 문법이 틀리면 설정 파일 전체가 무시된다. 설정 감시가 새 hook을 못 읽을 수 있으므로 "적용이 안 되면 세션을 새로 열어주세요"라고 안내한다.

### B. hook 기능이 없는 환경 (에이닷 비즈 등 다른 에이전트 플랫폼)

이 스킬이 켜져 있는 동안 **파일을 만들거나 고친 작업을 마칠 때마다, 마지막 응답을 보내기 직전에** 스크립트를 직접 실행한다.

- macOS·Linux·Git Bash: `sh .claude/auto-commit.sh "<작업폴더>"`
- Windows: `powershell -NoProfile -ExecutionPolicy Bypass -File .claude\auto-commit.ps1 -Dir "<작업폴더>"`

출력에 `자동 커밋했어요`가 있으면 응답 끝에 "변경 파일 N개를 자동 커밋했어요" 한 줄을 덧붙인다. 출력이 없으면 바뀐 파일이 없다는 뜻이므로 언급하지 않는다. 파일을 읽기만 한 대화에서는 실행하지 않아도 된다.

플랫폼이 명령 실행 자체를 지원하지 않으면, 자동 커밋이 불가능하다고 알리고 사용자가 직접 실행할 명령 한 줄을 안내한다.

## 4. 동작 확인

실제 저장소에 시험 기록을 남기지 않는다. 임시 폴더에 저장소를 만들어 시험하고, 끝나면 지운다.

1. 바뀐 파일이 없을 때 실행 → 커밋이 생기지 않아야 한다.
2. 한글 이름 파일 2개를 만들고 실행 → 커밋 1개가 생기고 `git log --stat`에 한글 파일명이 정상으로 보여야 한다.
3. `~$임시.xlsx`를 만들고 실행 → 커밋되지 않아야 한다.

결과를 사용자에게 한 줄씩 알린다.

## 5. 완료 안내

다음 내용을 짧게 알린다.

- 언제 실행되는지 (AI 응답이 끝날 때, 바뀐 파일이 있을 때만)
- 커밋 메시지 형식
- 제외되는 파일 (`.gitignore`)
- push는 하지 않는다는 점
- 기록 보는 법: `git log --oneline`
- 이전 버전 되돌리기는 요청하면 도와준다는 점 (사용자 확인 없이 `git reset --hard` 같은 되돌릴 수 없는 명령을 실행하지 않는다)
- 끄는 법

## 끄기 요청 ("자동 커밋 꺼줘")

- A 방식: `.claude/settings.json`에서 auto-commit 명령이 든 `Stop` 항목만 지운다. 다른 hook은 건드리지 않는다. JSON 문법을 다시 검사한다.
- B 방식: 이후 작업 종료 시 스크립트를 실행하지 않는다. 스킬을 계속 켜둘 경우를 대비해 사용자가 다시 켜달라고 할 때까지 실행하지 않는다고 알린다.
- 스크립트 파일과 지금까지의 커밋 기록은 지우지 않는다. 지우기를 원하면 따로 확인을 받는다.

## 하지 않는 일

- `git push`, 원격 저장소 추가, `--global` 설정 변경을 사용자 요청 없이 하지 않는다.
- 비밀값이 든 파일을 커밋하지 않는다.
- 사용자 이름·이메일을 추측해서 넣지 않는다.

## 부록 A. auto-commit.sh

```sh
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
```

## 부록 B. auto-commit.ps1

```powershell
# 작업 폴더에서 바뀐 파일을 한 번에 자동 커밋한다 (Windows PowerShell용).
# 사용: powershell -NoProfile -ExecutionPolicy Bypass -File auto-commit.ps1 [-Dir 폴더]
# 동작은 auto-commit.sh와 같다. push하지 않는다.
param([string]$Dir = $(if ($env:CLAUDE_PROJECT_DIR) { $env:CLAUDE_PROJECT_DIR } else { (Get-Location).Path }))
$ErrorActionPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
if (-not (Test-Path -LiteralPath $Dir)) { exit 0 }
Set-Location -LiteralPath $Dir
if ((git rev-parse --is-inside-work-tree 2>$null) -ne 'true') { exit 0 }

$gitDir = git rev-parse --git-dir
foreach ($p in 'MERGE_HEAD','rebase-merge','rebase-apply','index.lock') {
  if (Test-Path -LiteralPath (Join-Path $gitDir $p)) { exit 0 }
}
if (-not (git status --porcelain)) { exit 0 }
if (-not (git config user.name) -or -not (git config user.email)) {
  Write-Output '{"systemMessage": "자동 커밋을 건너뛰었어요: git 사용자 이름·이메일이 설정되지 않았어요"}'
  exit 0
}

git add -A
$files = @(git -c core.quotepath=false diff --cached --name-only)
$n = $files.Count
if ($n -eq 0) { exit 0 }
$names = ($files | Select-Object -First 3 | ForEach-Object { Split-Path $_ -Leaf }) -join ', '
if ($n -gt 3) { $names = "$names 외 $($n - 3)개" }
$subject = "자동 커밋: $(Get-Date -Format 'yyyy-MM-dd HH:mm') · 파일 ${n}개 ($names)"
$body = (git -c core.quotepath=false diff --cached --name-status) -join "`n"
$note = 'AI 작업이 끝날 때 git-auto-commit 스킬이 만든 커밋'

$gitArgs = @('-c','i18n.commitEncoding=utf-8','commit','-q','-m',$subject,'-m',$body,'-m',$note)
if ($env:AUTO_COMMIT_TRAILER) { $gitArgs += @('-m', $env:AUTO_COMMIT_TRAILER) }
git @args
if ($LASTEXITCODE -ne 0) { exit 0 }
if ($env:AUTO_COMMIT_QUIET -ne '1') { Write-Output "{`"systemMessage`": `"자동 커밋했어요 (파일 ${n}개)`"}" }
exit 0
```

## 부록 C. .gitignore 기본값

```gitignore
# 이 폴더 전용 Python 공간
.venv/
__pycache__/

# macOS·Windows 폴더 설정 파일
.DS_Store
Thumbs.db

# Office 파일을 열어 둘 때 생기는 임시 잠금 파일
~$*

# API 키 등 비밀값 (절대 커밋하지 않음)
.env
.env.*
!.env.example
```
