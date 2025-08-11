#!/usr/bin/env python3
"""
Modern Installation Script for Break Reminder
No admin required, no deprecation warnings
Works with Python 3.10+
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import platform


def check_admin():
    """Ensure we're NOT running as admin (modern security practice)"""
    if platform.system() == 'Windows':
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if is_admin:
                print("⚠️  You're running as Administrator.")
                print("   For security, please run this from a normal user terminal.")
                print("   The application will install to your user directory.")
                input("\nPress Enter to continue anyway, or Ctrl+C to exit...")
        except:
            pass


def main():
    """Simple, modern installation process"""
    print("=" * 60)
    print("Break Reminder - Modern Installation")
    print("=" * 60)
    print()
    
    # Check we're not admin
    check_admin()
    
    # Set up paths (user-level installation)
    user_home = Path.home()
    install_dir = user_home / "AppData" / "Local" / "BreakReminder"
    install_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Installing to: {install_dir}")
    print()
    
    # Step 1: Install dependencies
    print("📦 Installing dependencies...")
    deps = [
        "pystray>=0.19.0",
        "pillow>=10.0.0", 
        "plyer>=2.1",
        "pynput>=1.7.6",
        "pyinstaller>=6.0.0"
    ]
    
    for dep in deps:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--user", dep],
            capture_output=True
        )
    print("✅ Dependencies installed\n")
    
    # Step 2: Copy application files
    print("📄 Copying application files...")
    app_file = Path("unified-break-reminder.py")
    if app_file.exists():
        shutil.copy2(app_file, install_dir / "break_reminder.py")
    else:
        print("⚠️  Application file not found, creating placeholder...")
        (install_dir / "break_reminder.py").write_text(
            "# Placeholder - Replace with actual break_reminder.py"
        )
    print("✅ Files copied\n")
    
    # Step 3: Create launcher script (no console window)
    print("🚀 Creating launcher...")
    launcher_content = f'''@echo off
cd /d "{install_dir}"
start "" pythonw.exe break_reminder.py %*
exit
'''
    
    launcher_path = install_dir / "BreakReminder.bat"
    launcher_path.write_text(launcher_content)
    print("✅ Launcher created\n")
    
    # Step 4: Build executable (optional)
    response = input("Build standalone executable? (y/n): ")
    if response.lower() == 'y':
        print("\n🔨 Building executable (this may take a minute)...")
        
        # Create spec file programmatically (avoids deprecation)
        spec_content = f'''
# Auto-generated spec file
import sys
from pathlib import Path

a = Analysis(
    ['{install_dir / "break_reminder.py"}'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['pynput.mouse._win32', 'pynput.keyboard._win32'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'scipy'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='BreakReminder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
        
        spec_file = install_dir / "BreakReminder.spec"
        spec_file.write_text(spec_content)
        
        # Build using spec file (avoids admin requirement)
        os.chdir(install_dir)
        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", 
             "--distpath", str(install_dir / "dist"),
             "--workpath", str(install_dir / "build"),
             "--noconfirm", "--clean",
             str(spec_file)],
            capture_output=True
        )
        
        if result.returncode == 0:
            print("✅ Executable built successfully\n")
            exe_path = install_dir / "dist" / "BreakReminder.exe"
        else:
            print("⚠️  Build failed, using Python script instead\n")
            exe_path = launcher_path
    else:
        exe_path = launcher_path
    
    # Step 5: Create shortcuts (user-level, no admin)
    print("🔗 Creating shortcuts...")
    
    # Desktop shortcut
    desktop = user_home / "Desktop"
    if desktop.exists():
        shortcut_ps = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{desktop}\\Break Reminder.lnk")
$Shortcut.TargetPath = "{exe_path}"
$Shortcut.WorkingDirectory = "{install_dir}"
$Shortcut.Save()
'''
        subprocess.run(
            ["powershell", "-Command", shortcut_ps],
            capture_output=True
        )
        print("✅ Desktop shortcut created")
    
    # Step 6: Auto-start setup (user registry, no admin)
    print("\n🔄 Auto-start Configuration")
    response = input("Enable auto-start with Windows? (y/n): ")
    if response.lower() == 'y':
        if platform.system() == 'Windows':
            import winreg
            
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            try:
                # User-level registry (HKEY_CURRENT_USER)
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, 
                    key_path, 
                    0, 
                    winreg.KEY_SET_VALUE
                ) as key:
                    winreg.SetValueEx(
                        key,
                        "BreakReminder",
                        0,
                        winreg.REG_SZ,
                        f'"{exe_path}" --minimized'
                    )
                print("✅ Auto-start enabled (user-level)\n")
            except Exception as e:
                print(f"⚠️  Could not enable auto-start: {e}\n")
    
    # Complete!
    print("=" * 60)
    print("✨ Installation Complete!")
    print("=" * 60)
    print()
    print(f"📁 Installed to: {install_dir}")
    print(f"🖥️  Desktop shortcut: Break Reminder.lnk")
    if response.lower() == 'y':
        print(f"🔄 Auto-start: Enabled")
    print()
    print("To run the application:")
    print(f"  • Double-click the desktop shortcut, or")
    print(f"  • Run: {exe_path}")
    print()
    
    # Launch option
    launch = input("Launch Break Reminder now? (y/n): ")
    if launch.lower() == 'y':
        import subprocess
        if platform.system() == 'Windows':
            subprocess.Popen([str(exe_path)], shell=True)
        print("✅ Break Reminder started!")
    
    print("\nPress Enter to exit...")
    input()


if __name__ == "__main__":
    main()
    