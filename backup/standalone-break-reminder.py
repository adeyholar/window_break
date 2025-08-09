#!/usr/bin/env python3
"""
Standalone Break Reminder Application
A desktop application that runs in the system tray and reminds you to take breaks.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import os
from datetime import datetime, timedelta
import sys

# For system tray functionality
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    print("Note: Install 'pystray' and 'pillow' for system tray support")
    print("Run: pip install pystray pillow")

# For notification support
try:
    from plyer import notification
    NOTIFICATION_AVAILABLE = True
except ImportError:
    NOTIFICATION_AVAILABLE = False
    print("Note: Install 'plyer' for better notifications")
    print("Run: pip install plyer")

class BreakReminderApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Break Reminder")
        self.root.geometry("450x600")
        self.root.resizable(False, False)
        
        # Configuration
        self.config_file = "break_reminder_config.json"
        self.load_config()
        
        # Timer state
        self.is_running = False
        self.is_break = False
        self.time_left = self.work_minutes * 60
        self.timer_thread = None
        self.break_window = None
        
        # System tray
        self.tray_icon = None
        
        # Setup UI
        self.setup_ui()
        
        # Setup system tray if available
        if TRAY_AVAILABLE:
            self.setup_tray()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
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
            "auto_start_work": False
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
            "auto_start_work": self.auto_start_work
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def setup_ui(self):
        """Setup the main user interface"""
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main frame
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
        
        # Timer display
        self.timer_label = ttk.Label(main_frame, text="25:00",
                                     font=('Arial', 48, 'bold'))
        self.timer_label.grid(row=2, column=0, columnspan=2, pady=(0, 20))
        
        # Session counter
        self.session_label = ttk.Label(main_frame, text="Session: 0 / 4",
                                       font=('Arial', 10))
        self.session_label.grid(row=3, column=0, columnspan=2, pady=(0, 20))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(0, 20))
        
        self.start_button = ttk.Button(button_frame, text="Start Work",
                                       command=self.toggle_timer, width=12)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.reset_button = ttk.Button(button_frame, text="Reset",
                                       command=self.reset_timer, width=12)
        self.reset_button.grid(row=0, column=1, padx=5)
        
        # Settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        settings_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Create StringVar variables for spinboxes
        self.work_var = tk.StringVar(value=str(self.work_minutes))
        self.break_var = tk.StringVar(value=str(self.break_minutes))
        self.long_break_var = tk.StringVar(value=str(self.long_break_minutes))
        self.sessions_var = tk.StringVar(value=str(self.sessions_until_long_break))
        
        # Work time
        ttk.Label(settings_frame, text="Work time (min):").grid(row=0, column=0, sticky=tk.W)
        self.work_spinbox = ttk.Spinbox(settings_frame, from_=1, to=60, width=10,
                                        textvariable=self.work_var)
        self.work_spinbox.grid(row=0, column=1, padx=(10, 0))
        
        # Break time
        ttk.Label(settings_frame, text="Break time (min):").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.break_spinbox = ttk.Spinbox(settings_frame, from_=1, to=30, width=10,
                                         textvariable=self.break_var)
        self.break_spinbox.grid(row=1, column=1, padx=(10, 0), pady=(5, 0))
        
        # Long break time
        ttk.Label(settings_frame, text="Long break (min):").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        self.long_break_spinbox = ttk.Spinbox(settings_frame, from_=5, to=60, width=10,
                                              textvariable=self.long_break_var)
        self.long_break_spinbox.grid(row=2, column=1, padx=(10, 0), pady=(5, 0))
        
        # Sessions until long break
        ttk.Label(settings_frame, text="Sessions until long break:").grid(row=3, column=0, sticky=tk.W, pady=(5, 0))
        self.sessions_spinbox = ttk.Spinbox(settings_frame, from_=2, to=10, width=10,
                                            textvariable=self.sessions_var)
        self.sessions_spinbox.grid(row=3, column=1, padx=(10, 0), pady=(5, 0))
        
        # Checkboxes frame
        checkbox_frame = ttk.Frame(main_frame)
        checkbox_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Sound checkbox
        self.sound_var = tk.BooleanVar(value=self.sound_enabled)
        ttk.Checkbutton(checkbox_frame, text="Enable sound notifications",
                       variable=self.sound_var).grid(row=0, column=0, sticky=tk.W)
        
        # Auto-start break checkbox
        self.auto_break_var = tk.BooleanVar(value=self.auto_start_break)
        ttk.Checkbutton(checkbox_frame, text="Auto-start breaks",
                       variable=self.auto_break_var).grid(row=1, column=0, sticky=tk.W)
        
        # Auto-start work checkbox
        self.auto_work_var = tk.BooleanVar(value=self.auto_start_work)
        ttk.Checkbutton(checkbox_frame, text="Auto-start work after break",
                       variable=self.auto_work_var).grid(row=2, column=0, sticky=tk.W)
        
        # Minimize to tray checkbox
        if TRAY_AVAILABLE:
            self.tray_var = tk.BooleanVar(value=self.minimize_to_tray)
            ttk.Checkbutton(checkbox_frame, text="Minimize to system tray",
                           variable=self.tray_var).grid(row=3, column=0, sticky=tk.W)
        
        # Save settings button
        ttk.Button(main_frame, text="Save Settings",
                  command=self.save_settings, width=20).grid(row=7, column=0, columnspan=2, pady=(10, 0))
    
    def setup_tray(self):
        """Setup system tray icon"""
        if not TRAY_AVAILABLE:
            return
        
        # Create tray icon image
        def create_image():
            image = Image.new('RGB', (64, 64), color='white')
            draw = ImageDraw.Draw(image)
            draw.ellipse([8, 8, 56, 56], fill='blue')
            return image
        
        # Tray menu
        def show_window():
            self.root.deiconify()
            self.root.lift()
        
        def quit_app():
            self.is_running = False
            if self.timer_thread:
                self.timer_thread.join(timeout=1)
            self.root.quit()
        
        menu = pystray.Menu(
            pystray.MenuItem("Show", show_window, default=True),
            pystray.MenuItem("Start/Stop", self.toggle_timer),
            pystray.MenuItem("Quit", quit_app)
        )
        
        self.tray_icon = pystray.Icon("break_reminder", create_image(), menu=menu)
        
        # Run tray icon in separate thread
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()
    
    def update_display(self):
        """Update the timer display"""
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        self.timer_label.config(text=time_str)
        
        # Update session counter
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
        
        # Start timer thread
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
        self.session_count = 0
        
        # Update settings
        try:
            self.work_minutes = int(self.work_var.get()) if self.work_var.get() else self.work_minutes
        except (ValueError, AttributeError):
            pass  # Keep existing value if there's an error
            
        self.time_left = self.work_minutes * 60
        
        self.start_button.config(text="Start Work")
        self.status_label.config(text="Ready to start working")
        self.update_display()
        
        # Close break window if open
        if self.break_window:
            self.break_window.destroy()
            self.break_window = None
    
    def run_timer(self):
        """Timer loop that runs in a separate thread"""
        while self.is_running and self.time_left > 0:
            time.sleep(1)
            self.time_left -= 1
            
            # Update display in main thread
            self.root.after(0, self.update_display)
        
        if self.is_running and self.time_left == 0:
            # Timer completed
            self.root.after(0, self.on_timer_complete)
    
    def on_timer_complete(self):
        """Handle timer completion"""
        if self.is_break:
            # Break finished
            self.close_break_window()
            self.show_notification("Break Over!", "Time to get back to work!")
            self.is_break = False
            try:
                self.work_minutes = int(self.work_var.get()) if self.work_var.get() else self.work_minutes
            except (ValueError, AttributeError):
                pass  # Keep existing value
            self.time_left = self.work_minutes * 60
            
            if self.auto_work_var.get():
                self.start_timer()
            else:
                self.is_running = False
                self.start_button.config(text="Start Work")
                self.status_label.config(text="Ready to start working")
        else:
            # Work session finished
            self.session_count += 1
            
            # Determine break type
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
            
            self.show_notification("Work Complete!", 
                                 f"Time for a {break_minutes} minute break!")
            self.is_break = True
            self.time_left = break_minutes * 60
            
            # Show break window
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
        
        # Make it stay on top
        self.break_window.attributes('-topmost', True)
        
        # Center the window
        self.break_window.update_idletasks()
        width = self.break_window.winfo_width()
        height = self.break_window.winfo_height()
        x = (self.break_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.break_window.winfo_screenheight() // 2) - (height // 2)
        self.break_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Break content
        title_text = "☕ Long Break Time!" if break_type == "long" else "☕ Break Time!"
        title_label = tk.Label(self.break_window, text=title_text,
                               font=('Arial', 32, 'bold'), bg='#2E7D32', fg='white')
        title_label.pack(pady=(50, 20))
        
        message_label = tk.Label(self.break_window, 
                                text="Time to rest your eyes and stretch!",
                                font=('Arial', 16), bg='#2E7D32', fg='white')
        message_label.pack(pady=(0, 30))
        
        self.break_timer_label = tk.Label(self.break_window, 
                                         text=f"{break_minutes:02d}:00",
                                         font=('Arial', 48, 'bold'), 
                                         bg='#2E7D32', fg='white')
        self.break_timer_label.pack(pady=(0, 40))
        
        # Skip button
        skip_button = tk.Button(self.break_window, text="Skip Break",
                               command=self.skip_break,
                               font=('Arial', 12), padx=20, pady=10)
        skip_button.pack()
        
        # Update break timer
        def update_break_timer():
            if self.is_break and self.is_running and self.break_window:
                minutes = self.time_left // 60
                seconds = self.time_left % 60
                self.break_timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
                self.break_window.after(100, update_break_timer)
        
        update_break_timer()
    
    def close_break_window(self):
        """Close the break window"""
        if self.break_window:
            self.break_window.destroy()
            self.break_window = None
    
    def skip_break(self):
        """Skip the current break"""
        self.close_break_window()
        self.is_running = False
        self.is_break = False
        try:
            self.work_minutes = int(self.work_var.get()) if self.work_var.get() else self.work_minutes
        except (ValueError, AttributeError):
            pass  # Keep existing value
        self.time_left = self.work_minutes * 60
        self.start_button.config(text="Start Work")
        self.status_label.config(text="Break skipped - Ready to work")
        self.update_display()
    
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
        
        # Also play sound if enabled
        if self.sound_var.get():
            self.play_sound()
    
    def play_sound(self):
        """Play a notification sound"""
        try:
            # Use system bell
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
            self.sound_enabled = self.sound_var.get()
            self.auto_start_break = self.auto_break_var.get()
            self.auto_start_work = self.auto_work_var.get()
            
            if TRAY_AVAILABLE:
                self.minimize_to_tray = self.tray_var.get()
            
            self.save_config()
            messagebox.showinfo("Settings Saved", "Your settings have been saved!")
        except ValueError as e:
            messagebox.showerror("Error", "Please enter valid numbers for all time settings")
    
    def on_closing(self):
        """Handle window closing"""
        if TRAY_AVAILABLE and self.tray_var.get() and self.is_running:
            # Minimize to tray instead of closing
            self.root.withdraw()
            if NOTIFICATION_AVAILABLE:
                notification.notify(
                    title="Break Reminder",
                    message="Running in background. Click tray icon to restore.",
                    app_name="Break Reminder",
                    timeout=3
                )
        else:
            # Actually close the application
            self.is_running = False
            if self.timer_thread:
                self.timer_thread.join(timeout=1)
            if self.tray_icon:
                self.tray_icon.stop()
            self.root.quit()
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = BreakReminderApp()
    app.run()