https://github.com/user-attachments/assets/c58bc261-bf07-49f2-8623-7cc61c7228aa

<div align="center">

<h1>Driftway Media Randomizer</h1>

<hr>

<p>
  <strong>Free randomized media playback for Windows and macOS. Shuffle images and videos from any folder.</strong><br>
  <em>Recursive scanning, VLC-powered video playback, keyboard navigation, and Recycle Bin deletes.</em>
</p>

<p>
  <a href="#features">Features</a> &bull;
  <a href="#requirements">Requirements</a> &bull;
  <a href="#building">Building</a> &bull;
  <a href="#license">License</a>
</p>

<hr>

</div>

## Features

### Media Playback
- **Randomized playback**: Shuffles images and videos with double-pass OS-entropy seeding.
- **Recursive scanning**: Finds supported media inside the selected folder and its subfolders.
- **Wide format support**: JPG, PNG, GIF, WebP, BMP, TIFF, MP4, AVI, MKV, MOV, WMV, FLV, WebM, M4V, 3GP, and more.
- **Aspect-fit images**: Displays photos and artwork cleanly without cropping.
- **Looping video playback**: Uses VLC on Windows for reliable local video playback.

### Workflow
- **Keyboard navigation**: Use right arrow, left arrow, and spacebar for fast browsing.
- **Recoverable deletion**: Delete moves the current file to the Recycle Bin.
- **Session memory**: Remembers the last selected folder between launches.
- **Simple Windows installer**: Inno Setup installer creates desktop and Start Menu shortcuts.
- **No update prompts**: The app does not check GitHub or offer automatic updates.

## Platforms

| Platform | Stack | Location |
|---|---|---|
| **Windows** | Python 3 + PySide6 + VLC | `Windows/` |
| **macOS** | Swift + SwiftUI + AVKit | `Sources/` |

## Usage

1. Launch Driftway Media Randomizer.
2. Click **Open Folder** to choose a folder with images and videos.
3. Use arrow keys or spacebar to navigate.
4. Press **Delete** to move the current file to the Recycle Bin.

## Keyboard Controls

| Key | Action |
|---|---|
| **Right Arrow** | Next media |
| **Left Arrow** | Previous media |
| **Space** | Next media |
| **Delete** | Move current file to the Recycle Bin |

## Requirements

- Windows 10 or 11 64-bit for the packaged Windows app.
- VLC is bundled in release builds for Windows video playback.
- macOS support is provided by the SwiftUI source in `Sources/`.
- About 65 MB of disk space for the Windows build.

## Building

```bash
cd Windows
pip install PySide6 python-vlc send2trash
python gkmedia_randomizer.py

build.bat
```

The Windows release build creates the installer under `Windows/dist-installer/`.

## License

Driftway Media Randomizer is proprietary freeware. It is free to use for personal and commercial use, but modification, redistribution, resale, and sublicensing require prior written permission from George Karagioules.

See [LICENSE](LICENSE) for the EULA and [Windows/assets/THIRD_PARTY_NOTICES.txt](Windows/assets/THIRD_PARTY_NOTICES.txt) for bundled third-party notices. Bundled third-party components, including PySide6, Qt, libVLC, python-vlc, send2trash, OpenSSL, libffi, and the Python runtime, retain their respective open-source licenses.

For licensing inquiries, email **georgekaragioules@gmail.com**.
