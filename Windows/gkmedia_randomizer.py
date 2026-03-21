#!/usr/bin/env python3
"""
GKMediaRandomizer - Windows app to randomly view images and videos
Rewritten from Swift macOS app for Windows using PyQt5
Distributed as Inno Setup installer with auto-update from GitHub releases.
"""

APP_VERSION = "2.0.1"
REPO_OWNER = "georgekgr12"
REPO_NAME = "GKMediaRandomizer-releases"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"

import sys
import os
import json
import random
import traceback
import platform
import hashlib
import tempfile
import subprocess
from pathlib import Path
from enum import Enum
from collections import defaultdict
from typing import List, Optional, Dict
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QWidget, QFileDialog, QMessageBox, QProgressDialog,
    QStackedWidget, QFrame
)
from PyQt5.QtGui import QPixmap, QImage, QIcon, QFont, QKeySequence
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize

# Configure VLC paths before importing vlc module
import ctypes

def _setup_vlc():
    """Set up VLC library paths for both frozen (PyInstaller) and dev environments."""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = r'C:\Program Files\VideoLAN\VLC'

    if not os.path.isdir(base):
        return

    # Add to DLL search path so libvlccore.dll (dependency of libvlc) is found
    os.environ['PATH'] = base + os.pathsep + os.environ.get('PATH', '')
    if hasattr(os, 'add_dll_directory'):
        os.add_dll_directory(base)

    # Pre-load libvlccore before libvlc (libvlc depends on it)
    ctypes.CDLL(os.path.join(base, 'libvlccore.dll'))

    os.environ['PYTHON_VLC_MODULE_PATH'] = base
    os.environ['PYTHON_VLC_LIB_PATH'] = os.path.join(base, 'libvlc.dll')
    os.environ['VLC_PLUGIN_PATH'] = os.path.join(base, 'plugins')

_setup_vlc()
import vlc


class MediaType(Enum):
    """Enumeration for media types"""
    IMAGE = "image"
    VIDEO = "video"
    UNKNOWN = "unknown"


class RandomizationMode(Enum):
    """Enumeration for randomization modes"""
    GLOBAL_SHUFFLE = "Global"
    FOLDER_BALANCED = "Folder-Balanced"


