# PriveRandomizer - Windows Portable Edition

A modern Windows application to randomly view images and videos from a selected folder and its subfolders.

## ✨ Features

- **Folder Selection**: Choose any folder on your computer to scan for media
- **Recursive Search**: Automatically scans all subfolders for images and videos
- **Random Playback**: Displays media in random order with multiple randomization modes
- **Keyboard Navigation**: Easy navigation with arrow keys
- **Delete to Recycle Bin**: Remove unwanted files directly to the recycle bin
- **Persistent Settings**: Remembers your last selected folder and preferences
- **Modern UI**: Clean, dark interface optimized for media viewing
- **No Installation Required**: Portable executable - just run and go!

## 🎮 Keyboard Controls

| Key | Action |
|-----|--------|
| **→** (Right Arrow) | Next media |
| **←** (Left Arrow) | Previous media |
| **Space** | Next media |

## 🚀 Getting Started

1. **Double-click** `PriveRandomizer.exe` to launch the application
2. Click **"📁 Select Folder"** to choose a folder with images and videos
3. The app will scan the folder and display media randomly
4. Use arrow keys or spacebar to navigate through your media

## 🎯 Supported Media Formats

### Images
- `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.tiff`, `.ico`

### Videos
- `.mp4`, `.avi`, `.mkv`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v`, `.3gp`

## 🔧 Randomization Modes

Click the **randomization mode button** to toggle between:

- **Global**: Shuffles all media items together
- **Folder-Balanced**: Balances media from different subfolders

## 📁 Configuration

Settings are automatically saved in your user directory:
- **Config File**: `~/.prive_randomizer_config.json`

This file stores:
- Last selected folder
- Preferred randomization mode

You can manually delete this file to reset all settings.

## 🛠️ System Requirements

- **OS**: Windows 7 or later (10/11 recommended)
- **Memory**: 500 MB RAM minimum
- **Disk Space**: 50 MB for the application

## 🐛 Troubleshooting

### App won't launch
- Ensure you have Windows 7 or later
- Check that you have sufficient disk space
- Try running as Administrator

### Images won't display
- Verify the image file is not corrupted
- Check that the file format is supported
- Ensure you have read permissions for the file

### Delete function not working
- The file may be in use by another application
- Check that you have write permissions in the folder
- Try closing the file in other applications first

## 📝 Notes

- The application runs entirely offline - no internet connection required
- All media remains on your computer - nothing is uploaded anywhere
- The app respects hidden files if the folder contains any

## 🎨 About the Icon

The application uses a custom icon featuring:
- Play button (media playback)
- Shuffle symbols (random selection)
- Film strip (media content)

## 📦 Portable Edition

This is a fully portable Windows application. You can:
- Copy it to any Windows computer
- Run it from USB drives
- Carry it on portable storage devices
- No installation or registry modifications required

## 📄 License & Credits

**PriveRandomizer** - Private Media Randomizer
- Originally developed as a macOS application in Swift
- Converted to portable Windows application using Python and PyQt5
- Built with PyInstaller for seamless portability

---

**Version**: 1.0 Windows Portable Edition
**Release Date**: March 4, 2026

Enjoy browsing your media collection randomly! 🎬📸
