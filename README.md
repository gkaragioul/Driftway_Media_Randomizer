https://github.com/user-attachments/assets/c58bc261-bf07-49f2-8623-7cc61c7228aa

<div align="center">

<h1>Driftway Media Randomizer</h1>

<hr>

<p>
  <strong>Open-source randomized media playback for Windows and macOS. Shuffle images and videos from any folder.</strong><br>
  <em>MIT-licensed app source with recursive scanning, VLC-powered Windows playback, keyboard navigation, and Recycle Bin deletes.</em>
</p>

<p>
  <a href="https://github.com/gkaragioul/Driftway_Media_Randomizer/releases/latest">Download</a> &bull;
  <a href="#features">Features</a> &bull;
  <a href="#requirements">Requirements</a> &bull;
  <a href="#building">Building</a> &bull;
  <a href="#license">License</a>
</p>

<hr>

</div>

<p align="center">
  <a href="https://buymeacoffee.com/gkaragioul"><img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black" alt="Buy Me a Coffee"></a><br>
  <sub>Free to download and use. Tips are voluntary and don't buy support or a warranty.</sub>
</p>


## Features

### Media Playback
- **Randomized playback**: Shuffles images and videos with double-pass OS-entropy seeding.
- **Recursive scanning**: Finds supported media inside the selected folder and its subfolders.
- **Wide format support**: JPG, PNG, GIF, WebP, BMP, TIFF, MP4, AVI, MKV, MOV, WMV, FLV, WebM, M4V, 3GP, and more.
- **Aspect-fit images**: Displays photos and artwork cleanly without cropping.
- **Looping video playback**: Uses VLC on Windows for reliable local video playback.

### Workflow
- **Keyboard navigation**: Use right arrow, left arrow, and spacebar for fast browsing.
- **Recoverable deletion**: Delete asks first, then moves the current file to the Recycle Bin.
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
4. Press **Delete** and confirm to move the current file to the Recycle Bin.

## Keyboard Controls

| Key | Action |
|---|---|
| **Right Arrow** | Next media |
| **Left Arrow** | Previous media |
| **Space** | Next media |
| **Delete** | Move current file to the Recycle Bin (asks first) |

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

## Disclaimer

Driftway Media Randomizer is provided as is, without warranty of any kind, under the [MIT License](LICENSE). Use it at your own risk; you are responsible for the files you delete with it.

**Delete** asks before moving the current file to the Recycle Bin (Windows, from version 2.3.3) or the Trash (macOS). Windows versions up to 2.3.2 delete straight away without asking. If you run the Windows source without `send2trash` installed, there is no Recycle Bin fallback: the app warns you and then deletes the file permanently.

## License

Driftway Media Randomizer source code and original project assets are released under the [MIT License](LICENSE).

You may use, copy, modify, merge, publish, distribute, sublicense, and sell copies of the app source, provided the MIT copyright and permission notice are included in copies or substantial portions of the software.

Bundled third-party components, including PySide6, Qt, libVLC, python-vlc, PyInstaller, send2trash, OpenSSL, libffi, the Python runtime, and Microsoft Visual C++ runtime files, retain their respective licenses. See [Windows/assets/THIRD_PARTY_NOTICES.txt](Windows/assets/THIRD_PARTY_NOTICES.txt) for bundled third-party notices.
