# Workaround for "Rename HEAD.lock to HEAD failed" on Windows (e.g. when Cursor or OneDrive locks .git).
# Usage: .\scripts\git-switch-branch.ps1 <branch-name>
# Example: .\scripts\git-switch-branch.ps1 ui-update

param([Parameter(Mandatory=$true)][string]$Branch)

$repoRoot = (Get-Item $PSScriptRoot).Parent.FullName
$gitDir = Join-Path $repoRoot ".git"
$headPath = Join-Path $gitDir "HEAD"
$lockPath = Join-Path $gitDir "HEAD.lock"

Set-Location $repoRoot

# Remove stale lock so normal git commands can run later if they retry
if (Test-Path $lockPath) {
    Remove-Item $lockPath -Force
    Write-Host "Removed stale .git/HEAD.lock"
}

# Ensure branch exists (local or create from remote)
$branchRef = "refs/heads/$Branch"
$refPath = Join-Path $gitDir $branchRef
if (-not (Test-Path $refPath)) {
    # Try to create from remote
    $null = git show-ref --verify "refs/remotes/origin/$Branch" 2>$null
    if ($LASTEXITCODE -eq 0) {
        git branch $Branch "origin/$Branch" 2>$null
    }
    if (-not (Test-Path $refPath)) {
        Write-Error "Branch '$Branch' not found. Run: git branch -a"
        exit 1
    }
}

# Point HEAD at the branch (avoids lock/rename that fails on this machine).
# If you get "file is being used by another process", run this script from a terminal
# outside Cursor (e.g. Start -> PowerShell, cd to repo, then run this script).
Set-Content -Path $headPath -Value "ref: $branchRef" -NoNewline
# Sync index and working tree to the new branch
git read-tree --reset -u HEAD
if ($LASTEXITCODE -ne 0) {
    Write-Error "git read-tree failed"
    exit 1
}

Write-Host "Switched to branch '$Branch'."
git status -sb
