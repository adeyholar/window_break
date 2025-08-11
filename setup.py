# setup.py - PyInstaller configuration for secure Windows executable
"""
Build script for creating a secure Windows executable of Break Reminder
that won't be flagged as a virus and can auto-start with Windows.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Build configuration
APP_NAME = "BreakReminder"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Your Name"
APP_DESCRIPTION = "Desktop break reminder with activity detection"
MAIN_SCRIPT = "standalone-break-reminder.py"

def create_spec_file():
    """Create PyInstaller spec file with security-focused settings"""
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{MAIN_SCRIPT}'],
    pathex=[],
    binaries=[],
    datas=[
        ('README.md', '.'),
        ('LICENSE', '.'),
    ],
    hiddenimports=[
        'pynput.mouse._win32',
        'pynput.keyboard._win32',
        'PIL._tkinter_finder',
        'plyer.platforms.win.notification',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
        'notebook',
        'tkinter.test',
        'test',
        'unittest',
        'distutils',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',
    icon='icon.ico',
    uac_admin=False,
    uac_uiaccess=False,
    manifest='app.manifest',
)
'''
    
    with open(f"{APP_NAME}.spec", "w") as f:
        f.write(spec_content)

def create_version_info():
    """Create version info file for Windows executable metadata"""
    version_info = f'''# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({APP_VERSION.replace('.', ', ')}, 0),
    prodvers=({APP_VERSION.replace('.', ', ')}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'{APP_AUTHOR}'),
        StringStruct(u'FileDescription', u'{APP_DESCRIPTION}'),
        StringStruct(u'FileVersion', u'{APP_VERSION}'),
        StringStruct(u'InternalName', u'{APP_NAME}'),
        StringStruct(u'LegalCopyright', u'Copyright © 2025 {APP_AUTHOR}'),
        StringStruct(u'OriginalFilename', u'{APP_NAME}.exe'),
        StringStruct(u'ProductName', u'{APP_NAME}'),
        StringStruct(u'ProductVersion', u'{APP_VERSION}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    with open("version_info.txt", "w") as f:
        f.write(version_info)

def create_manifest():
    """Create application manifest for Windows compatibility and security"""
    manifest_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity
    version="1.0.0.0"
    processorArchitecture="*"
    name="BreakReminder"
    type="win32"
  />
  <description>Desktop break reminder application</description>
  
  <!-- Windows 10/11 compatibility -->
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
    <application>
      <!-- Windows 10 -->
      <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/>
      <!-- Windows 8.1 -->
      <supportedOS Id="{1f676c76-80e1-4239-95bb-83d0f6d0da78}"/>
      <!-- Windows 8 -->
      <supportedOS Id="{4a2f28e3-53b9-4441-ba9c-d69d4a4a6e38}"/>
      <!-- Windows 7 -->
      <supportedOS Id="{35138b9a-5d96-4fbd-8e2d-a2440225f93a}"/>
    </application>
  </compatibility>
  
  <!-- DPI awareness -->
  <application xmlns="urn:schemas-microsoft-com:asm.v3">
    <windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true</dpiAware>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2</dpiAwareness>
    </windowsSettings>
  </application>
  
  <!-- Security settings -->
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v2">
    <security>
      <requestedPrivileges xmlns="urn:schemas-microsoft-com:asm.v3">
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
</assembly>
'''
    
    with open("app.manifest", "w") as f:
        f.write(manifest_content)

def create_icon():
    """Create a simple icon file if none exists"""
    if not os.path.exists("icon.ico"):
        print("Creating default icon...")
        try:
            from PIL import Image, ImageDraw
            
            # Create a simple icon
            size = 256
            image = Image.new('RGBA', (size, size), (255, 255, 255, 0))
            draw = ImageDraw.Draw(image)
            
            # Draw a clock icon
            margin = size // 8
            draw.ellipse([margin, margin, size-margin, size-margin], 
                        fill=(52, 125, 50, 255), outline=(0, 0, 0, 255), width=8)
            
            # Clock hands
            center = size // 2
            hand_length = size // 3
            draw.line([center, center, center, center - hand_length], 
                     fill=(255, 255, 255, 255), width=8)
            draw.line([center, center, center + hand_length//2, center], 
                     fill=(255, 255, 255, 255), width=6)
            
            # Save as ICO
            image.save("icon.ico", format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
            print("✓ Icon created successfully")
        except ImportError:
            print("⚠ PIL not available, using default icon")
            # Create a minimal ico file
            with open("icon.ico", "wb") as f:
                f.write(b'\\x00\\x00\\x01\\x00\\x01\\x00\\x10\\x10\\x00\\x00\\x01\\x00\\x08\\x00h\\x05\\x00\\x00\\x16\\x00\\x00\\x00')

def create_readme():
    """Create README file for transparency"""
    readme_content = f"""# {APP_NAME}

