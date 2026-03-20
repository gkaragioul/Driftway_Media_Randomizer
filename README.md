# PriveRandomizer

A portable app to randomly view images and videos from a selected folder and its subfolders. Originally built as a Swift macOS app, now also available as a standalone Windows executable.

## Features

- **Folder selection** with recursive scanning for media files
- **Randomized playback** with two modes: Global Shuffle and Folder-Balanced
- **Keyboard navigation**: Left/Right arrows, Space for next, Delete to remove
- **Instant delete** — moves file to Recycle Bin immediately, no confirmation dialog
- **Video playback** with auto-looping (VLC-powered on Windows)
- **Remembers last folder** and settings between sessions
- **Crash logging** — on any unexpected crash, a detailed log is written to the Desktop

## Platforms

### Windows (`Windows/`)
- Standalone `.exe` built with PyInstaller (PyQt5 + VLC)
- All video codecs supported via bundled VLC libraries
- No installation required — just run the exe

### macOS (`Sources/`)
- Native Swift app using SwiftUI and AVKit
- Requires macOS 12.0+

## Building (Windows)

```bash
pip install PyQt5 python-vlc send2trash pyinstaller
pyinstaller Windows/PriveRandomizer.spec --clean
```

The built exe will be in `Windows/dist/`.

## Usage

1. Launch the app
2. Click **Select Folder** to choose a folder with images/videos
3. Use **Right Arrow** or **Space** to go to the next item
4. Use **Left Arrow** to go to the previous item
5. Press **Delete** to instantly move the current file to the Recycle Bin
6. Toggle **Global / Folder-Balanced** to switch randomization mode

## Randomization Modes

| Mode | Behaviour |
|---|---|
| **Global** | All files from all folders shuffled together using OS-entropy seeding |
| **Folder-Balanced** | Files grouped per folder, each folder shuffled independently, then round-robin interleaved so every folder gets equal coverage |

## Crash Logs

If the app crashes unexpectedly a file named `PriveRandomizer_crash_YYYY-MM-DD_HH-MM-SS.log` is written to your Desktop with the full exception details, Python version, and platform info.

## Changelog

### v1.1 — 2026-03-20
- Crash handler: detailed log dumped to Desktop on any unhandled exception
- Delete is now instant — no confirmation popup, no success popup
- Delete key (keyboard) now triggers deletion
- Global Shuffle: seeded from `os.urandom` with two independent passes for better entropy
- Folder-Balanced mode fully implemented: per-folder shuffle + round-robin interleave

### v1.0 — 2026-03-04
- Initial Windows release (PyQt5 + VLC)
