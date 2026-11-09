@echo off
REM Build standalone EXE on Windows - double-click this file
REM If Python is not installed, install Python 3.10+ first from https://www.python.org/downloads/
REM and check "Add python.exe to PATH" during install.
cd /d "%~dp0"
REM Preserve user data across the rebuild (PyInstaller removes dist\DalbitViewer).
set "BACKUP=%TEMP%\DalbitViewer_build_backup_%RANDOM%%RANDOM%"
mkdir "%BACKUP%" 2>nul
if exist "dist\DalbitViewer\settings.json" copy /y "dist\DalbitViewer\settings.json" "%BACKUP%\" >nul
if exist "dist\DalbitViewer\viewed_folders.json" copy /y "dist\DalbitViewer\viewed_folders.json" "%BACKUP%\" >nul
echo Installing Pillow and PyInstaller...
python -m pip install --upgrade Pillow pyinstaller
if errorlevel 1 (
  echo python command failed, trying py launcher...
  py -3 -m pip install --upgrade Pillow pyinstaller
)
if errorlevel 1 (
  echo.
  echo ERROR: Python was not found. Install Python 3.10+ with "Add python.exe to PATH" checked, then run this file again.
  pause
  exit /b 1
)
echo Building EXE...
python -m PyInstaller --noconfirm --onedir --windowed --exclude-module numpy --name "DalbitViewer" --icon icon.ico main.py
if errorlevel 1 (
  echo Trying with py launcher...
  py -3 -m PyInstaller --noconfirm --onedir --windowed --exclude-module numpy --name "DalbitViewer" --icon icon.ico main.py
)
if errorlevel 1 (
  echo.
  echo ERROR: Build failed. Your settings backup is at "%BACKUP%".
  pause
  exit /b 1
)
if not exist "dist\DalbitViewer\DalbitViewer.exe" (
  echo.
  echo ERROR: Build failed. Your settings backup is at "%BACKUP%".
  pause
  exit /b 1
)
if exist "%BACKUP%\settings.json" copy /y "%BACKUP%\settings.json" "dist\DalbitViewer\" >nul
if exist "%BACKUP%\viewed_folders.json" copy /y "%BACKUP%\viewed_folders.json" "dist\DalbitViewer\" >nul
rmdir /s /q "%BACKUP%"
echo.
echo Done: dist\DalbitViewer\DalbitViewer.exe (onedir: start faster, no extraction)
if /i not "%~1"=="--no-pause" pause
