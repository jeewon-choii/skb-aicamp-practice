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
