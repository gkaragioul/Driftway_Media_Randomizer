@echo off
REM Build script for PriveRandomizer portable app
REM This creates a single executable file that includes all dependencies

echo Building PriveRandomizer portable app...
echo.

REM Remove old build artifacts
if exist "build\" rmdir /s /q build
if exist "dist\" rmdir /s /q dist
if exist "*.spec" del *.spec

echo [*] Running PyInstaller...
pyinstaller --onefile --windowed ^
    --name "PriveRandomizer" ^
    --icon "icon.ico" ^
    --add-data "icon.ico;." ^
    --add-data "icon.png;." ^
    --distpath "dist" ^
    --buildpath "build" ^
    prive_randomizer.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [✓] Build successful!
    echo [✓] Executable location: dist\PriveRandomizer.exe
    echo.
    echo [*] Copying to desktop...
    copy "dist\PriveRandomizer.exe" "%USERPROFILE%\Desktop\" >nul 2>&amp;1
    copy "icon.ico" "%USERPROFILE%\Desktop\PriveRandomizer.ico" >nul 2>&amp;1
    echo [✓] Application exported to desktop!
    echo.
) else (
    echo.
    echo [✗] Build failed with error code %ERRORLEVEL%
    pause
)

pause