class MediaItem:
    """Represents a single media item (image or video)"""
    
    def __init__(self, path: Path):
        self.path = path
        self.type = self._determine_type()
    
    def _determine_type(self) -> MediaType:
        """Determine if the file is an image or video"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.ico'}
        video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
        
        ext = self.path.suffix.lower()
        if ext in image_extensions:
            return MediaType.IMAGE
        elif ext in video_extensions:
            return MediaType.VIDEO
        return MediaType.UNKNOWN


class MediaScanner(QThread):
    """Thread for scanning folders to find media files"""
    
    progress = pyqtSignal(str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, folder_path: Path):
        super().__init__()
        self.folder_path = folder_path
        self._is_running = True
    
    def run(self):
        """Scan folder recursively for media files"""
        try:
            media_items = []
            
            if not self.folder_path.exists():
                self.error.emit(f"Folder does not exist: {self.folder_path}")
                return
            
            for file_path in self.folder_path.rglob('*'):
                if not self._is_running:
                    break
                
                if file_path.is_file():
                    item = MediaItem(file_path)
                    if item.type != MediaType.UNKNOWN:
                        media_items.append(item)
                        self.progress.emit(f"Found {len(media_items)} media files...")
            
            if not media_items:
                self.error.emit("No media files found in the selected folder")
            else:
                self.finished.emit(media_items)
        
        except Exception as e:
            self.error.emit(f"Error scanning folder: {str(e)}")
    
    def stop(self):
        """Stop the scanning thread"""
        self._is_running = False


class UpdateChecker(QThread):
    """Thread for checking GitHub releases for updates"""

    result = pyqtSignal(dict)   # update info or empty dict
    error = pyqtSignal(str)

    def __init__(self, is_auto: bool = False):
        super().__init__()
        self.is_auto = is_auto

    def run(self):
        try:
            req = Request(GITHUB_API_URL, headers={
                "User-Agent": f"GKMediaRandomizer/{APP_VERSION}",
                "Accept": "application/vnd.github.v3+json",
            })
            with urlopen(req, timeout=15) as resp:
                release = json.loads(resp.read().decode())

            tag = release.get("tag_name", "")
            if not tag:
                self.result.emit({})
                return

            latest = tag.lstrip("v")
            if not self._is_newer(latest, APP_VERSION):
                self.result.emit({})
                return

            # Find .exe asset (Inno Setup installer)
            assets = release.get("assets", [])
            exe_asset = next((a for a in assets if a["name"].endswith(".exe")), None)
            if not exe_asset:
                self.result.emit({})
                return

            # Extract SHA256 from release body
            body = release.get("body", "")
            import re
            sha_match = re.search(r"SHA256:\s*([a-fA-F0-9]{64})", body, re.IGNORECASE)
            expected_sha = sha_match.group(1).lower() if sha_match else None

            self.result.emit({
                "version": tag,
                "download_url": exe_asset["browser_download_url"],
                "file_name": exe_asset["name"],
                "release_notes": body or "No release notes.",
                "expected_sha256": expected_sha,
                "is_auto": self.is_auto,
            })
        except Exception as e:
            if not self.is_auto:
                msg = str(e)
                if not msg:
                    msg = type(e).__name__
                if hasattr(e, 'code'):
                    msg = f"HTTP {e.code}: {e.reason}" if hasattr(e, 'reason') else f"HTTP {e.code}"
                self.error.emit(msg)
            else:
                self.result.emit({})

    @staticmethod
    def _is_newer(latest: str, current: str) -> bool:
        lp = [int(x) for x in latest.split(".")[:3]]
        cp = [int(x) for x in current.split(".")[:3]]
        while len(lp) < 3: lp.append(0)
        while len(cp) < 3: cp.append(0)
        return lp > cp


class UpdateDownloader(QThread):
    """Thread for downloading an update installer with SHA256 verification"""

    progress = pyqtSignal(int)       # 0-100
    finished = pyqtSignal(str)       # file path on success
    error = pyqtSignal(str)

    def __init__(self, url: str, file_name: str, expected_sha256: Optional[str]):
        super().__init__()
        self.url = url
        self.file_name = file_name
        self.expected_sha256 = expected_sha256

    def run(self):
        try:
            temp_dir = tempfile.gettempdir()
            dest = os.path.join(temp_dir, f"gkmr_{int(datetime.now().timestamp())}_{self.file_name}")

            req = Request(self.url, headers={"User-Agent": f"GKMediaRandomizer/{APP_VERSION}"})
            resp = urlopen(req, timeout=120)
            total = int(resp.headers.get("Content-Length", 0))
            sha = hashlib.sha256()
            downloaded = 0

            with open(dest, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    sha.update(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        self.progress.emit(int(downloaded * 100 / total))

            # Verify SHA256
            actual_sha = sha.hexdigest()
            if self.expected_sha256 and actual_sha != self.expected_sha256:
                try:
                    os.unlink(dest)
                except Exception:
                    pass
                self.error.emit(
                    f"Integrity check failed.\n\n"
                    f"Expected: {self.expected_sha256}\n"
                    f"Actual: {actual_sha}\n\n"
                    f"The file has been deleted for safety."
                )
                return

            self.finished.emit(dest)
        except Exception as e:
            self.error.emit(str(e))


class GKMediaRandomizerApp(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()
        self.media_items: List[MediaItem] = []
        self.current_index = -1
        self.current_folder: Optional[Path] = None
        self.randomization_mode = RandomizationMode.GLOBAL_SHUFFLE
        self.scanner_thread: Optional[MediaScanner] = None
        self._update_checker: Optional[UpdateChecker] = None
        self._update_downloader: Optional[UpdateDownloader] = None
        self.config_file = Path.home() / ".gkmedia_randomizer_config.json"
        self._app_data_dir = Path(os.environ.get("APPDATA", Path.home())) / "GKMediaRandomizer"
        self._app_data_dir.mkdir(parents=True, exist_ok=True)
        self._dismissed_file = self._app_data_dir / "dismissed_update.txt"
        self._pending_file = self._app_data_dir / "pending_update.txt"

        # Load settings
        self.load_settings()

        # Setup UI
        self.init_ui()

        # Setup keyboard shortcuts
        self.setup_shortcuts()

        # Check for failed pending update, then auto-check for new updates
        self._check_pending_update_failed()
        self._cleanup_orphaned_scripts()
        QTimer.singleShot(1500, lambda: self._check_for_updates(is_auto=True))
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("GKMediaRandomizer")
        self.setGeometry(100, 100, 1000, 750)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget to switch between image and video display
        self.media_stack = QStackedWidget()
        self.media_stack.setMinimumSize(QSize(800, 600))
        self.media_stack.setStyleSheet("background-color: black;")

        # Image display (page 0)
        self.media_label = QLabel()
        self.media_label.setStyleSheet("background-color: black;")
        self.media_label.setAlignment(Qt.AlignCenter)
        self.media_stack.addWidget(self.media_label)

        # Video display (page 1) — QFrame for VLC to render into
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        self.media_stack.addWidget(self.video_frame)

        # VLC player
        self.vlc_instance = vlc.Instance('--quiet', '--no-video-title-show')
        self.vlc_player = self.vlc_instance.media_player_new()

        # Timer to detect end-of-media for looping
        self._vlc_poll_timer = QTimer()
        self._vlc_poll_timer.setInterval(250)
        self._vlc_poll_timer.timeout.connect(self._vlc_check_state)

        main_layout.addWidget(self.media_stack)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # File info
        self.info_label = QLabel("Select a folder to start")
        self.info_label.setStyleSheet("color: white; background-color: rgba(0,0,0,0.6); padding: 10px; border-radius: 5px;")
        control_layout.addWidget(self.info_label)
        
        # Folder button
        self.folder_btn = QPushButton("📁 Select Folder")
        self.folder_btn.clicked.connect(self.select_folder)
        control_layout.addWidget(self.folder_btn)
        
        # Randomization mode button
        self.mode_btn = QPushButton(self.randomization_mode.value)
        self.mode_btn.clicked.connect(self.toggle_randomization_mode)
        control_layout.addWidget(self.mode_btn)
        
        # Delete button
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.clicked.connect(self.delete_current_item)
        self.delete_btn.setEnabled(False)
        control_layout.addWidget(self.delete_btn)

        # Version label + update check button
        self.version_label = QLabel(f"v{APP_VERSION}")
        self.version_label.setStyleSheet("color: rgba(255,255,255,0.5); padding: 0 8px; font-size: 11px;")
        control_layout.addWidget(self.version_label)

        self.update_btn = QPushButton("Check for Updates")
        self.update_btn.setStyleSheet("""
            QPushButton { background-color: #37474f; font-size: 11px; padding: 6px 10px; }
            QPushButton:hover { background-color: #455a64; }
        """)
        self.update_btn.clicked.connect(lambda: self._check_for_updates(is_auto=False))
        control_layout.addWidget(self.update_btn)

        main_layout.addLayout(control_layout)
        
        # Set stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: black;
            }
            QPushButton {
                background-color: #0d47a1;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0c3aa3;
            }
            QLabel {
                color: white;
            }
        """)
        
        self.show_welcome_screen()
        self.show()
    
    def show_welcome_screen(self):
        """Show welcome screen when no media is loaded"""
        if not self.media_items:
            self._stop_video()
            self.media_stack.setCurrentIndex(0)
            pixmap = QPixmap(800, 600)
            pixmap.fill(Qt.black)

            self.info_label.setText("No folder selected. Click 'Select Folder' to begin.")
            self.media_label.setPixmap(pixmap)
            self.delete_btn.setEnabled(False)
    
    def select_folder(self):
        """Open folder selection dialog"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select a folder containing images and videos",
            str(Path.home()),
            options=QFileDialog.ShowDirsOnly
        )
        
        if folder_path:
            self.current_folder = Path(folder_path)
            self.scan_folder()
    
    def scan_folder(self):
        """Scan the selected folder for media files"""
        if not self.current_folder:
            return
        
        # Create and start scanner thread
        self.scanner_thread = MediaScanner(self.current_folder)
        self.scanner_thread.progress.connect(self.update_progress)
        self.scanner_thread.finished.connect(self.on_scan_finished)
        self.scanner_thread.error.connect(self.on_scan_error)
        
        # Show progress
        self.info_label.setText(f"Scanning: {self.current_folder.name}...")
        self.media_label.setText("Scanning folder...\nPlease wait...")
        self.scanner_thread.start()
    
    def update_progress(self, message: str):
        """Update progress message"""
        self.info_label.setText(message)
    
    def on_scan_finished(self, items: List[MediaItem]):
        """Handle scan completion"""
        self.media_items = self._apply_randomization(items)
        self.current_index = 0
        self.info_label.setText(f"Loaded {len(self.media_items)} media files")
        self.delete_btn.setEnabled(True)
        self.save_settings()
        self.display_current_media()

    def _apply_randomization(self, items: List[MediaItem]) -> List[MediaItem]:
        """Shuffle items according to the current randomization mode."""
        if not items:
            return items

        if self.randomization_mode == RandomizationMode.FOLDER_BALANCED:
            # Group by parent folder, shuffle within each folder, then
            # interleave folders round-robin so every folder gets fair coverage
            buckets: Dict[Path, List[MediaItem]] = defaultdict(list)
            for item in items:
                buckets[item.path.parent].append(item)

            folder_lists = list(buckets.values())
            for lst in folder_lists:
                random.shuffle(lst)
            random.shuffle(folder_lists)

            result: List[MediaItem] = []
            while folder_lists:
                still_going = []
                for lst in folder_lists:
                    if lst:
                        result.append(lst.pop(0))
                    if lst:
                        still_going.append(lst)
                folder_lists = still_going
            return result
        else:
            # GLOBAL_SHUFFLE: Fisher-Yates via random.shuffle with fresh entropy
            shuffled = list(items)
            random.seed(os.urandom(32))
            random.shuffle(shuffled)
            # Second pass with a different seed breaks up any accidental locality
            random.seed(os.urandom(32))
            random.shuffle(shuffled)
            return shuffled
    
    def on_scan_error(self, error_message: str):
        """Handle scan error"""
        QMessageBox.warning(self, "Error", error_message)
        self.show_welcome_screen()
    
    def display_current_media(self):
        """Display the current media item"""
        if not self.media_items or self.current_index < 0 or self.current_index >= len(self.media_items):
            self.show_welcome_screen()
            return
        
        item = self.media_items[self.current_index]
        file_name = item.path.name
        file_info = f"{self.current_index + 1} / {len(self.media_items)} - {file_name}"
        self.info_label.setText(file_info)
        
        if item.type == MediaType.IMAGE:
            self.display_image(item)
        elif item.type == MediaType.VIDEO:
            self.display_video(item)
    
    def display_image(self, item: MediaItem):
        """Display an image"""
        self._stop_video()
        self.media_stack.setCurrentIndex(0)
        try:
            pixmap = QPixmap(str(item.path))
            if pixmap.isNull():
                self.media_label.setText("Error loading image")
                return
            
            # Scale to fit the label
            label_size = self.media_label.size()
            scaled_pixmap = pixmap.scaled(label_size.width(), label_size.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.media_label.setPixmap(scaled_pixmap)
        except Exception as e:
            self.media_label.setText(f"Error loading image: {str(e)}")
    
    def display_video(self, item: MediaItem):
        """Play a video using VLC"""
        self._stop_video()
        self.media_stack.setCurrentIndex(1)

        # Attach VLC to the video frame's native window handle
        if sys.platform == 'win32':
            self.vlc_player.set_hwnd(int(self.video_frame.winId()))
        else:
            self.vlc_player.set_xwindow(int(self.video_frame.winId()))

        media = self.vlc_instance.media_new(str(item.path))
        self.vlc_player.set_media(media)
        self.vlc_player.play()
        self._vlc_poll_timer.start()

    def _vlc_check_state(self):
        """Poll VLC state to loop video at end"""
        state = self.vlc_player.get_state()
        if state == vlc.State.Ended:
            self.vlc_player.set_position(0)
            self.vlc_player.play()
        elif state == vlc.State.Error:
            self._vlc_poll_timer.stop()
            self.info_label.setText("Playback error: VLC could not play this file")

    def _stop_video(self):
        """Stop any playing video"""
        self._vlc_poll_timer.stop()
        self.vlc_player.stop()
    
    def show_next(self):
        """Show next media item"""
        if not self.media_items:
            return
        
        self.current_index = (self.current_index + 1) % len(self.media_items)
        self.display_current_media()
    
    def show_previous(self):
        """Show previous media item"""
        if not self.media_items:
            return
        
        self.current_index = (self.current_index - 1) % len(self.media_items)
        self.display_current_media()
    
    def toggle_randomization_mode(self):
        """Toggle between randomization modes"""
        if self.randomization_mode == RandomizationMode.GLOBAL_SHUFFLE:
            self.randomization_mode = RandomizationMode.FOLDER_BALANCED
        else:
            self.randomization_mode = RandomizationMode.GLOBAL_SHUFFLE
        
        self.mode_btn.setText(self.randomization_mode.value)
        self.save_settings()
        
        if self.media_items:
            self.scan_folder()
    
    def delete_current_item(self):
        """Delete current item to recycle bin — no confirmation dialog."""
        if not self.media_items or self.current_index < 0:
            return

        item = self.media_items[self.current_index]
        try:
            import send2trash
            send2trash.send2trash(str(item.path))
        except ImportError:
            try:
                os.remove(str(item.path))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete file: {str(e)}")
                return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete file: {str(e)}")
            return

        self.media_items.pop(self.current_index)
        if not self.media_items:
            self.show_welcome_screen()
        else:
            self.current_index = min(self.current_index, len(self.media_items) - 1)
            self.display_current_media()
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Right arrow or Space for next
        self.next_shortcut = self.add_shortcut(Qt.Key_Right, self.show_next)
        self.add_shortcut(Qt.Key_Space, self.show_next)
        
        # Left arrow for previous
        self.prev_shortcut = self.add_shortcut(Qt.Key_Left, self.show_previous)
    
    def add_shortcut(self, key: int, callback):
        """Add a keyboard shortcut"""
        from PyQt5.QtWidgets import QShortcut
        shortcut = QShortcut(QKeySequence(key), self)
        shortcut.activated.connect(callback)
        return shortcut
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key_Right or event.key() == Qt.Key_Space:
            self.show_next()
        elif event.key() == Qt.Key_Left:
            self.show_previous()
        elif event.key() == Qt.Key_Delete:
            self.delete_current_item()
        else:
            super().keyPressEvent(event)
    
    # ── Auto-update system ──────────────────────────────────────

    def _check_pending_update_failed(self):
        """On startup, check if a previous update attempt failed."""
        try:
            if not self._pending_file.exists():
                return
            expected = self._pending_file.read_text(encoding="utf-8").strip()
            self._pending_file.unlink(missing_ok=True)
            if not expected:
                return
            expected_clean = expected.lstrip("v")
            if UpdateChecker._is_newer(expected_clean, APP_VERSION):
                QMessageBox.warning(
                    self, "Update Failed",
                    f"The update to {expected} did not apply successfully.\n"
                    f"You are still running v{APP_VERSION}.\n\n"
                    f"Please try updating again or download manually."
                )
        except Exception:
            pass

    def _cleanup_orphaned_scripts(self):
        """Remove leftover update helper scripts from temp."""
        try:
            tmp = tempfile.gettempdir()
            for f in os.listdir(tmp):
                if f.startswith("gkmr_relaunch_") or f.startswith("gkmr_launcher_"):
                    try:
                        os.unlink(os.path.join(tmp, f))
                    except Exception:
                        pass
        except Exception:
            pass

    def _is_dismissed(self, tag: str) -> bool:
        try:
            if not self._dismissed_file.exists():
                return False
            return self._dismissed_file.read_text(encoding="utf-8").strip() == tag
        except Exception:
            return False

    def _dismiss_version(self, tag: str):
        try:
            self._dismissed_file.write_text(tag, encoding="utf-8")
        except Exception:
            pass

    def _check_for_updates(self, is_auto: bool = False):
        """Start an update check in a background thread."""
        if self._update_checker and self._update_checker.isRunning():
            return
        self._update_is_auto = is_auto
        if not is_auto:
            self.update_btn.setText("Checking...")
            self.update_btn.setEnabled(False)
        self._update_checker = UpdateChecker(is_auto=is_auto)
        self._update_checker.result.connect(self._on_update_check_result)
        self._update_checker.error.connect(self._on_update_check_error)
        self._update_checker.start()

    def _on_update_check_result(self, info: dict):
        self.update_btn.setText("Check for Updates")
        self.update_btn.setEnabled(True)

        if not info:
            if not self._update_is_auto:
                self.version_label.setText(f"v{APP_VERSION} — up to date")
            return

        is_auto = info.get("is_auto", False)
        tag = info["version"]

        # Skip dismissed versions on auto-check
        if is_auto and self._is_dismissed(tag):
            return

        reply = QMessageBox.question(
            self, "Update Available",
            f"A new version is available: {tag}\n\n"
            f"{info.get('release_notes', '')}\n\n"
            f"Download and install now?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self._download_update(info)
        elif is_auto:
            self._dismiss_version(tag)

    def _on_update_check_error(self, error_msg: str):
        self.update_btn.setText("Check for Updates")
        self.update_btn.setEnabled(True)
        QMessageBox.warning(self, "Update Check Failed", f"Could not check for updates:\n{error_msg}")

    def _download_update(self, info: dict):
        """Download the update installer."""
        self.update_btn.setText("Downloading: 0%")
        self.update_btn.setEnabled(False)
        self._pending_update_info = info

        self._update_downloader = UpdateDownloader(
            info["download_url"], info["file_name"], info.get("expected_sha256")
        )
        self._update_downloader.progress.connect(
            lambda pct: self.update_btn.setText(f"Downloading: {pct}%")
        )
        self._update_downloader.finished.connect(self._on_download_finished)
        self._update_downloader.error.connect(self._on_download_error)
        self._update_downloader.start()

    def _on_download_finished(self, file_path: str):
        self.update_btn.setText("Installing update...")
        self._install_update(file_path, self._pending_update_info["version"])

    def _on_download_error(self, error_msg: str):
        self.update_btn.setText("Check for Updates")
        self.update_btn.setEnabled(True)
        QMessageBox.critical(self, "Download Failed", error_msg)

    def _install_update(self, installer_path: str, version: str):
        """Launch installer via PowerShell + VBScript (matches GKMD pattern) and quit."""
        if not os.path.exists(installer_path):
            return

        # Write pending update marker
        try:
            self._pending_file.write_text(version, encoding="utf-8")
        except Exception:
            pass

        app_exe = sys.executable
        tmp = tempfile.gettempdir()
        ts = int(datetime.now().timestamp())

        # PowerShell script: wait → run installer silently with UAC → relaunch
        ps1_path = os.path.join(tmp, f"gkmr_relaunch_{ts}.ps1")
        ps1_lines = [
            "Start-Sleep -Seconds 3",
            f"$proc = Start-Process -FilePath '{installer_path}' -ArgumentList '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART' -Verb RunAs -Wait -PassThru",
            "Start-Sleep -Seconds 2",
            f"if (Test-Path '{app_exe}') {{ Start-Process '{app_exe}' }}",
            f"Remove-Item '{ps1_path}' -Force -ErrorAction SilentlyContinue",
        ]
        with open(ps1_path, "w", encoding="utf-8") as f:
            f.write("\r\n".join(ps1_lines))

        # VBScript launcher for session isolation (UAC + GUI)
        vbs_path = os.path.join(tmp, f"gkmr_launcher_{ts}.vbs")
        vbs_lines = [
            'Set ws = CreateObject("WScript.Shell")',
            f'ws.Run "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File ""{ps1_path}""", 0, True',
            'CreateObject("Scripting.FileSystemObject").DeleteFile WScript.ScriptFullName',
        ]
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write("\r\n".join(vbs_lines))

        # Launch VBScript detached
        subprocess.Popen(
            ["wscript.exe", vbs_path],
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            close_fds=True,
        )

        # Quit app so installer can replace files
        QTimer.singleShot(500, QApplication.instance().quit)

    def save_settings(self):
        """Save application settings"""
        try:
            settings = {
                "last_folder": str(self.current_folder) if self.current_folder else None,
                "randomization_mode": self.randomization_mode.value,
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def load_settings(self):
        """Load application settings"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    settings = json.load(f)
                    
                    if settings.get("last_folder"):
                        last_folder = Path(settings["last_folder"])
                        if last_folder.exists():
                            self.current_folder = last_folder
                    
                    mode_str = settings.get("randomization_mode", "Global")
                    if mode_str == "Folder-Balanced":
                        self.randomization_mode = RandomizationMode.FOLDER_BALANCED
                    else:
                        self.randomization_mode = RandomizationMode.GLOBAL_SHUFFLE
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        self._stop_video()
        if self.scanner_thread and self.scanner_thread.isRunning():
            self.scanner_thread.stop()
            self.scanner_thread.wait()
        
        self.save_settings()
        event.accept()


def _install_crash_handler():
    """Write a detailed crash log to the Desktop on any unhandled exception."""
    desktop = Path.home() / "Desktop"

    def handle_exception(exc_type, exc_value, exc_tb):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_name = f"GKMediaRandomizer_crash_{timestamp}.log"
        log_path = desktop / log_name

        lines = [
            "GKMediaRandomizer — Crash Report",
            "=" * 50,
            f"Time     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Python   : {sys.version}",
            f"Platform : {platform.platform()}",
            f"Exe      : {sys.executable}",
            "",
            f"Exception Type    : {exc_type.__name__}",
            f"Exception Message : {exc_value}",
            "",
            "Traceback (most recent call last):",
            "".join(traceback.format_tb(exc_tb)),
        ]

        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
        except Exception:
            pass  # Never let the crash handler itself crash

        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = handle_exception


def main():
    """Main entry point"""
    _install_crash_handler()

    # Redirect stderr to a log file for the windowed exe so crashes aren't silent
    log_path = Path.home() / ".gkmedia_randomizer_error.log"
    try:
        sys.stderr = open(str(log_path), 'w')
    except Exception:
        pass

    app = QApplication(sys.argv)

    # Set application icon (if exists)
    icon_path = Path(__file__).parent / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Also check next to the exe (for PyInstaller bundled app)
    if getattr(sys, 'frozen', False):
        exe_icon = Path(sys.executable).parent / "icon.ico"
        if exe_icon.exists():
            app.setWindowIcon(QIcon(str(exe_icon)))

    window = GKMediaRandomizerApp()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
