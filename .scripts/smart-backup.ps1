# .scripts/smart-backup.ps1

$projectPath = Get-Location
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmm"
$backupDir = ".\backups" 

# 1. GIT SNAPSHOT
Write-Host "Creating Git Snapshot..."
git add .
git commit -m "Auto-backup: Task Completed [$timestamp]"

# 2. LOCAL ZIP BACKUP
if (!(Test-Path $backupDir)) { New-Item -ItemType Directory -Path $backupDir | Out-Null }
$zipName = "$backupDir\Backup_$timestamp.zip"
Write-Host "Zipping to $zipName..."
Compress-Archive -Path "$projectPath\*" -DestinationPath $zipName -Force

Write-Host "Backup Complete."
