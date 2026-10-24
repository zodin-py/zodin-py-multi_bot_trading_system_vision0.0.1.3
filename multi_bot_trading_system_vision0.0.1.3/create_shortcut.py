#!/usr/bin/env python3
"""Create desktop shortcut for Multi-Bot Trading System"""
import os
import sys

def create_shortcut():
    try:
        import win32com.client
    except ImportError:
        print("Installing pywin32...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32"])
        import win32com.client

    # Paths
    desktop = os.path.join(os.path.expanduser("~"), "OneDrive - bwv.siwiwissen.de", "Desktop")
    shortcut_path = os.path.join(desktop, "Multi-Bot Trading System.lnk")
    project_dir = r"C:\Users\Zidan Tarawieh\OneDrive - bwv.siwiwissen.de\Dokumente\zodin-py-multi_bot_trading_system_vision0.0.1.3\multi_bot_trading_system_vision0.0.1.3"
    bat_file = os.path.join(project_dir, "start_trading_system.bat")

    # Create shortcut
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.TargetPath = r"C:\Windows\System32\cmd.exe"
    shortcut.Arguments = f'/k cd /d "{project_dir}" && start_trading_system.bat'
    shortcut.WorkingDirectory = project_dir
    shortcut.Description = "Startet das Multi-Bot Trading System (Frontend + Backend)"
    shortcut.IconLocation = r"C:\Windows\System32\cmd.exe,0"
    shortcut.Save()

    print(f"Shortcut created: {shortcut_path}")
    return True

if __name__ == "__main__":
    create_shortcut()