# .scripts/smart-backup.ps1

$projectPath = Get-Location
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmm"
$backupDir = ".\_DevOps\backups" 

# 1. GIT SNAPSHOT
Write-Host "Creating Git Snapshot..."
git add .
git commit -m "Auto-backup: Task Completed [$timestamp]"

# 2. LOCAL ZIP BACKUP
if (!(Test-Path $backupDir)) { New-Item -ItemType Directory -Path $backupDir | Out-Null }
$zipName = "$backupDir\Backup_$timestamp.zip"
Write-Host "Zipping to $zipName..."

# Exclude backups folder itself and other heavy/junk folders
$exclude = @("_DevOps", "backups", "bad backups", "local backups", "node_modules", ".git", ".vs", ".vscode")
Get-ChildItem -Path $projectPath -Exclude $exclude | Compress-Archive -DestinationPath $zipName -Force

# 3. UPDATE DIARY
$diaryFile = "$projectPath\_DevOps\behavior\project_diary.md"
if (Test-Path $diaryFile) {
    "  - **Backup Created**: [$timestamp] ($zipName)" | Add-Content $diaryFile
}

Write-Host "Backup Complete."
