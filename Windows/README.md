# PriveRandomizer — Windows Portable Edition

A modern Windows application to randomly view images and videos from a selected folder and its subfolders.

## Features

- **Folder Selection**: Choose any folder to scan for media (recursive)
- **Instant Delete**: Press Delete key or click the button — no confirmation dialog, straight to Recycle Bin
- **Randomized Playback**: Two modes — Global Shuffle and Folder-Balanced
- **Keyboard Navigation**: Arrow keys and spacebar
- **Video Playback**: Auto-looping via bundled VLC
- **Crash Logs**: On any crash, a `PriveRandomizer_crash_*.log` file is written to your Desktop
- **Persistent Settings**: Remembers last folder and mode between sessions
- **No Installation Required**: Single portable `.exe`

## Keyboard Controls

| Key | Action |
|---|---|
| **→** Right Arrow | Next media |
| **←** Left Arrow | Previous media |
| **Space** | Next media |
| **Delete** | Move current file to Recycle Bin |

## Getting Started

1. Double-click `PriveRandomizer.exe`
2. Click **Select Folder** to pick a folder with images/videos
3. Navigate with arrow keys or spacebar
4. Press **Delete** to instantly remove a file

## Supported Formats

**Images**: `.jpg` `.jpeg` `.png` `.gif` `.bmp` `.webp` `.tiff` `.ico`

**Videos**: `.mp4` `.avi` `.mkv` `.mov` `.wmv` `.flv` `.webm` `.m4v` `.3gp`

## Randomization Modes

Click the mode button in the toolbar to toggle:

- **Global**: All files shuffled together using OS-entropy seeding (two independent passes)
- **Folder-Balanced**: Each folder is shuffled independently, then folders are interleaved round-robin so every folder gets equal screen time

## Crash Logging

If the app crashes unexpectedly, look on your Desktop for a file named:

```
PriveRandomizer_crash_YYYY-MM-DD_HH-MM-SS.log
```

It contains the exception type, message, full traceback, Python version, and platform info.

## Configuration

Settings are saved automatically to `~/.prive_randomizer_config.json`:

- Last selected folder
- Preferred randomization mode

Delete this file to reset all settings.

## System Requirements

- **OS**: Windows 10 / 11 recommended (Windows 7+ supported)
- **Memory**: 500 MB RAM
- **Disk**: ~65 MB for the application

## Building from Source

```bash
pip install PyQt5 python-vlc send2trash pyinstaller
pyinstaller PriveRandomizer.spec --clean
python deploy.py   # copies exe to Desktop
```

## Troubleshooting

**App won't launch** — Try running as Administrator; check Windows Defender hasn't quarantined the exe.

**Video won't play** — Ensure the file isn't corrupted; VLC codecs are bundled so no separate install is needed.

**Delete not working** — File may be open in another app, or you lack write permissions for that folder.

**Crash on startup** — Check `~/.prive_randomizer_error.log` and any crash log on your Desktop for details.

---

**Version**: 1.1 — 2026-03-20
