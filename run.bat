@echo off
cd /d "%~dp0"
python gui_launcher.py
if errorlevel 1 pause
