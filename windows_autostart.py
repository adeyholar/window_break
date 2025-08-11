# windows_autostart.py - Windows startup integration module
"""
Windows Auto-Startup Integration
Provides secure methods to add/remove the application from Windows startup
without triggering antivirus false positives.
"""

import os
import sys
import winreg
import shutil
from pathlib import Path

class WindowsAutoStart:
    """Handles Windows startup integration securely"""
    
    def __init__(self, app_name="BreakReminder", app_description="Break Reminder App"):
        self.app_name = app_name
        self.app_description = app_description
        self.startup_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        
    def get_executable_path(self):
        """Get the current executable path"""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            return sys.executable
        else:
            # Running as script
            return os.path.abspath(sys.argv[0])
    
    def is_startup_enabled(self):
        """Check if auto-startup is currently enabled"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.startup_key, 0, winreg.KEY_READ) as key:
                try:
                    value, _ = winreg.QueryValueEx(key, self.app_name)
                    return True
                except FileNotFoundError:
                    return False
        except Exception:
            return False
    
    def enable_startup(self):
        """Enable auto-startup with Windows (current user only for security)"""
        try:
            exe_path = self.get_executable_path()
            
            # Use current user registry (safer than system-wide)
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.startup_key, 0, 
                               winreg.KEY_SET_VALUE) as key:
                # Add to startup with minimized flag
                startup_command = f'"{exe_path}" --minimized'
                winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, startup_command)
            
            return True, "Auto-startup enabled successfully"
            
        except PermissionError:
            return False, "Permission denied. Please run as administrator."
        except Exception as e:
            return False, f"Failed to enable auto-startup: {str(e)}"
    
    def disable_startup(self):
        """Disable auto-startup"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.startup_key, 0, 
                               winreg.KEY_SET_VALUE) as key:
                try:
                    winreg.DeleteValue(key, self.app_name)
                    return True, "Auto-startup disabled successfully"
                except FileNotFoundError:
                    return True, "Auto-startup was not enabled"
                    
        except Exception as e:
            return False, f"Failed to disable auto-startup: {str(e)}"
    
    def create_startup_shortcut(self):
        """Alternative method: Create shortcut in Startup folder"""
        try:
            import pythoncom
            from win32com.shell import shell, shellcon
            
            # Get startup folder
            startup_folder = shell.SHGetFolderPath(0, shellcon.CSIDL_STARTUP, None, 0)
            shortcut_path = os.path.join(startup_folder, f"{self.app_name}.lnk")
            
            # Create shortcut
            pythoncom.CoInitialize()
            shortcut = pythoncom.CoCreateInstance(
                shell.CLSID_ShellLink, None,
                pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink
            )
            
            exe_path = self.get_executable_path()
            shortcut.SetPath(exe_path)
            shortcut.SetDescription(self.app_description)
            shortcut.SetArguments("--minimized")
            shortcut.SetWorkingDirectory(os.path.dirname(exe_path))
            
            persist_file = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
            persist_file.Save(shortcut_path, 0)
            
            pythoncom.CoUninitialize()
            return True, f"Startup shortcut created: {shortcut_path}"
            
        except ImportError:
            return False, "pywin32 not available for shortcut creation"
        except Exception as e:
            return False, f"Failed to create startup shortcut: {str(e)}"
    
    def remove_startup_shortcut(self):
        """Remove shortcut from Startup folder"""
        try:
            from win32com.shell import shell, shellcon
            
            startup_folder = shell.SHGetFolderPath(0, shellcon.CSIDL_STARTUP, None, 0)
            shortcut_path = os.path.join(startup_folder, f"{self.app_name}.lnk")
            
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
                return True, "Startup shortcut removed"
            else:
                return True, "Startup shortcut was not found"
                
        except Exception as e:
            return False, f"Failed to remove startup shortcut: {str(e)}"

# Integration code to add to the main application
def integrate_autostart_ui(self):
    """Add auto-startup controls to the main application UI"""
    
    # Add this to your checkbox_frame in setup_ui method:
    
    # Auto-startup checkbox
    self.autostart_var = tk.BooleanVar()
    autostart_cb = ttk.Checkbutton(
        checkbox_frame, 
        text="Start with Windows",
        variable=self.autostart_var,
        command=self.toggle_autostart
    )
    autostart_cb.grid(row=8, column=0, sticky=tk.W)
    
    # Initialize the checkbox state
    self.autostart_manager = WindowsAutoStart()
    self.autostart_var.set(self.autostart_manager.is_startup_enabled())

def toggle_autostart(self):
    """Toggle Windows auto-startup"""
    if self.autostart_var.get():
        success, message = self.autostart_manager.enable_startup()
        if not success:
            self.autostart_var.set(False)
            messagebox.showerror("Auto-Startup Error", message)
        else:
            messagebox.showinfo("Auto-Startup", message)
    else:
        success, message = self.autostart_manager.disable_startup()
        if not success:
            self.autostart_var.set(True)
            messagebox.showerror("Auto-Startup Error", message)
        else:
            messagebox.showinfo("Auto-Startup", message)

# Command line argument handling for minimized startup
def handle_startup_args():
    """Handle command line arguments for startup behavior"""
    if len(sys.argv) > 1 and "--minimized" in sys.argv:
        # Start minimized to tray
        return True
    return False

# Add this to your main application __init__ method:
def __init__(self):
    # ... existing init code ...
    
    # Handle startup arguments
    self.start_minimized = handle_startup_args()
    
    # ... rest of init code ...
    
    # If starting minimized, don't show window initially
    if self.start_minimized and TRAY_AVAILABLE:
        self.root.withdraw()
        # Show a brief notification that the app started
        if NOTIFICATION_AVAILABLE:
            notification.notify(
                title="Break Reminder",
                message="Started in background. Click tray icon to open.",
                app_name="Break Reminder",
                timeout=3
            )

# Security considerations for the executable
SECURITY_CHECKLIST = """
Windows Executable Security Checklist:
=====================================

1. ✓ Code Signing (Recommended):
   - Get a code signing certificate from a trusted CA
   - Sign the executable: signtool sign /f certificate.p12 /p password BreakReminder.exe
   - This prevents "Unknown Publisher" warnings

2. ✓ Metadata Inclusion:
   - Version information included
   - Company/Author information
   - Application description
   - Legal copyright notice

3. ✓ Transparent Functionality:
   - README.md explaining what the app does
   - License file included
   - No hidden or obfuscated functionality
   - Clear privacy policy

4. ✓ Registry Access Pattern:
   - Uses HKEY_CURRENT_USER (not HKEY_LOCAL_MACHINE)
   - Only modifies startup registry key
   - No system-level changes

5. ✓ File System Access:
   - Only writes to user directories
   - Config files in application directory
   - No system file modifications

6. ✓ Network Activity:
   - No network communication
   - No data transmission
   - Purely local functionality

7. ✓ Process Behavior:
   - Single process application
   - No process injection
   - No system service installation
   - Clean shutdown procedures

8. ✓ Distribution Method:
   - NSIS installer for professional deployment
   - Uninstaller included
   - Proper Add/Remove Programs integration
"""

if __name__ == "__main__":
    print(SECURITY_CHECKLIST)
    
    # Test auto-startup functionality
    autostart = WindowsAutoStart()
    print(f"Auto-startup currently enabled: {autostart.is_startup_enabled()}")
