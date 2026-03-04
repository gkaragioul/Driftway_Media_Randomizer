# PriveRandomizer

A portable app to randomly view images and videos from a selected folder and its subfolders. Originally built as a Swift macOS app, now also available as a standalone Windows executable.

## Features

- **Folder selection** with recursive scanning for media files
- **Randomized playback** of images and videos
- **Two randomization modes**: Global Shuffle and Folder-Balanced
- **Keyboard navigation**: Left/Right arrows, Space for next
- **Video playback** with auto-looping (VLC-powered on Windows)
- **Delete to Recycle Bin** for quick cleanup
- **Remembers last folder** and settings between sessions

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
pip install PyQt5 python-vlc pyinstaller
python -m PyInstaller PriveRandomizer.spec
```

The built exe will be in `Windows/dist/`.

## Usage

1. Launch the app
2. Click **Select Folder** to choose a folder with images/videos
3. Use **Right Arrow** or **Space** to go to the next item
4. Use **Left Arrow** to go to the previous item
5. Click **Global/Folder-Balanced** to toggle randomization mode
6. Click **Delete** to move the current file to the Recycle Bin
