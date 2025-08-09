#!/usr/bin/env python3
"""
Windows Service Wrapper for Break Reminder
This creates a Windows service that auto-starts the break reminder
"""

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import os
import sys
import subprocess
import threading

class BreakReminderService(win32serviceutil.ServiceFramework):
    _svc_name_ = "BreakReminderService"
    _svc_display_name_ = "Break Reminder Service"
    _svc_description_ = "Reminds you to take regular breaks"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.is_running = True
        self.process = None
        
    def SvcStop(self):
        """Stop the service"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_running = False
        if self.process:
            self.process.terminate()
            
    def SvcDoRun(self):
        """Start the service"""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()
        
    def main(self):
        """Main service loop"""
        # Path to your break reminder script
        script_path = r"C:\Users\adeol\standalone-break-reminder.py"
        python_path = sys.executable.replace("python.exe", "pythonw.exe")
        
        # Start the break reminder app
        self.process = subprocess.Popen(
            [python_path, script_path],
            cwd=os.path.dirname(script_path)
        )
        
        # Keep service running
        while self.is_running:
            if win32event.WaitForSingleObject(self.hWaitStop, 1000) == win32event.WAIT_OBJECT_0:
                break
                
        # Cleanup
        if self.process:
            self.process.terminate()
            self.process.wait()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        # Install/start the service
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(BreakReminderService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Command line arguments for installing/removing service
        win32serviceutil.HandleCommandLine(BreakReminderService)