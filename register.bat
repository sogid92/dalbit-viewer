@echo off
REM Register DalbitViewer (no Python, no build) - double-click this file.
REM Works from either the DalbitViewer folder itself or its parent folder.
cd /d "%~dp0"
if exist "DalbitViewer.exe" (
  "DalbitViewer.exe" --register
) else if exist "dist\DalbitViewer\DalbitViewer.exe" (
  "dist\DalbitViewer\DalbitViewer.exe" --register
) else if exist "dist\DalbitViewer.exe" (
  "dist\DalbitViewer.exe" --register
) else (
  echo ERROR: DalbitViewer.exe not found.
  echo Put this file in the same folder as DalbitViewer.exe, or in the parent folder of dist.
)
echo.
echo Done. Now double-click an image in Explorer to open it.
pause
