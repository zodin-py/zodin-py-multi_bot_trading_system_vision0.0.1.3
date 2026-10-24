Set shell = CreateObject("WScript.Shell")
Set shortcut = shell.CreateShortcut("C:\Users\Zidan Tarawieh\OneDrive - bwv.siwiwissen.de\Desktop\Multi-Bot Trading System.lnk")
shortcut.TargetPath = "cmd.exe"
shortcut.Arguments = "/c ""C:\Users\Zidan Tarawieh\OneDrive - bwv.siwiwissen.de\Dokumente\zodin-py-multi_bot_trading_system_vision0.0.1.3\multi_bot_trading_system_vision0.0.1.3\start_trading_system.bat"""
shortcut.WorkingDirectory = "C:\Users\Zidan Tarawieh\OneDrive - bwv.siwiwissen.de\Dokumente\zodin-py-multi_bot_trading_system_vision0.0.1.3\multi_bot_trading_system_vision0.0.1.3"
shortcut.Description = "Startet das Multi-Bot Trading System (Frontend + Backend)"
shortcut.IconLocation = "C:\Windows\System32\cmd.exe,0"
shortcut.Save
WScript.Echo "Shortcut created successfully!"