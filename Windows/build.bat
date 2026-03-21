@echo off
REM Build script for GKMediaRandomizer installer
REM Step 1: PyInstaller one-dir build
REM Step 2: Inno Setup compiler

echo ============================================
echo  GKMediaRandomizer — Build Installer
echo ============================================
echo.

REM Remove old build artifacts
if exist "build\" rmdir /s /q build
if exist "dist\GKMediaRandomizer\" rmdir /s /q "dist\GKMediaRandomizer"
if exist "dist-installer\" rmdir /s /q dist-installer

echo [1/2] Running PyInstaller (one-dir)...
pyinstaller GKMediaRandomizer.spec --clean --noconfirm

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [FAIL] PyInstaller build failed with error code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [OK] PyInstaller build complete.
echo.

REM Check for Inno Setup compiler
where iscc >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    REM Try default install locations
    if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
        set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
    ) else if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
        set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    ) else (
        echo [WARN] Inno Setup compiler (ISCC.exe) not found in PATH.
        echo        Install Inno Setup 6 from https://jrsoftware.org/issetup.php
        echo        The PyInstaller output is in dist\GKMediaRandomizer\
        pause
        exit /b 1
    )
) else (
    set ISCC=iscc
)

echo [2/2] Running Inno Setup compiler...
%ISCC% installer.iss

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [FAIL] Inno Setup build failed with error code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ============================================
echo  Build successful!
echo  Installer: dist-installer\GKMediaRandomizer_Setup_2.0.1.exe
echo ============================================
echo.

REM Generate SHA256 for release notes
echo SHA256 hash for release notes:
certutil -hashfile "dist-installer\GKMediaRandomizer_Setup_2.0.1.exe" SHA256 | findstr /V "hash"
echo.

pause
