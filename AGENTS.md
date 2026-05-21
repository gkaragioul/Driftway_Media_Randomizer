# Driftway Media Randomizer

## Project Overview
Cross-platform media viewer (images & videos) that randomizes playback order from a selected folder. Product name: **Driftway Media Randomizer**. Windows desktop app uses Python + PySide6 and is distributed via Inno Setup installer without automatic updates.

## Architecture
- **macOS**: Swift/SwiftUI native app (in `Sources/DriftwayMediaRandomizer/`)
- **Windows**: Python 3 + PySide6 + VLC (in `Windows/`)
  - `gkmedia_randomizer.py` - Main application: UI, media playback, randomization
  - VLC bundled via PyInstaller for video playback
- **Build**: PyInstaller (one-dir) -> Inno Setup installer `.exe`
- **Installer**: Inno Setup with EULA, installs to Program Files, creates desktop/start menu shortcuts

## Key Files
- `Windows/gkmedia_randomizer.py` - Main app source (UI, media, randomization)
- `Windows/DriftwayMediaRandomizer.spec` - PyInstaller configuration (one-dir mode with VLC plugins)
- `Windows/installer.iss` - Inno Setup installer script
- `Windows/build.bat` - Build script (PyInstaller -> Inno Setup)
- `Windows/assets/license.txt` - Freeware EULA shown during installation (also bundled into the install folder as `LICENSE.txt` and inside the PyInstaller archive for runtime display in About dialog)
- `Windows/assets/THIRD_PARTY_NOTICES.txt` - Open-source attribution for bundled libraries (PySide6, Qt, libVLC, python-vlc, send2trash, OpenSSL, libffi, Python runtime, MS VC Runtime)
- `LICENSE` (repo root) - Mirror of the freeware EULA for GitHub auto-detection
- `Windows/icon.ico` - Application icon

## Build & Run
```bash
cd Windows
pip install PySide6 python-vlc send2trash
python gkmedia_randomizer.py          # Dev mode

build.bat                            # Build installer .exe
# Output: Windows/dist-installer/Driftway_Media_Randomizer_Setup.exe
```

## Version
- Version is set in `Windows/gkmedia_randomizer.py` -> `APP_VERSION` constant
- Version displayed in bottom control bar

## GitHub
- Owner profile: `https://github.com/gkaragioul`
- The app does not contact GitHub or offer update prompts.

## App Branding
- App name: `Driftway Media Randomizer`
- App ID (Inno Setup): `{B8F2D3A1-7C4E-4F5A-9B6D-2E8F1A3C5D7E}`
- Desktop shortcut name: `Driftway Media Randomizer`
- Config location: `%APPDATA%\DriftwayMediaRandomizer\`

## Features
- Recursive folder scanning for images and videos
- Global shuffle randomization (Fisher-Yates, double-pass with os.urandom entropy)
- Image display with aspect-fit scaling
- Video playback via VLC with auto-looping
- Instant delete to Recycle Bin (no confirmation)
- Keyboard navigation (arrow keys, space, delete)
- Settings persistence (last folder)
- Crash logging to Desktop
- Inno Setup installer with EULA, Program Files install, desktop shortcut

## Legacy Files
- `Package.swift` - Swift Package Manager manifest for the macOS SwiftUI version
- `AppIcon.iconset/` - macOS icon assets
