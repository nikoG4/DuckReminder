@echo off
cd /d "%~dp0"
C:\Python312\python.exe -m PyInstaller --noconsole --onefile --name PatoRecordatorio --icon app_icon.ico --add-data "locales;locales" --hidden-import pystray._win32 --hidden-import pystray._base main.py
pause