## Description
{APP_DESCRIPTION}

## Features
- Pomodoro-style work/break timer
- Activity detection (automatically pauses when away)
- System tray integration
- Auto-start with Windows
- Customizable work and break intervals
- Sound and visual notifications

## Privacy & Security
This application:
- Only monitors local activity (mouse/keyboard) for timer functionality
- Does NOT send any data over the internet
- Does NOT collect personal information
- Stores settings locally in JSON format
- Is open source and transparent

## Startup Behavior
This application can be configured to start automatically with Windows
for convenience. You can disable this in the application settings or
Windows startup settings.

## Source Code
This application is built from open source Python code using:
- tkinter (GUI)
- pynput (activity detection)
- pystray (system tray)
- plyer (notifications)

## Version: {APP_VERSION}
## Author: {APP_AUTHOR}
## Build Date: {datetime.now().strftime('%Y-%m-%d')}
"""
    
    with open("README.md", "w") as f:
        f.write(readme_content)

def create_license():
    """Create license file"""
    license_content = """MIT License

Copyright (c) 2025 Break Reminder

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    
    with open("LICENSE", "w") as f:
        f.write(license_content)

def build_executable():
    """Build the executable using PyInstaller"""
    print("🔨 Building Windows executable...")
    
    # Clean previous builds
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # Build with PyInstaller
    cmd = [
        "pyinstaller",
        f"{APP_NAME}.spec",
        "--clean",
        "--noconfirm"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✓ Executable built successfully!")
        print(f"📁 Output: dist/{APP_NAME}.exe")
        return True
    else:
        print("❌ Build failed:")
        print(result.stderr)
        return False

def create_installer_script():
    """Create NSIS installer script for professional distribution"""
    nsis_script = f'''# NSIS Installer Script for {APP_NAME}
# This creates a professional installer that won't be flagged as malicious

!define APP_NAME "{APP_NAME}"
!define APP_VERSION "{APP_VERSION}"
!define APP_PUBLISHER "{APP_AUTHOR}"
!define APP_DESCRIPTION "{APP_DESCRIPTION}"
!define APP_EXE "${{APP_NAME}}.exe"

# Installer properties
Name "${{APP_NAME}}"
OutFile "${{APP_NAME}}_Setup_${{APP_VERSION}}.exe"
InstallDir "$PROGRAMFILES64\\${{APP_NAME}}"
RequestExecutionLevel admin
ShowInstDetails show
ShowUnInstDetails show

# Modern UI
!include "MUI2.nsh"
!define MUI_ABORTWARNING
!define MUI_ICON "icon.ico"
!define MUI_UNICON "icon.ico"

# Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

# Languages
!insertmacro MUI_LANGUAGE "English"

# Version Information
VIProductVersion "${{APP_VERSION}}.0"
VIAddVersionKey "ProductName" "${{APP_NAME}}"
VIAddVersionKey "CompanyName" "${{APP_PUBLISHER}}"
VIAddVersionKey "LegalCopyright" "© 2025 ${{APP_PUBLISHER}}"
VIAddVersionKey "FileDescription" "${{APP_DESCRIPTION}}"
VIAddVersionKey "FileVersion" "${{APP_VERSION}}"

Section "Install"
  SetOutPath "$INSTDIR"
  
  # Copy files
  File "dist\\${{APP_EXE}}"
  File "README.md"
  File "LICENSE"
  File "icon.ico"
  
  # Create uninstaller
  WriteUninstaller "$INSTDIR\\Uninstall.exe"
  
  # Registry entries
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" \\
                   "DisplayName" "${{APP_NAME}}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" \\
                   "UninstallString" "$INSTDIR\\Uninstall.exe"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" \\
                   "Publisher" "${{APP_PUBLISHER}}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" \\
                   "DisplayVersion" "${{APP_VERSION}}"
  
  # Start menu shortcuts
  CreateDirectory "$SMPROGRAMS\\${{APP_NAME}}"
  CreateShortCut "$SMPROGRAMS\\${{APP_NAME}}\\${{APP_NAME}}.lnk" "$INSTDIR\\${{APP_EXE}}"
  CreateShortCut "$SMPROGRAMS\\${{APP_NAME}}\\Uninstall.lnk" "$INSTDIR\\Uninstall.exe"
  
  # Desktop shortcut (optional)
  CreateShortCut "$DESKTOP\\${{APP_NAME}}.lnk" "$INSTDIR\\${{APP_EXE}}"
  
SectionEnd

Section "Uninstall"
  # Remove files
  Delete "$INSTDIR\\${{APP_EXE}}"
  Delete "$INSTDIR\\README.md"
  Delete "$INSTDIR\\LICENSE"
  Delete "$INSTDIR\\icon.ico"
  Delete "$INSTDIR\\Uninstall.exe"
  RMDir "$INSTDIR"
  
  # Remove shortcuts
  Delete "$SMPROGRAMS\\${{APP_NAME}}\\${{APP_NAME}}.lnk"
  Delete "$SMPROGRAMS\\${{APP_NAME}}\\Uninstall.lnk"
  RMDir "$SMPROGRAMS\\${{APP_NAME}}"
  Delete "$DESKTOP\\${{APP_NAME}}.lnk"
  
  # Remove registry entries
  DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}"
  
SectionEnd
'''
    
    with open(f"{APP_NAME}_installer.nsi", "w") as f:
        f.write(nsis_script)

def create_build_script():
    """Create automated build script"""
    build_script = f'''@echo off
echo Building {APP_NAME} Windows Executable
echo =====================================

echo.
echo Installing dependencies...
pip install pyinstaller pillow pystray plyer pynput

echo.
echo Creating build files...
python setup.py

echo.
echo Build complete!
echo.
echo Executable location: dist\\{APP_NAME}.exe
echo.
echo To create installer, install NSIS and run:
echo makensis {APP_NAME}_installer.nsi
echo.
pause
'''
    
    with open("build.bat", "w") as f:
        f.write(build_script)

if __name__ == "__main__":
    import datetime
    
    print(f"🚀 Setting up build environment for {APP_NAME}")
    
    # Create all necessary files
    create_readme()
    create_license()
    create_icon()
    create_version_info()
    create_manifest()
    create_spec_file()
    create_installer_script()
    create_build_script()
    
    print("✓ All build files created!")
    print("\nNext steps:")
    print("1. Run: python setup.py")
    print("2. Run: pyinstaller BreakReminder.spec")
    print("3. Test: dist/BreakReminder.exe")
    print("4. (Optional) Create installer with NSIS")
    
    # Optionally build immediately
    if len(sys.argv) > 1 and sys.argv[1] == "--build":
        if build_executable():
            print("\n🎉 Build successful!")
        else:
            print("\n❌ Build failed!")
