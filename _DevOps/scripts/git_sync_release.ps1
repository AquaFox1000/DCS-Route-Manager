$ErrorActionPreference = "Stop"

# --- Configuration ---
$ReleaseBranch = "release"
$DcsHooksPath = "C:\Users\pino4\Saved Games\DCS.openbeta\Scripts\Hooks"
$BuildDir = "build"
$DistDir = "dist"
$StageDir = "_release_stage"
$CommitMsg = "Auto-Release [$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')]"

# --- Execution ---
Write-Host ">>> Starting Release Build & Sync..." -ForegroundColor Cyan

# 1. Build Executable
Write-Host "Building EXE with PyInstaller..."
# Ensure clean build
if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
if (Test-Path $DistDir) { Remove-Item -Recurse -Force $DistDir }

# Run PyInstaller (Assuming pyinstaller is in path, or use python -m)
pyinstaller --noconfirm --onedir --windowed --icon "static/icon.ico" --name "RouteManager" --add-data "templates;templates" --add-data "static;static" "RouteManager.py"

if (-not (Test-Path "$DistDir\RouteManager\RouteManager.exe")) {
    Write-Error "Build Failed! RouteManager.exe not found."
}

# 2. Prepare Staging Area
Write-Host "Preparing Staging Area ('$StageDir')..."
if (Test-Path $StageDir) { Remove-Item -Recurse -Force $StageDir }
New-Item -ItemType Directory -Path "$StageDir" | Out-Null
New-Item -ItemType Directory -Path "$StageDir\Scripts\Hooks" | Out-Null
New-Item -ItemType Directory -Path "$StageDir\Mods\tech\RouteManager\bin" | Out-Null
New-Item -ItemType Directory -Path "$StageDir\Mods\tech\RouteManager\data" | Out-Null
New-Item -ItemType Directory -Path "$StageDir\Mods\tech\RouteManager\static" | Out-Null
New-Item -ItemType Directory -Path "$StageDir\Mods\tech\RouteManager\Templates" | Out-Null

# 3. Copy Assets
Write-Host "Copying Files..."

# A. Hook Script (From DCS Saved Games - "Source of Truth" for the hook)
$LocalHook = "$DcsHooksPath\RouteManagerHook.lua"
if (Test-Path $LocalHook) {
    Copy-Item $LocalHook "$StageDir\Scripts\Hooks\"
    Write-Host "Fetched latest hook from DCS Saved Games."
} else {
    Write-Error "DCS Hook not found at $LocalHook"
}

# B. Binaries (The PyInstaller Output)
Copy-Item "$DistDir\RouteManager\*" "$StageDir\Mods\tech\RouteManager\bin\" -Recurse

# C. Mod Assets (DATA, Static, Templates - needed for structure/defaults)
Copy-Item "DATA\*" "$StageDir\Mods\tech\RouteManager\data\" -Recurse
Copy-Item "static\*" "$StageDir\Mods\tech\RouteManager\static\" -Recurse
Copy-Item "Templates\*" "$StageDir\Mods\tech\RouteManager\Templates\" -Recurse

# D. Copy entry.lua if it exists (Optional, if it's a tech mod)
# For now, assuming standalone exe + hook, but structure implies tech mod.
# If you have an entry.lua for the Mod Manager, copy it here.
# Copy-Item "Mods\tech\RouteManager\entry.lua" "$StageDir\Mods\tech\RouteManager\"

# 4. Git Release Push
Write-Host "Publishing to Git Branch '$ReleaseBranch'..."

# Stash current changes to avoid losing work
git stash push -m "Pre-Release Stash"

# Switch to Orphan Branch (Fresh Start)
git checkout --orphan $ReleaseBranch
git reset --hard # Clear index

# Delete everything in root except .git (CAREFUL!)
# We MUST preserve _DevOps, .agent, and local configs because they are not tracked but we need them!
$Preserve = @(".git", "$StageDir", "_DevOps", ".agent", ".cursorrules", "task.md", "walkthrough.md", "implementation_plan.md")
Get-ChildItem -Path . -Exclude $Preserve | Remove-Item -Recurse -Force

# Move Stage Content to Root
Get-ChildItem -Path "$StageDir\*" | Move-Item -Destination . -Force
Remove-Item $StageDir -Recurse -Force

# Add and Commit
git add .
git commit -m "$CommitMsg"
git push origin $ReleaseBranch -f

# 5. Restore Main
Write-Host "Switching back to main..."
git checkout main
# Popping stash might conflict if main changed, but usually safe if we just switched.
# git stash pop 

Write-Host ">>> Release Published Successfully!" -ForegroundColor Green
