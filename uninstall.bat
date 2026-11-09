@echo off
REM Remove DalbitViewer file association (current user).
cd /d "%~dp0"
if exist "dist\DalbitViewer\DalbitViewer.exe" (
  "dist\DalbitViewer\DalbitViewer.exe" --unregister
) else if exist "dist\DalbitViewer.exe" (
  "dist\DalbitViewer.exe" --unregister
) else (
  echo EXE not found, trying with Python...
  python main.py --unregister
)
echo Done. The EXE file itself is kept. Delete the folder to remove everything.
pause
