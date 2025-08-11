# Quick Install and Setup Script for Break Reminder
# Run this in PowerShell as Administrator if you want system-wide installation

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Break Reminder - Quick Setup" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python first." -ForegroundColor Red
    Write-Host "Download from: https://python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

# Create project directory
$projectDir = "$env:USERPROFILE\BreakReminder"
if (!(Test-Path $projectDir)) {
    New-Item -ItemType Directory -Path $projectDir | Out-Null
    Write-Host "✓ Created project directory: $projectDir" -ForegroundColor Green
}

Set-Location $projectDir

# Download the unified script if not present
$scriptPath = "$projectDir\unified-break-reminder.py"
if (!(Test-Path $scriptPath)) {
    Write-Host "Creating main application file..." -ForegroundColor Yellow
    # Here you would copy the unified-break-reminder.py content
    # For now, we'll assume it's been copied
}

# Install requirements
Write-Host ""
Write-Host "Installing required packages..." -ForegroundColor Yellow
pip install --upgrade pip | Out-Null
pip install pystray pillow plyer pynput pyinstaller | Out-Null
Write-Host "✓ Packages installed" -ForegroundColor Green

# Create icon
Write-Host ""
Write-Host "Creating application icon..." -ForegroundColor Yellow
if (!(Test-Path "$projectDir\break_reminder.ico")) {
    # Create icon using the Python script
    python create-icon-script.py 2>$null
    if ($?) {
        Write-Host "✓ Icon created" -ForegroundColor Green
    } else {
        Write-Host "⚠ Icon creation skipped (optional)" -ForegroundColor Yellow
    }
}

# Build executable
Write-Host ""
Write-Host "Building executable..." -ForegroundColor Yellow
$buildCommand = @"
pyinstaller --onefile --windowed --name "BreakReminder" --icon="break_reminder.ico" --noupx --clean unified-break-reminder.py
"@
Invoke-Expression $buildCommand | Out-Null

if (Test-Path "$projectDir\dist\BreakReminder.exe") {
    Write-Host "✓ Executable built successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Build failed" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit
}

# Create shortcuts
Write-Host ""
Write-Host "Creating shortcuts..." -ForegroundColor Yellow

# Desktop shortcut
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\BreakReminder.lnk")
$Shortcut.TargetPath = "$projectDir\dist\BreakReminder.exe"
$Shortcut.WorkingDirectory = "$projectDir\dist"
$Shortcut.IconLocation = "$projectDir\dist\BreakReminder.exe"
$Shortcut.Save()
Write-Host "✓ Desktop shortcut created" -ForegroundColor Green

# Start Menu shortcut
$startMenuPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
$Shortcut = $WshShell.CreateShortcut("$startMenuPath\BreakReminder.lnk")
$Shortcut.TargetPath = "$projectDir\dist\BreakReminder.exe"
$Shortcut.WorkingDirectory = "$projectDir\dist"
$Shortcut.IconLocation = "$projectDir\dist\BreakReminder.exe"
$Shortcut.Save()
Write-Host "✓ Start Menu shortcut created" -ForegroundColor Green

# Auto-start setup
Write-Host ""
$autostart = Read-Host "Enable auto-start with Windows? (Y/N)"
if ($autostart -eq 'Y' -or $autostart -eq 'y') {
    # Add to registry
    $regPath = "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
    $appName = "BreakReminder"
    $exePath = "$projectDir\dist\BreakReminder.exe --minimized"
    
    try {
        Set-ItemProperty -Path $regPath -Name $appName -Value $exePath
        Write-Host "✓ Auto-start enabled" -ForegroundColor Green
    } catch {
        Write-Host "✗ Failed to enable auto-start" -ForegroundColor Red
    }
}

# Final summary
Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Application installed to:" -ForegroundColor White
Write-Host "  $projectDir\dist\BreakReminder.exe" -ForegroundColor Yellow
Write-Host ""
Write-Host "Shortcuts created:" -ForegroundColor White
Write-Host "  • Desktop" -ForegroundColor Yellow
Write-Host "  • Start Menu" -ForegroundColor Yellow
if ($autostart -eq 'Y' -or $autostart -eq 'y') {
    Write-Host "  • Auto-start enabled" -ForegroundColor Yellow
}
Write-Host ""

# Launch option
$launch = Read-Host "Launch Break Reminder now? (Y/N)"
if ($launch -eq 'Y' -or $launch -eq 'y') {
    Start-Process "$projectDir\dist\BreakReminder.exe"
    Write-Host "✓ Break Reminder started!" -ForegroundColor Green
}

Write-Host ""
Write-Host "Press Enter to exit..." -ForegroundColor Gray
Read-Host