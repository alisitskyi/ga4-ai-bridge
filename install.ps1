# Windows Installer for ga4-ai-bridge
param(
    [string]$CredentialsPath = ""
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Installing ga4-ai-bridge (Windows)      " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Check Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[ERROR] Python is not installed or not in PATH." -ForegroundColor Red
    exit 1
}
Write-Host "[+] Found Python: $($pythonCmd.Source)" -ForegroundColor Green

# 2. Install dependencies
Write-Host "[*] Installing dependencies..." -ForegroundColor Yellow
python -m pip install -r "$PSScriptRoot\requirements.txt" --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to install dependencies." -ForegroundColor Red
    exit 1
}
Write-Host "[+] Dependencies installed successfully." -ForegroundColor Green

# 3. Create ~/.ga4 directory
$ga4Home = "$HOME\.ga4"
$ga4Bin = "$ga4Home\bin"
New-Item -ItemType Directory -Path $ga4Home -Force | Out-Null
New-Item -ItemType Directory -Path $ga4Bin -Force | Out-Null

Copy-Item "$PSScriptRoot\src\ga4_ai\cli.py" -Destination "$ga4Home\ga4_tool.py" -Force

# Create wrappers
"@echo off`r`npython `"$ga4Home\ga4_tool.py`" %*" | Set-Content "$ga4Bin\ga4.cmd" -Force
"& python `"$ga4Home\ga4_tool.py`" `$args" | Set-Content "$ga4Bin\ga4.ps1" -Force

# 4. Handle credentials
if ($CredentialsPath -and (Test-Path $CredentialsPath)) {
    Copy-Item $CredentialsPath -Destination "$ga4Home\credentials.json" -Force
    Write-Host "[+] Copied credentials from $CredentialsPath" -ForegroundColor Green
} elseif (Test-Path "$HOME\.gdoc\credentials.json") {
    Copy-Item "$HOME\.gdoc\credentials.json" -Destination "$ga4Home\credentials.json" -Force
    Write-Host "[+] Reused existing credentials from ~/.gdoc" -ForegroundColor Green
}

# 5. Add to User PATH
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -notlike "*$ga4Bin*") {
    $newUserPath = $userPath.TrimEnd(';') + ";$ga4Bin"
    [Environment]::SetEnvironmentVariable("PATH", $newUserPath, "User")
    Write-Host "[+] Added $ga4Bin to permanent User PATH." -ForegroundColor Green
} else {
    Write-Host "[+] $ga4Bin is already in User PATH." -ForegroundColor Green
}

$env:PATH = "$env:PATH;$ga4Bin"

Write-Host "`n[+] Installation complete!" -ForegroundColor Cyan
Write-Host "Next steps:" -ForegroundColor White
Write-Host "1. Enable Google Analytics Data API in Google Cloud Console"
Write-Host "2. In a new terminal, run: ga4 auth"
Write-Host "3. List your properties with: ga4 properties"
