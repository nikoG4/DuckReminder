@echo off
cd /d "%~dp0"
C:\Python312\python.exe -m PyInstaller --noconsole --onefile --name PatoRecordatorio --icon app_icon.ico --hidden-import pystray._win32 --hidden-import pystray._base main.py
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
pause
