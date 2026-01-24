# build_release.ps1

Write-Host "Starting Release Build..." -ForegroundColor Green

# Define Python Path
$PYTHON = "C:/Users/pino4/AppData/Local/Programs/Python/Python313/python.exe"

if (-not (Test-Path $PYTHON)) {
    Write-Error "Python executable not found at $PYTHON"
    exit 1
}

# 1. Install Requirements
Write-Host "Installing/Verifying PyInstaller..."
& $PYTHON -m pip install pyinstaller

# 2. Cleanup
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "_release") { Remove-Item -Recurse -Force "_release" }

# 3. Build Executable
Write-Host "Building RouteManager..."

# Use python -m PyInstaller to avoid PATH issues
# --console shows the terminal window (DEBUG MODE)
& $PYTHON -m PyInstaller --noconfirm --onedir --console --name "RouteManager" `
    --add-data "Templates;Templates" `
    --add-data "static;static" `
    --hidden-import "engineio.async_drivers.threading" `
    --hidden-import "engineio.async_drivers.gevent" `
    RouteManager.py

if (-not (Test-Path "dist\RouteManager\RouteManager.exe")) {
    Write-Error "Build Failed! Exe not found."
    exit 1
}

# 4. Create Directory Structure
Write-Host "Organizing Release Folder..."
$releaseDir = "_release"
$modsDir = "$releaseDir\Mods\tech\RouteManager"
$scriptsDir = "$releaseDir\Scripts"

New-Item -ItemType Directory -Force -Path $modsDir | Out-Null
New-Item -ItemType Directory -Force -Path $scriptsDir | Out-Null

# Move Build Artifacts into Mods/tech/RouteManager
# We move the *contents* of dist/RouteManager into the target folder
Copy-Item -Recurse -Force "dist\RouteManager\*" $modsDir

# Copy Scripts (Hooks)
if (Test-Path "Scripts") {
    Copy-Item -Recurse -Force "Scripts\*" $scriptsDir
} else {
    Write-Warning "Scripts folder not found in root!"
}

Write-Host "Build Complete!" -ForegroundColor Green
Write-Host "Release available at: $(Resolve-Path $releaseDir)"
