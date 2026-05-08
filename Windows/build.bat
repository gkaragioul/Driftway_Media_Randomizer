@echo off
REM Build script for Driftway Media Randomizer installer
REM Step 1: PyInstaller one-dir build
REM Step 2: Inno Setup compiler

echo ============================================
echo  Driftway Media Randomizer - Build Installer
echo ============================================
echo.

REM Remove old build artifacts
if exist "build\" rmdir /s /q build
if exist "dist\DriftwayMediaRandomizer\" rmdir /s /q "dist\DriftwayMediaRandomizer"
if exist "dist-installer\" rmdir /s /q dist-installer

echo [1/2] Running PyInstaller (one-dir)...
pyinstaller DriftwayMediaRandomizer.spec --clean --noconfirm

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [FAIL] PyInstaller build failed with error code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [OK] PyInstaller build complete.
echo.

REM Locate Inno Setup compiler (avoid nested else-if; CMD mis-parses paths with parens)
set "ISCC="
where iscc >nul 2>&1
if %ERRORLEVEL% EQU 0 set "ISCC=iscc"
if not defined ISCC if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC (
    echo [WARN] Inno Setup compiler ^(ISCC.exe^) not found.
    echo        Install Inno Setup 6 from https://jrsoftware.org/issetup.php
    echo        The PyInstaller output is in dist\DriftwayMediaRandomizer\
    pause
    exit /b 1
)

echo [2/2] Running Inno Setup compiler...
"%ISCC%" installer.iss

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [FAIL] Inno Setup build failed with error code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ============================================
echo  Build successful!
echo  Installer: dist-installer\Driftway_Media_Randomizer_Setup.exe
echo ============================================
echo.

REM Generate SHA256 for release notes
echo SHA256 hash for release notes:
certutil -hashfile "dist-installer\Driftway_Media_Randomizer_Setup.exe" SHA256 | findstr /V "hash"
echo.

pause
