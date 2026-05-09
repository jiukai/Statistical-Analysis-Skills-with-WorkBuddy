# PowerShell Script: Create GitHub Repository and Upload Skills
# 时间序列分析技能包 GitHub 发布脚本

param(
    [Parameter(Mandatory=$true)]
    [string]$Token,
    
    [Parameter(Mandatory=$false)]
    [string]$RepoName = "Statistical-Analysis-Skills-with-WorkBuddy",
    
    [Parameter(Mandatory=$false)]
    [string]$UserName = "jiukai89"
)

$Description = "WorkBuddy AI Skills for Stata-run, python-run, and Time Series Analysis - 面向经管科研的统计软件AI教育智能体技能包"

Write-Host "=== Creating GitHub Repository ===" -ForegroundColor Cyan

# Step 1: Create repo
$headers = @{
    "Authorization" = "token $Token"
    "Accept" = "application/vnd.github.v3+json"
}

$body = @{
    name = $RepoName
    description = $Description
    private = $false
    auto_init = $true
    has_issues = $true
    has_wiki = $true
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "https://api.github.com/user/repos" -Method Post -Headers $headers -Body $body -ContentType "application/json"
    Write-Host "[OK] Repository created: https://github.com/$UserName/$RepoName" -ForegroundColor Green
}
catch {
    if ($_.Exception.Response.StatusCode -eq 422) {
        Write-Host "[!] Repository already exists, proceeding with upload..." -ForegroundColor Yellow
    }
    else {
        Write-Host "[ERROR] $_" -ForegroundColor Red
        exit 1
    }
}

# Step 2: Upload files via Git (requires git installed)
$scriptPath = Split-Path -Parent $PSCommandPath
$repoDir = Join-Path $scriptPath "repo_local"

if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Host "Git found, cloning and uploading..." -ForegroundColor Cyan
    
    # Clone the repo
    $cloneUrl = "https://$UserName`:$Token@github.com/$UserName/$RepoName.git"
    git clone $cloneUrl $repoDir 2>&1 | Out-Null
    
    if (Test-Path $repoDir) {
        # Copy all skill files
        Copy-Item -Path (Join-Path $scriptPath "Stata-run") -Destination $repoDir -Recurse -Force
        Copy-Item -Path (Join-Path $scriptPath "python-run") -Destination $repoDir -Recurse -Force
        Copy-Item -Path (Join-Path $scriptPath "时间序列分析") -Destination $repoDir -Recurse -Force
        Copy-Item -Path (Join-Path $scriptPath "README.md") -Destination $repoDir -Force
        Copy-Item -Path (Join-Path $scriptPath "LICENSE") -Destination $repoDir -Force
        
        # Commit and push
        Push-Location $repoDir
        git add -A 2>&1 | Out-Null
        git -c user.name="$UserName" -c user.email="jiukai89@163.com" commit -m "Initial release: Stata-run, python-run, 时间序列分析 skills" 2>&1 | Out-Null
        git push 2>&1 | Out-Null
        Pop-Location
        
        Write-Host "[OK] All files uploaded to GitHub!" -ForegroundColor Green
        Remove-Item -Path $repoDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
else {
    Write-Host "[!] Git not found. Please upload files manually." -ForegroundColor Yellow
    Write-Host "    1. Go to: https://github.com/$UserName/$RepoName" -ForegroundColor Yellow
    Write-Host "    2. Click 'Add file' -> 'Upload files'" -ForegroundColor Yellow
    Write-Host "    3. Drag and drop these folders: Stata-run/, python-run/, 时间序列分析/" -ForegroundColor Yellow
    Write-Host "    4. Also upload: README.md, LICENSE" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Done! ===" -ForegroundColor Cyan
Write-Host "Repo URL: https://github.com/$UserName/$RepoName"
