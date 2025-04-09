# Script to delete all files and directories that match .gitignore patterns

$projectRoot = "c:\Users\erraz\repos VS\T7_Praktika"
Set-Location $projectRoot

# Key directories to clean (from your .gitignore)
$directoriesToDelete = @(
    "__pycache__",
    "node_modules",
    ".svelte-kit",
    "build",
    "dist",
    "venv",
    "env",
    "ENV",
    ".venv",
    ".hypothesis",
    ".pytest_cache",
    ".tox",
    ".nox",
    "instance",
    ".flask_session",
    ".vscode",
    ".idea",
    ".ipynb_checkpoints",
    "public/build",
    ".output",
    ".vercel",
    ".netlify"
)

# Files to clean (common patterns)
$filePatterns = @(
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.so",
    "*.egg",
    "*.egg-info",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "*.code-workspace",
    "*.log",
    "*.sqlite",
    "*.sqlite3",
    "*.db",
    ".DS_Store",
    "Thumbs.db",
    "ehthumbs.db",
    ".env",
    ".env.*"
)

# Remove directories
Write-Host "Removing directories..." -ForegroundColor Yellow
foreach ($dir in $directoriesToDelete) {
    $dirsToRemove = Get-ChildItem -Path $projectRoot -Directory -Recurse -Force | 
                    Where-Object { $_.Name -eq $dir } |
                    Select-Object -ExpandProperty FullName
    
    foreach ($dirToRemove in $dirsToRemove) {
        Write-Host "  Removing: $dirToRemove" -ForegroundColor Cyan
        Remove-Item -Path $dirToRemove -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# Remove files
Write-Host "Removing files..." -ForegroundColor Yellow
foreach ($pattern in $filePatterns) {
    $filesToRemove = Get-ChildItem -Path $projectRoot -File -Recurse -Force -Include $pattern |
                     Select-Object -ExpandProperty FullName
    
    foreach ($fileToRemove in $filesToRemove) {
        Write-Host "  Removing: $fileToRemove" -ForegroundColor Cyan
        Remove-Item -Path $fileToRemove -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Clean-up complete!" -ForegroundColor Green
Write-Host "Note: This script only removes common ignored files and directories." -ForegroundColor Yellow
