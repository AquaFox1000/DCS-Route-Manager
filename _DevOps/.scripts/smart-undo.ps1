# .scripts/smart-undo.ps1
Write-Host "WARNING: This will RESET the project to the last commit."
Write-Host "Any uncommitted changes will be LOST."
$confirmation = Read-Host "Type 'UNDO' to confirm"

if ($confirmation -eq 'UNDO') {
    Write-Host "Resetting to HEAD..."
    git reset --hard HEAD
    Write-Host "Undo Complete. Project state reverted to last commit."
} else {
    Write-Host "Undo Cancelled."
}
