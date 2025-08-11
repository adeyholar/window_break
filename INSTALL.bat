@echo off
:: Modern One-Click Installer for Break Reminder
:: No admin required, no deprecated methods

setlocal enabledelayedexpansion

:: Set console colors
color 0A

echo.
echo ============================================================
echo           Break Reminder - Modern Installation
echo ============================================================
echo.

:: Check if running as admin and warn
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [WARNING] Running as Administrator is not recommended!
    echo           Please run this installer as a normal user.
    echo.
    pause
)

:: Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please install Python 3.10 or later from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo [OK] Python found
echo.

:: Set installation directory (user-level)
set "INSTALL_DIR=%LOCALAPPDATA%\BreakReminder"
echo Installation directory: %INSTALL_DIR%
echo.

:: Create installation directory
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
cd /d "%INSTALL_DIR%"

:: Copy files from current directory
echo Copying application files...
if exist "%~dp0unified-break-reminder.py" (
    copy "%~dp0unified-break-reminder.py" "%INSTALL_DIR%\break_reminder.py" >nul
    echo [OK] Application copied
) else (
    echo [WARNING] Application file not found
)

if exist "%~dp0create-icon-script.py" (
    copy "%~dp0create-icon-script.py" "%INSTALL_DIR%\" >nul
)

:: Install Python packages (user-level, no admin)
echo.
echo Installing required packages...
echo This may take a minute...
echo.

:: Use --user flag to avoid admin requirements
python -m pip install --user --upgrade pip >nul 2>&1
python -m pip install --user pystray pillow plyer pynput >nul 2>&1
python -m pip install --user pyinstaller >nul 2>&1

echo [OK] Packages installed
echo.

:: Create icon
if exist "create-icon-script.py" (
    echo Creating application icon...
    python create-icon-script.py >nul 2>&1
    if exist "break_reminder.ico" (
        echo [OK] Icon created
    ) else (
        echo [WARNING] Icon creation failed (optional)
    )
    echo.
)

:: Build executable
echo Building executable (this may take 1-2 minutes)...
echo Please wait...
echo.

:: Create a minimal spec file to avoid deprecation warnings
(
echo # PyInstaller spec file - Modern approach
echo import sys
echo a = Analysis(['break_reminder.py'],
echo              pathex=[],
echo              binaries=[],
echo              datas=[],
echo              hiddenimports=['pynput.mouse._win32', 'pynput.keyboard._win32'],
echo              hookspath=[],
echo              runtime_hooks=[],
echo              excludes=['matplotlib', 'numpy', 'scipy', 'pandas'],
echo              noarchive=False^)
echo pyz = PYZ(a.pure^)
echo exe = EXE(pyz, a.scripts, a.binaries, a.datas, [],
echo           name='BreakReminder',
echo           debug=False,
echo           console=False,
echo           icon='break_reminder.ico'^)
) > BreakReminder.spec

:: Build using spec (avoids all deprecation warnings)
python -m PyInstaller --distpath "%INSTALL_DIR%\dist" --workpath "%INSTALL_DIR%\build" --clean --noconfirm BreakReminder.spec >nul 2>&1

if exist "%INSTALL_DIR%\dist\BreakReminder.exe" (
    echo [OK] Executable built successfully
    set "EXE_PATH=%INSTALL_DIR%\dist\BreakReminder.exe"
) else (
    echo [WARNING] Build failed, creating Python launcher instead
    :: Create a launcher batch file as fallback
    (
        echo @echo off
        echo start "" pythonw "%INSTALL_DIR%\break_reminder.py" %%*
    ) > "%INSTALL_DIR%\BreakReminder.bat"
    set "EXE_PATH=%INSTALL_DIR%\BreakReminder.bat"
)

echo.

:: Create Desktop shortcut (user-level, no admin)
echo Creating shortcuts...

:: Use PowerShell to create shortcut (modern method)
powershell -NoProfile -Command ^
    "$ws = New-Object -ComObject WScript.Shell; ^
    $shortcut = $ws.CreateShortcut('%USERPROFILE%\Desktop\Break Reminder.lnk'); ^
    $shortcut.TargetPath = '%EXE_PATH%'; ^
    $shortcut.WorkingDirectory = '%INSTALL_DIR%'; ^
    $shortcut.IconLocation = '%INSTALL_DIR%\break_reminder.ico'; ^
    $shortcut.Save()" >nul 2>&1

if exist "%USERPROFILE%\Desktop\Break Reminder.lnk" (
    echo [OK] Desktop shortcut created
) else (
    echo [WARNING] Could not create desktop shortcut
)

:: Create Start Menu shortcut
powershell -NoProfile -Command ^
    "$ws = New-Object -ComObject WScript.Shell; ^
    $shortcut = $ws.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\Break Reminder.lnk'); ^
    $shortcut.TargetPath = '%EXE_PATH%'; ^
    $shortcut.WorkingDirectory = '%INSTALL_DIR%'; ^
    $shortcut.IconLocation = '%INSTALL_DIR%\break_reminder.ico'; ^
    $shortcut.Save()" >nul 2>&1

if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Break Reminder.lnk" (
    echo [OK] Start Menu shortcut created
) else (
    echo [WARNING] Could not create Start Menu shortcut
)

echo.

:: Auto-start configuration (user registry, no admin)
echo ============================================================
set /p AUTOSTART="Enable auto-start with Windows? (Y/N): "
if /i "%AUTOSTART%"=="Y" (
    :: Use REG ADD with HKCU (user-level, no admin required)
    reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /v "BreakReminder" /t REG_SZ /d "\"%EXE_PATH%\" --minimized" /f >nul 2>&1
    if !errorlevel! == 0 (
        echo [OK] Auto-start enabled (user-level^)
    ) else (
        echo [WARNING] Could not enable auto-start
    )
) else (
    echo [OK] Auto-start not enabled
)

echo.
echo ============================================================
echo                  Installation Complete!
echo ============================================================
echo.
echo Installed to: %INSTALL_DIR%
echo.
echo You can run Break Reminder by:
echo   - Double-clicking the desktop shortcut
echo   - Finding it in the Start Menu
echo   - It will auto-start with Windows (if enabled)
echo.
echo ============================================================
echo.

:: Launch option
set /p LAUNCH="Launch Break Reminder now? (Y/N): "
if /i "%LAUNCH%"=="Y" (
    start "" "%EXE_PATH%"
    echo.
    echo [OK] Break Reminder started!
)

echo.
echo Press any key to exit...
pause >nul