@echo off
REM Install DalbitViewer: build EXE + register file association
REM Double-click this file once. After that, double-clicking an image in Explorer opens it in this viewer.
REM Uses HKCU (current user) only, so no admin rights are needed.
REM NOTE: Always rebuilds the EXE. Old EXE ignored the file path from Explorer
REM and showed only the initial screen, so reusing an old EXE is not allowed.
cd /d "%~dp0"
echo === DalbitViewer install ===
echo Step 1: Build EXE (always rebuild, to match current main.py)...
call build_exe.bat
if not exist "dist\DalbitViewer\DalbitViewer.exe" (
  echo.
  echo ERROR: Build failed. dist\DalbitViewer\DalbitViewer.exe not found.
  pause
  exit /b 1
)
echo.
echo Step 2: Register file association (current user)...
"dist\DalbitViewer\DalbitViewer.exe" --register
if errorlevel 1 (
  echo.
  echo ERROR: Registration failed.
  pause
  exit /b 1
)
echo.
echo Step 3: Opening Settings - Default apps...
echo Pick "DalbitViewer" once in Settings to make it the default viewer.
echo (Windows does not allow programs to change the default app silently.)
start "" "ms-settings:defaultapps"
echo.
echo Done. Now double-click an image in Explorer to open it in the viewer.
echo To undo, run uninstall.bat (in this same folder, NOT in dist).
pause
