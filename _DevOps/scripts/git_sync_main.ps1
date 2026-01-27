$ErrorActionPreference = "Stop"

# --- Configuration ---
$Branch = "main"
$FilesToSync = @("RouteManager.py", "modules", "static", "Templates", "Scripts", "DATA", "_DevOps/package.json", "_DevOps/behavior", "_DevOps/docs", "_DevOps/scripts", ".cursorrules")
$CommitMsg = "Auto-Sync Source [$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')]"

# --- Execution ---
Write-Host ">>> Starting Source Sync to '$Branch'..." -ForegroundColor Cyan

# 1. Check Git Status
if (-not (Test-Path .git)) {
    Write-Error "Not a git repository."
}

# 2. Switch to Main
$currentBranch = git branch --show-current
if ($currentBranch -ne $Branch) {
    Write-Host "Switching to branch '$Branch'..."
    git checkout $Branch 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Branch '$Branch' not found. Creating it..."
        git checkout -b $Branch
    }
}

# 3. Clean Stage
git reset
# We do NOT want to delete untracked files in main via clean, because _DevOps and others are here.
# Just ensuring index is fresh.

# 4. Force Add Specific Files
foreach ($item in $FilesToSync) {
    if (Test-Path $item) {
        Write-Host "Adding $item..."
        git add -f $item
    } else {
        Write-Warning "Item '$item' not found. Skipping."
    }
}

# 5. Commit
$status = git status --porcelain
if ($status) {
    Write-Host "Committing changes..."
    git commit -m "$CommitMsg"
} else {
    Write-Host "No changes to commit." -ForegroundColor Yellow
}

# 6. Push
Write-Host "Pushing to origin/$Branch..."
git push origin $Branch -f

Write-Host ">>> Source Sync Complete!" -ForegroundColor Green
