<p align="center">
  <img src="GKMediaRandomizer.png" alt="GKMediaRandomizer logo" width="128">
</p>

<h1 align="center">GKMediaRandomizer</h1>

<p align="center">
  <strong>Cross-platform media viewer that randomizes playback from a selected folder.</strong><br>
  Browse images and videos in a shuffled, keyboard-friendly viewer.
</p>

<p align="center">
  <a href="#features">Features</a> -
  <a href="#usage">Usage</a> -
  <a href="#keyboard-controls">Controls</a> -
  <a href="#build-from-source">Build</a> -
  <a href="#license">License</a>
</p>

![Windows](https://img.shields.io/badge/Windows-10+-0078D6.svg)
![macOS](https://img.shields.io/badge/macOS-SwiftUI-000000.svg)
![License](https://img.shields.io/badge/License-Freeware-red.svg)

## Overview

GKMediaRandomizer is a media viewer for rediscovering images and videos from a selected folder. It scans media recursively, shuffles playback order, supports fast keyboard navigation, and keeps deletion recoverable by moving files to the Recycle Bin.

## Features

- **Randomized media playback**: Shuffle images and videos with double-pass OS-entropy seeding
- **Wide format support**: JPG, PNG, GIF, WebP, BMP, TIFF, MP4, AVI, MKV, MOV, WMV, FLV, WebM, M4V, 3GP, and more
- **Recursive folder scanning**: Discovers media files inside subfolders
- **Video playback with auto-looping**: Powered by VLC for reliable playback
- **Keyboard-driven navigation**: Arrow keys, spacebar, and delete key for fast browsing
- **Instant delete to Recycle Bin**: Remove unwanted files while keeping them recoverable
- **Session memory**: Picks up from the last selected folder
- **Simple Windows installer**: Inno Setup installer with desktop and Start Menu shortcuts

## Platforms

| Platform | Stack | Location |
|---|---|---|
| **Windows** | Python 3 + PySide6 + VLC | `Windows/` |
| **macOS** | Swift + SwiftUI + AVKit | `Sources/` |

## Usage

1. Launch GKMediaRandomizer.
2. Click **Open Folder** to choose a folder with images and videos.
3. Use arrow keys or spacebar to navigate.
4. Press **Delete** to move the current file to the Recycle Bin.

## Keyboard Controls

| Key | Action |
|---|---|
| **Right Arrow** | Next media |
| **Left Arrow** | Previous media |
| **Space** | Next media |
| **Delete** | Move current file to Recycle Bin |

## Build From Source

```bash
cd Windows
pip install PySide6 python-vlc send2trash
python gkmedia_randomizer.py

build.bat
```

## System Requirements

- **OS**: Windows 10 / 11 64-bit
- **Memory**: 512 MB RAM
- **Disk**: About 65 MB

## License

GKMediaRandomizer is proprietary freeware. It is free to use for personal and commercial use, but modification, redistribution, resale, and sublicensing require prior written permission from George Karagioules.

See [LICENSE](LICENSE) for the EULA and [Windows/assets/THIRD_PARTY_NOTICES.txt](Windows/assets/THIRD_PARTY_NOTICES.txt) for bundled third-party notices. Bundled third-party components, including PySide6, Qt, libVLC, python-vlc, send2trash, OpenSSL, libffi, and the Python runtime, retain their respective open-source licenses.

For licensing inquiries, open an issue at https://github.com/gkaragioul/Driftway_Media_Randomizer.
