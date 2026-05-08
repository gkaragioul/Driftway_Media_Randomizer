# GKMediaRandomizer

## Project Overview
Cross-platform media viewer (images & videos) that randomizes playback order from a selected folder. Originally a Swift/SwiftUI macOS app, now also available as a Windows desktop app (Python + PySide6) distributed via Inno Setup installer with auto-updates.

## Architecture
- **macOS**: Swift/SwiftUI native app (in `Sources/GKMediaRandomizer/`)
- **Windows**: Python 3 + PySide6 + VLC (in `Windows/`)
  - `gkmedia_randomizer.py` — Main application: UI, media playback, randomization, auto-update system
  - VLC bundled via PyInstaller for video playback
- **Build**: PyInstaller (one-dir) → Inno Setup installer `.exe`
- **Installer**: Inno Setup with EULA, installs to Program Files, creates desktop/start menu shortcuts

## Key Files
- `Windows/gkmedia_randomizer.py` — Main app source (UI, media, randomization, update system)
- `Windows/GKMediaRandomizer.spec` — PyInstaller configuration (one-dir mode with VLC plugins)
- `Windows/installer.iss` — Inno Setup installer script
- `Windows/build.bat` — Build script (PyInstaller → Inno Setup)
- `Windows/assets/license.txt` — Freeware EULA shown during installation (also bundled into the install folder as `LICENSE.txt` and inside the PyInstaller archive for runtime display in About dialog)
- `Windows/assets/THIRD_PARTY_NOTICES.txt` — Open-source attribution for bundled libraries (PySide6, Qt, libVLC, python-vlc, send2trash, OpenSSL, libffi, Python runtime, MS VC Runtime)
- `LICENSE` (repo root) — Mirror of the freeware EULA for GitHub auto-detection
- `Windows/icon.ico` — Application icon

## Build & Run
```bash
cd Windows
pip install PySide6 python-vlc send2trash
python gkmedia_randomizer.py          # Dev mode

build.bat                            # Build installer .exe
# Output: Windows/dist-installer/GKMediaRandomizer_Setup.exe
```

## Version & Updates
- Version is set in `Windows/gkmedia_randomizer.py` → `APP_VERSION` constant
- Update system checks GitHub releases at `karagioules/GKMediaRandomizer_Releases`
- Update flow (matches GKMD pattern):
  1. Check `api.github.com/repos/karagioules/GKMediaRandomizer_Releases/releases/latest`
  2. Compare tag version with current app version
  3. Prompt user with release notes
  4. Download installer to temp (with SHA256 verification if hash in release notes)
  5. Create PowerShell helper script that: waits → runs installer silently (`/VERYSILENT`) → relaunches app
  6. Quit current app, let helper script handle the rest
- Failed update detection: writes pending marker before install, checks on next launch
- Dismissed version tracking: user can skip a version, won't be prompted again (auto-check)
- ETag caching: sends `If-None-Match` header with cached ETag; 304 responses don't count against GitHub rate limit. Cache stored at `%APPDATA%\GKMediaRandomizer\etag_cache.json`
- Version displayed in bottom control bar

## GitHub
- Source repo: `https://github.com/karagioules/Driftplay_RandomMedia_Player` (private source code)
- Releases repo: `https://github.com/karagioules/GKMediaRandomizer_Releases` (public, for auto-updates)
- Releases should contain the Inno Setup `.exe` installer with SHA256 hash in release notes body
- SHA256 format in release notes: `SHA256: <64-char hex>`

## App Branding
- App name: `GKMediaRandomizer`
- App ID (Inno Setup): `{B8F2D3A1-7C4E-4F5A-9B6D-2E8F1A3C5D7E}`
- Desktop shortcut name: `GKMediaRandomizer`
- Config location: `%APPDATA%\GKMediaRandomizer\`

## Features
- Recursive folder scanning for images and videos
- Global shuffle randomization (Fisher-Yates, double-pass with os.urandom entropy)
- Image display with aspect-fit scaling
- Video playback via VLC with auto-looping
- Instant delete to Recycle Bin (no confirmation)
- Keyboard navigation (arrow keys, space, delete)
- Settings persistence (last folder)
- Auto-update from GitHub releases (with SHA256 integrity check)
- Crash logging to Desktop
- Inno Setup installer with EULA, Program Files install, desktop shortcut

## Legacy Files (not part of Windows app)
- `Sources/GKMediaRandomizer/` — macOS SwiftUI version (legacy name)
- `Package.swift` — Swift Package Manager manifest
- `AppIcon.iconset/` — macOS icon assets
