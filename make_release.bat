@echo off
REM Build a clean release ZIP for GitHub Releases - double-click this file.
REM Output: release\DalbitViewer-<version>-win64.zip
cd /d "%~dp0"
call build_exe.bat --no-pause
if not exist "dist\DalbitViewer\DalbitViewer.exe" (
  echo.
  echo ERROR: Build failed.
  pause
  exit /b 1
)
for /f "tokens=3" %%v in ('findstr /b "VERSION = " main.py') do set "VERSION=%%~v"
if not defined VERSION (
  echo ERROR: VERSION not found in main.py.
  pause
  exit /b 1
)
set "STAGE=%TEMP%\DalbitViewer_release_%RANDOM%%RANDOM%"
set "ZIP=release\DalbitViewer-%VERSION%-win64.zip"
echo Packaging %ZIP% ...
robocopy "dist\DalbitViewer" "%STAGE%\DalbitViewer" /E /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 (
  echo ERROR: Could not copy the dist folder.
  pause
  exit /b 1
)
REM User settings and logs must not ship in a release.
del /q "%STAGE%\DalbitViewer\settings.json" 2>nul
del /q "%STAGE%\DalbitViewer\viewed_folders.json" 2>nul
del /q "%STAGE%\DalbitViewer\viewer_error.log" 2>nul
if not exist "release" mkdir "release"
if exist "%ZIP%" del /q "%ZIP%"
powershell -NoProfile -Command "Compress-Archive -Path '%STAGE%\DalbitViewer' -DestinationPath '%ZIP%' -CompressionLevel Optimal"
rmdir /s /q "%STAGE%" 2>nul
if not exist "%ZIP%" (
  echo ERROR: ZIP was not created.
  pause
  exit /b 1
)
for %%f in ("%ZIP%") do echo Done: %%f  (%%~zf bytes)
echo Publish with: gh release create v%VERSION% "%ZIP%" --title "DalbitViewer %VERSION%"
pause
