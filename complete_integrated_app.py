#!/usr/bin/env python3
"""
Complete Break Reminder Application with Windows Integration
A desktop application with activity detection, system tray, and Windows startup integration.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import os
import sys
import winreg
from datetime import datetime, timedelta
from pathlib import Path

# For system tray functionality
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    print("Note: Install 'pystray' and 'pillow' for system tray support")

# For notification support
try:
    from plyer import notification
    NOTIFICATION_AVAILABLE = True
except ImportError:
    NOTIFICATION_AVAILABLE = False
    print("Note: Install 'plyer' for better notifications")

# For activity detection
try:
    import pynput
    from pynput import mouse, keyboard
    ACTIVITY_DETECTION_AVAILABLE = True
except ImportError:
    ACTIVITY_DETECTION_AVAILABLE = False
    print("Note: Install 'pynput' for activity detection")

class WindowsAutoStart:
    """Handles Windows startup integration securely"""
    
    def __init__(self, app_name="BreakReminder"):
        self.app_name = app_name
        self.startup_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        
    def get_executable_path(self):
        """Get the current executable path"""
        if getattr(sys, 'frozen', False):
            return sys.executable
        else:
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
        """Enable auto-startup with Windows"""
        try:
            exe_path = self.get_executable_path()
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.startup_key, 0, 
                               winreg.KEY_SET_VALUE) as key:
                startup_command = f'"{exe_path}" --minimized'
                winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, startup_command)
            return True, "Auto-startup enabled successfully"
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

class ActivityMonitor:
    """Monitor mouse and keyboard activity"""
    
    def __init__(self, callback=None, timeout=60):
        self.callback = callback
        self.timeout = timeout
        self.last_activity = time.time()
        self.is_active = True
        self.mouse_listener = None
        self.keyboard_listener = None
        self.monitor_thread = None
        self.running = False
        
    def on_activity(self):
        """Called when any activity is detected"""
        current_time = time.time()
        was_inactive = not self.is_active
        
        self.last_activity = current_time
        self.is_active = True
        
        if was_inactive and self.callback:
            self.callback('resumed')
    
    def on_mouse_move(self, x, y):
        self.on_activity()
    
    def on_mouse_click(self, x, y, button, pressed):
        self.on_activity()
    
    def on_mouse_scroll(self, x, y, dx, dy):
        self.on_activity()
    
    def on_key_press(self, key):
        self.on_activity()
    
    def monitor_activity(self):
        """Monitor for inactivity in separate thread"""
        while self.running:
            current_time = time.time()
            time_since_activity = current_time - self.last_activity
            
            if self.is_active and time_since_activity > self.timeout:
                self.is_active = False
                if self.callback:
                    self.callback('paused')
            
            time.sleep(1)
    
    def start_monitoring(self):
        """Start monitoring user activity"""
        if not ACTIVITY_DETECTION_AVAILABLE:
            return False
        
        self.running = True
        self.last_activity = time.time()
        self.is_active = True
        
        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse_move,
            on_click=self.on_mouse_click,
            on_scroll=self.on_mouse_scroll
        )
        self.mouse_listener.start()
        
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        self.keyboard_listener.start()
        
        self.monitor_thread = threading.Thread(target=self.monitor_activity, daemon=True)
        self.monitor_thread.start()
        
        return True
    
    def stop_monitoring(self):
        """Stop monitoring user activity"""
        self.running = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()

class BreakReminderApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Break Reminder")
        self.root.geometry("450x750")
        self.root.resizable(False, False)
        
        # Handle startup arguments
        self.start_minimized = self.handle_startup_args()
        
        # Configuration
        self.config_file = "break_reminder_config.json"
        self.load_config()
        
        # Windows integration
        self.autostart_manager = WindowsAutoStart()
        
        # Timer state
        self.is_running = False
        self.is_break = False
        self.is_paused = False
        self.pause_reason = ""
        self.time_left = self.work_minutes * 60
        self.timer_thread = None
        self.break_window = None
        
        # Activity monitoring
        self.activity_monitor = ActivityMonitor(
            callback=self.on_activity_change,
            timeout=self.inactivity_timeout
        )
        
        # System tray
        self.tray_icon = None
        
        # Setup UI
        self.setup_ui()
        
        # Setup system tray if available
        if TRAY_AVAILABLE:
            self.setup_tray()
        
        # Start activity monitoring if enabled
        if self.activity_detection_enabled and ACTIVITY_DETECTION_AVAILABLE:
            self.activity_monitor.start_monitoring()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Handle minimized startup
        if self.start_minimized and TRAY_AVAILABLE:
            self.root.withdraw()
            if NOTIFICATION_AVAILABLE:
                notification.notify(
                    title="Break Reminder",
                    message="Started in background. Click tray icon to open.",
                    app_name="Break Reminder",
                    timeout=3
                )
        
        # Auto-start timer if enabled and not starting minimized
        if self.auto_start_on_launch and not self.start_minimized:
            self.start_timer()
    
    def handle_startup_args(self):
        """Handle command line arguments for startup behavior"""
        return len(sys.argv) > 1 and "--minimized" in sys.argv
        
    def load_config(self):
        """Load configuration from file or use defaults"""
        default_config = {
            "work_minutes": 25,
            "break_minutes": 5,
            "long_break_minutes": 15,
            "sessions_until_long_break": 4,
            "sound_enabled": True,
            "minimize_to_tray": True,
            "auto_start_break": True,
            "auto_start_work": False,
            "auto_start_on_launch": True,
            "auto_restart_on_skip": True,
            "activity_detection_enabled": True,
            "inactivity_timeout": 60,
            "pause_during_breaks": False
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    for key, value in default_config.items():
                        setattr(self, key, config.get(key, value))
            except:
                for key, value in default_config.items():
                    setattr(self, key, value)
        else:
            for key, value in default_config.items():
                setattr(self, key, value)
        
        self.session_count = 0
        
    def save_config(self):
        """Save current configuration to file"""
        config = {
            "work_minutes": self.work_minutes,
            "break_minutes": self.break_minutes,
            "long_break_minutes": self.long_break_minutes,
            "sessions_until_long_break": self.sessions_until_long_break,
            "sound_enabled": self.sound_enabled,
            "minimize_to_tray": self.minimize_to_tray,
            "auto_start_break": self.auto_start_break,
            "auto_start_work": self.auto_start_work,
            "auto_start_on_launch": self.auto_start_on_launch,
            "auto_restart_on_skip": self.auto_restart_on_skip,
            "activity_detection_enabled": self.activity_detection_enabled,
            "inactivity_timeout": self.inactivity_timeout,
            "pause_during_breaks": self.pause_during_breaks
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def setup_ui(self):
        """Setup the main user interface"""
        style = ttk.Style()
        style.theme_use('clam')
        
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="⏰ Break Reminder", 
                                font=('Arial', 20, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Status
        self.status_label = ttk.Label(main_frame, text="Ready to start working",
                                      font=('Arial', 12))
        self.status_label.grid(row=1, column=0, columnspan=2, pady=(0, 10))
        
        # Activity status
        self.activity_label = ttk.Label(main_frame, text="Activity: Active",
                                        font=('Arial', 10), foreground='green')
        self.activity_label.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        # Timer display
        self.timer_label = ttk.Label(main_frame, text="25:00",
                                     font=('Arial', 48, 'bold'))
        self.timer_label.grid(row=3, column=0, columnspan=2, pady=(0, 20))
        
        # Session counter
        self.session_label = ttk.Label(main_frame, text="Session: 0 / 4",
                                       font=('Arial', 10))
        self.session_label.grid(row=4, column=0, columnspan=2, pady=(0, 20))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(0, 20))
        
        self.start_button = ttk.Button(button_frame, text="Start Work",
                                       command=self.toggle_timer, width=12)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.reset_button = ttk.Button(button_frame, text="Reset",
                                       command=self.reset_timer, width=12)
        self.reset_button.grid(row=0, column=1, padx=5)
        
        # Settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Timer Settings", padding="10")
        settings_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Create StringVar variables
        self.work_var = tk.StringVar(value=str(self.work_minutes))
        self.break_var = tk.StringVar(value=str(self.break_minutes))
        self.long_break_var = tk.StringVar(value=str(self.long_break_minutes))
        self.sessions_var = tk.StringVar(value=str(self.sessions_until_long_break))
        self.timeout_var = tk.StringVar(value=str(self.inactivity_timeout))
        
        # Timer settings
        ttk.Label(settings_frame, text="Work time (min):").grid(row=0, column=0, sticky=tk.W)
        ttk.Spinbox(settings_frame, from_=1, to=60, width=10, textvariable=self.work_var).grid(row=0, column=1, padx=(10, 0))
        
        ttk.Label(settings_frame, text="Break time (min):").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Spinbox(settings_frame, from_=1, to=30, width=10, textvariable=self.break_var).grid(row=1, column=1, padx=(10, 0), pady=(5, 0))
        
        ttk.Label(settings_frame, text="Long break (min):").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Spinbox(settings_frame, from_=5, to=60, width=10, textvariable=self.long_break_var).grid(row=2, column=1, padx=(10, 0), pady=(5, 0))
        
        ttk.Label(settings_frame, text="Sessions until long break:").grid(row=3, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Spinbox(settings_frame, from_=2, to=10, width=10, textvariable=self.sessions_var).grid(row=3, column=1, padx=(10, 0), pady=(5, 0))
        
        # Activity Settings
        activity_frame = ttk.LabelFrame(main_frame, text="Activity Detection", padding="10")
        activity_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(activity_frame, text="Inactivity timeout (sec):").grid(row=0, column=0, sticky=tk.W)
        ttk.Spinbox(activity_frame, from_=30, to=300, width=10, textvariable=self.timeout_var).grid(row=0, column=1, padx=(10, 0))
        
        # Checkboxes
        checkbox_frame = ttk.Frame(main_frame)
        checkbox_frame.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # All checkboxes
        self.sound_var = tk.BooleanVar(value=self.sound_enabled)
        ttk.Checkbutton(checkbox_frame, text="Enable sound notifications", variable=self.sound_var).grid(row=0, column=0, sticky=tk.W)
        
        self.auto_break_var = tk.BooleanVar(value=self.auto_start_break)
        ttk.Checkbutton(checkbox_frame, text="Auto-start breaks", variable=self.auto_break_var).grid(row=1, column=0, sticky=tk.W)
        
        self.auto_work_var = tk.BooleanVar(value=self.auto_start_work)
        ttk.Checkbutton(checkbox_frame, text="Auto-start work after break", variable=self.auto_work_var).grid(row=2, column=0, sticky=tk.W)
        
        self.auto_launch_var = tk.BooleanVar(value=self.auto_start_on_launch)
        ttk.Checkbutton(checkbox_frame, text="Auto-start timer on launch", variable=self.auto_launch_var).grid(row=3, column=0, sticky=tk.W)
        
        self.auto_skip_var = tk.BooleanVar(value=self.auto_restart_on_skip)
        ttk.Checkbutton(checkbox_frame, text="Auto-restart work when skipping break", variable=self.auto_skip_var).grid(row=4, column=0, sticky=tk.W)
        
        self.activity_var = tk.BooleanVar(value=self.activity_detection_enabled)
        ttk.Checkbutton(checkbox_frame, text="Enable activity detection", variable=self.activity_var, command=self.toggle_activity_detection).grid(row=5, column=0, sticky=tk.W)
        
        self.pause_breaks_var = tk.BooleanVar(value=self.pause_during_breaks)
        ttk.Checkbutton(checkbox_frame, text="Pause timer during breaks when inactive", variable=self.pause_breaks_var).grid(row=6, column=0, sticky=tk.W)
        
        # Windows Integration
        self.autostart_var = tk.BooleanVar()
        ttk.Checkbutton(checkbox_frame, text="Start with Windows", variable=self.autostart_var, command=self.toggle_autostart).grid(row=7, column=0, sticky=tk.W)
        
        if TRAY_AVAILABLE:
            self.tray_var = tk.BooleanVar(value=self.minimize_to_tray)
            ttk.Checkbutton(checkbox_frame, text="Minimize to system tray", variable=self.tray_var).grid(row=8, column=0, sticky=tk.W)
        
        # Initialize autostart checkbox
        self.autostart_var.set(self.autostart_manager.is_startup_enabled())
        
        # Status messages
        if not ACTIVITY_DETECTION_AVAILABLE:
            ttk.Label(checkbox_frame, text="⚠️ Install 'pynput' for activity detection", foreground='orange').grid(row=9, column=0, sticky=tk.W, pady=(5, 0))
        
        # Save button
        ttk.Button(main_frame, text="Save Settings", command=self.save_settings, width=20).grid(row=9, column=0, columnspan=2, pady=(10, 0))
    
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
    
    def toggle_activity_detection(self):
        """Toggle activity detection"""
        if not ACTIVITY_DETECTION_AVAILABLE:
            messagebox.showwarning("Feature Unavailable", 
                                   "Activity detection requires 'pynput' package.\n"
                                   "Install it with: pip install pynput")
            self.activity_var.set(False)
            return
        
        if self.activity_var.get():
            self.activity_monitor.start_monitoring()
            self.activity_label.config(text="Activity: Monitoring", foreground='blue')
        else:
            self.activity_monitor.stop_monitoring()
            self.activity_label.config(text="Activity: Disabled", foreground='gray')
    
    def on_activity_change(self, status):
        """Handle activity status changes"""
        if status == 'paused':
            self.is_paused = True
            self.pause_reason = "Away from computer"
            self.root.after(0, lambda: self.activity_label.config(
                text="Activity: Away (Timer Paused)", foreground='red'))
        elif status == 'resumed':
            if self.is_paused:
                self.is_paused = False
                self.pause_reason = ""
                self.root.after(0, lambda: self.activity_label.config(
                    text="Activity: Active", foreground='green'))
    
    def setup_tray(self):
        """Setup system tray icon"""
        if not TRAY_AVAILABLE:
            return
        
        def create_image():
            image = Image.new('RGB', (64, 64), color='white')
            draw = ImageDraw.Draw(image)
            draw.ellipse([8, 8, 56, 56], fill='blue')
            return image
        
        def show_window():
            self.root.deiconify()
            self.root.lift()
        
        def quit_app():
            self.is_running = False
            self.activity_monitor.stop_monitoring()
            if self.timer_thread:
                self.timer_thread.join(timeout=1)
            self.root.quit()
        
        menu = pystray.Menu(
            pystray.MenuItem("Show", show_window, default=True),
            pystray.MenuItem("Start/Stop", self.toggle_timer),
            pystray.MenuItem("Quit", quit_app)
        )
        
        self.tray_icon = pystray.Icon("break_reminder", create_image(), menu=menu)
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()
    
    def update_display(self):
        """Update the timer display"""
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        if self.is_paused:
            time_str += " ⏸️"
        
        self.timer_label.config(text=time_str)
        self.session_label.config(text=f"Session: {self.session_count} / {self.sessions_until_long_break}")
    
    def toggle_timer(self):
        """Start or stop the timer"""
        if self.is_running:
            self.stop_timer()
        else:
            self.start_timer()
    
    def start_timer(self):
        """Start the timer"""
        self.is_running = True
        self.start_button.config(text="Stop")
        
        if self.is_break:
            self.status_label.config(text="☕ Taking a break - Relax!")
        else:
            self.status_label.config(text="💼 Working - Stay focused!")
        
        self.timer_thread = threading.Thread(target=self.run_timer, daemon=True)
        self.timer_thread.start()
    
    def stop_timer(self):
        """Stop the timer"""
        self.is_running = False
        self.start_button.config(text="Start Work")
        self.status_label.config(text="Timer stopped")
    
    def reset_timer(self):
        """Reset the timer"""
        self.is_running = False
        self.is_break = False
        self.is_paused = False
        self.session_count = 0
        
        try:
            self.work_minutes = int(self.work_var.get()) if self.work_var.get() else self.work_minutes
        except (ValueError, AttributeError):
            pass
            
        self.time_left = self.work_minutes * 60
        self.start_button.config(text="Start Work")
        self.status_label.config(text="Ready to start working")
        self.update_display()
        
        if self.break_window:
            self.break_window.destroy()
            self.break_window = None
    
    def run_timer(self):
        """Timer loop that runs in a separate thread"""
        while self.is_running and self.time_left > 0:
            should_pause = (
                self.activity_detection_enabled and 
                ACTIVITY_DETECTION_AVAILABLE and
                not self.activity_monitor.is_active and
                (not self.is_break or self.pause_during_breaks)
            )
            
            if not should_pause or not self.is_paused:
                if self.is_paused and not should_pause:
                    self.is_paused = False
                    self.pause_reason = ""
                
                time.sleep(1)
                if not self.is_paused:
                    self.time_left -= 1
            else:
                if not self.is_paused:
                    self.is_paused = True
                    self.pause_reason = "Away from computer"
                time.sleep(1)
            
            self.root.after(0, self.update_display)
        
        if self.is_running and self.time_left == 0:
            self.root.after(0, self.on_timer_complete)
    
    def on_timer_complete(self):
        """Handle timer completion"""
        if self.is_break:
            self.close_break_window()
            self.show_notification("Break Over!", "Time to get back to work!")
            self.is_break = False
            try:
                self.work_minutes = int(self.work_var.get()) if self.work_var.get() else self.work_minutes
            except (ValueError, AttributeError):
                pass
            self.time_left = self.work_minutes * 60
            
            if self.auto_work_var.get():
                self.start_timer()
            else:
                self.is_running = False
                self.start_button.config(text="Start Work")
                self.status_label.config(text="Ready to start working")
        else:
            self.session_count += 1
            
            if self.session_count >= self.sessions_until_long_break:
                try:
                    break_minutes = int(self.long_break_var.get()) if self.long_break_var.get() else self.long_break_minutes
                except (ValueError, AttributeError):
                    break_minutes = self.long_break_minutes
                self.session_count = 0
                break_type = "long"
            else:
                try:
                    break_minutes = int(self.break_var.get()) if self.break_var.get() else self.break_minutes
                except (ValueError, AttributeError):
                    break_minutes = self.break_minutes
                break_type = "short"
            
            self.show_notification("Work Complete!", f"Time for a {break_minutes} minute break!")
            self.is_break = True
            self.time_left = break_minutes * 60
            
            self.show_break_window(break_minutes, break_type)
            
            if self.auto_break_var.get():
                self.start_timer()
            else:
                self.is_running = False
                self.start_button.config(text="Start Break")
                self.status_label.config(text="Break time!")
        
        self.update_display()
    
    def show_break_window(self, break_minutes, break_type):
        """Show the break popup window"""
        if self.break_window:
            self.break_window.destroy()
        
        self.break_window = tk.Toplevel(self.root)
        self.break_window.title("Break Time!")
        self.break_window.geometry("600x400")
        self.break_window.configure(bg='#2E7D32')
        self.break_window.attributes('-topmost', True)
        
        # Center window
        self.break_window.update_idletasks()
        width = self.break_window.winfo_width()
        height = self.break_window.winfo_height()
        x = (self.break_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.break_window.winfo_screenheight() // 2) - (height // 2)
        self.break_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Content
        title_text = "☕ Long Break Time!" if break_type == "long" else "☕ Break Time!"
        tk.Label(self.break_window, text=title_text, font=('Arial', 32, 'bold'), 
                bg='#2E7D32', fg='white').pack(pady=(50, 20))
        
        tk.Label(self.break_window, text="Time to rest your eyes and stretch!",
                font=('Arial', 16), bg='#2E7D32', fg='white').pack(pady=(0, 30))
        
        self.break_timer_label = tk.Label(self.break_window, text=f"{break_minutes:02d}:00",
                                         font=('Arial', 48, 'bold'), bg='#2E7D32', fg='white')
        self.break_timer_label.pack(pady=(0, 40))
        
        tk.Button(self.break_window, text="Skip Break", command=self.skip_break,
                 font=('Arial', 12), padx=20, pady=10).pack()
        
        def update_break_timer():
            if self.is_break and self.is_running and self.break_window:
                minutes = self.time_left // 60
                seconds = self.time_left % 60
                time_text = f"{minutes:02d}:{seconds:02d}"
                if self.is_paused:
                    time_text += " ⏸️"
                self.break_timer_label.config(text=time_text)
                self.break_window.after(100, update_break_timer)
        
        update_break_timer()
    
    def close_break_window(self):
        """Close the break window"""
        if self.break_window:
            self.break_window.destroy()
            self.break_window = None
    
    def skip_break(self):
        """Skip the current break and optionally restart work timer"""
        self.close_break_window()
        self.is_running = False
        self.is_break = False
        self.is_paused = False
        
        try:
            self.work_minutes = int(self.work_var.get()) if self.work_var.get() else self.work_minutes
        except (ValueError, AttributeError):
            pass
        
        self.time_left = self.work_minutes * 60
        self.update_display()
        
        if self.auto_skip_var.get():
            self.start_timer()
            self.status_label.config(text="💼 Working - Stay focused!")
        else:
            self.start_button.config(text="Start Work")
            self.status_label.config(text="Break skipped - Ready to work")
    
    def show_notification(self, title, message):
        """Show a system notification"""
        if NOTIFICATION_AVAILABLE:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_name="Break Reminder",
                    timeout=5
                )
            except:
                pass
        
        if self.sound_var.get():
            self.play_sound()
    
    def play_sound(self):
        """Play a notification sound"""
        try:
            self.root.bell()
        except:
            pass
    
    def save_settings(self):
        """Save current settings"""
        try:
            self.work_minutes = int(self.work_var.get()) if self.work_var.get() else 25
            self.break_minutes = int(self.break_var.get()) if self.break_var.get() else 5
            self.long_break_minutes = int(self.long_break_var.get()) if self.long_break_var.get() else 15
            self.sessions_until_long_break = int(self.sessions_var.get()) if self.sessions_var.get() else 4
            self.inactivity_timeout = int(self.timeout_var.get()) if self.timeout_var.get() else 60
            
            self.sound_enabled = self.sound_var.get()
            self.auto_start_break = self.auto_break_var.get()
            self.auto_start_work = self.auto_work_var.get()
            self.auto_start_on_launch = self.auto_launch_var.get()
            self.auto_restart_on_skip = self.auto_skip_var.get()
            self.activity_detection_enabled = self.activity_var.get()
            self.pause_during_breaks = self.pause_breaks_var.get()
            
            if TRAY_AVAILABLE:
                self.minimize_to_tray = self.tray_var.get()
            
            self.activity_monitor.timeout = self.inactivity_timeout
            
            if self.activity_detection_enabled and ACTIVITY_DETECTION_AVAILABLE:
                if not self.activity_monitor.running:
                    self.activity_monitor.start_monitoring()
                    self.activity_label.config(text="Activity: Monitoring", foreground='blue')
            else:
                if self.activity_monitor.running:
                    self.activity_monitor.stop_monitoring()
                    self.activity_label.config(text="Activity: Disabled", foreground='gray')
            
            self.save_config()
            messagebox.showinfo("Settings Saved", "Your settings have been saved!")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for all time settings")
    
    def on_closing(self):
        """Handle window closing"""
        if TRAY_AVAILABLE and hasattr(self, 'tray_var') and self.tray_var.get() and self.is_running:
            self.root.withdraw()
            if NOTIFICATION_AVAILABLE:
                try:
                    notification.notify(
                        title="Break Reminder",
                        message="Running in background. Click tray icon to restore.",
                        app_name="Break Reminder",
                        timeout=3
                    )
                except:
                    pass
        else:
            self.is_running = False
            self.activity_monitor.stop_monitoring()
            if self.timer_thread:
                self.timer_thread.join(timeout=1)
            if self.tray_icon:
                self.tray_icon.stop()
            self.root.quit()
    
    def run(self):
        """Start the application"""
        try:
            self.root.mainloop()
        finally:
            self.activity_monitor.stop_monitoring()

if __name__ == "__main__":
    app = BreakReminderApp()
    app.run()