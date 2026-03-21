# GKMediaRandomizer

A cross-platform media viewer that randomizes playback order from a selected folder. Browse your images and videos in a shuffled order — perfect for rediscovering forgotten media, curating collections, or simply enjoying a randomized slideshow.

## Features

- **Randomized media playback** — Shuffle through images and videos with cryptographically seeded randomization (Fisher-Yates, double-pass with OS entropy)
- **Wide format support** — JPG, PNG, GIF, WebP, BMP, TIFF, MP4, AVI, MKV, MOV, WMV, FLV, WebM, M4V, 3GP, and more
- **Recursive folder scanning** — Automatically discovers all media files in subfolders
- **Video playback with auto-looping** — Powered by VLC for reliable, seamless video playback
- **Keyboard-driven navigation** — Arrow keys, spacebar, and delete key for fast, fluid browsing
- **Instant delete to Recycle Bin** — Remove unwanted files on the fly, always recoverable
- **Automatic updates** — SHA256-verified downloads from GitHub releases, silent install, and automatic relaunch
- **Remembers your last session** — Picks up right where you left off
- **Modern dark interface** — Clean, minimal UI that keeps your media front and center
- **Simple Windows installer** — One-click Inno Setup installer with desktop shortcut

## Platforms

| Platform | Stack | Location |
|---|---|---|
| **Windows** | Python 3 + PyQt5 + VLC | `Windows/` |
| **macOS** | Swift + SwiftUI + AVKit | `Sources/` (legacy) |

## Keyboard Controls

| Key | Action |
|---|---|
| **→** Right Arrow | Next media |
| **←** Left Arrow | Previous media |
| **Space** | Next media |
| **Delete** | Move current file to Recycle Bin |

## Getting Started

### Download

Grab the latest installer from [Releases](https://github.com/georgekgr12/GK_MediaRandomizer_Releases/releases/latest).

### Build from Source

```bash
cd Windows
pip install PyQt5 python-vlc Pillow send2trash
python gkmedia_randomizer.py          # Run in dev mode

build.bat                             # Build installer .exe
# Output: Windows/dist-installer/GKMediaRandomizer_Setup.exe
```

## Usage

1. Launch GKMediaRandomizer
2. Click **Select Folder** to choose a folder with images and videos
3. Use arrow keys or spacebar to navigate
4. Press **Delete** to instantly move the current file to the Recycle Bin

## Auto-Update System

The app checks GitHub for new releases on launch:
- Compares the latest release tag with the current app version
- Prompts with release notes before downloading
- Verifies download integrity via SHA256 hash
- Installs silently and relaunches the app
- ETag caching minimizes GitHub API usage

## System Requirements

- **OS**: Windows 10 / 11 (64-bit)
- **Memory**: 512 MB RAM
- **Disk**: ~65 MB

## License

Freeware — see [license.txt](Windows/assets/license.txt) for details.

---

Made by **George Karagioules**
