#!/usr/bin/env python3
"""
GKMediaRandomizer - Windows app to randomly view images and videos
Distributed as Inno Setup installer with auto-update from GitHub releases.
"""

APP_VERSION = "2.2.7"
REPO_OWNER = "karagioules"
REPO_NAME = "GKMediaRandomizer"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"

import sys
import os
import re
import json
import random
import traceback
import platform
import hashlib
import tempfile
import subprocess
from pathlib import Path
from enum import Enum
from typing import List, Optional
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QWidget, QFileDialog, QMessageBox, QProgressDialog,
    QStackedWidget, QFrame, QGraphicsDropShadowEffect,
    QDialog, QSizePolicy, QSpacerItem
)
from PySide6.QtGui import (
    QPixmap, QImage, QIcon, QFont, QKeySequence, QColor, QPainter, QShortcut,
)
from PySide6.QtCore import (
    Qt, QTimer, QThread, Signal, QSize, QPropertyAnimation, QEasingCurve, QLockFile,
)

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

    os.environ['PATH'] = base + os.pathsep + os.environ.get('PATH', '')
    if hasattr(os, 'add_dll_directory'):
        os.add_dll_directory(base)

    ctypes.CDLL(os.path.join(base, 'libvlccore.dll'))

    os.environ['PYTHON_VLC_MODULE_PATH'] = base
    os.environ['PYTHON_VLC_LIB_PATH'] = os.path.join(base, 'libvlc.dll')
    os.environ['VLC_PLUGIN_PATH'] = os.path.join(base, 'plugins')

_setup_vlc()
import vlc


# ── Colour palette ───────────────────────────────────────────
BG_DARK      = "#0a0a0a"
BG_SURFACE   = "#161618"
BG_ELEVATED  = "#1e1e22"
BG_HOVER     = "#2a2a30"
ACCENT       = "#6c5ce7"
ACCENT_HOVER = "#7f70f0"
ACCENT_DIM   = "#4a3fb5"
TEXT_PRIMARY  = "#e8e8ec"
TEXT_SECONDARY = "#8e8e96"
TEXT_MUTED    = "#5c5c64"
BORDER       = "#2a2a30"
DANGER       = "#e74c3c"
DANGER_HOVER = "#ff6b5a"
SUCCESS      = "#2ecc71"


# ── Shared stylesheet ────────────────────────────────────────
APP_STYLESHEET = f"""
QMainWindow {{
    background-color: {BG_DARK};
}}
QWidget {{
    font-family: "Segoe UI", system-ui, sans-serif;
    font-size: 13px;
}}
QLabel {{
    color: {TEXT_PRIMARY};
}}
QPushButton {{
    background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    padding: 7px 16px;
    border-radius: 6px;
    font-weight: 500;
    font-size: 12px;
}}
QPushButton:hover {{
    background-color: {BG_HOVER};
    border-color: {TEXT_MUTED};
}}
QPushButton:pressed {{
    background-color: {BG_SURFACE};
}}
QPushButton:disabled {{
    color: {TEXT_MUTED};
    background-color: {BG_SURFACE};
    border-color: {BG_ELEVATED};
}}
QPushButton[accent="true"] {{
    background-color: {ACCENT};
    border: none;
    color: white;
    font-weight: 600;
}}
QPushButton[accent="true"]:hover {{
    background-color: {ACCENT_HOVER};
}}
QPushButton[accent="true"]:pressed {{
    background-color: {ACCENT_DIM};
}}
QPushButton[danger="true"] {{
    background-color: {BG_ELEVATED};
    border: 1px solid {DANGER};
    color: {DANGER};
}}
QPushButton[danger="true"]:hover {{
    background-color: {DANGER};
    color: white;
}}
QMessageBox {{
    background-color: {BG_SURFACE};
}}
QMessageBox QLabel {{
    color: {TEXT_PRIMARY};
    font-size: 13px;
    min-width: 280px;
}}
QMessageBox QPushButton {{
    min-width: 80px;
    padding: 6px 20px;
}}
"""


class MediaType(Enum):
    IMAGE = "image"
    VIDEO = "video"
    UNKNOWN = "unknown"




class MediaItem:
    def __init__(self, path: Path):
        self.path = path
        self.type = self._determine_type()

    def _determine_type(self) -> MediaType:
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.ico'}
        video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
        ext = self.path.suffix.lower()
        if ext in image_extensions:
            return MediaType.IMAGE
        elif ext in video_extensions:
            return MediaType.VIDEO
        return MediaType.UNKNOWN


class MediaScanner(QThread):
    progress = Signal(str)
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, folder_path: Path):
        super().__init__()
        self.folder_path = folder_path
        self._is_running = True

    def run(self):
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
                        if len(media_items) % 50 == 0:
                            self.progress.emit(f"Scanning... {len(media_items)} files found")
            if not media_items:
                self.error.emit("No media files found in the selected folder.")
            else:
                self.finished.emit(media_items)
        except Exception as e:
            self.error.emit(f"Error scanning folder: {str(e)}")

    def stop(self):
        self._is_running = False


class UpdateChecker(QThread):
    result = Signal(dict)
    error = Signal(str)

    def __init__(self, is_auto: bool = False, cache_dir: Optional[Path] = None):
        super().__init__()
        self.is_auto = is_auto
        self._cache_file = (cache_dir / "etag_cache.json") if cache_dir else None

    def _load_cache(self) -> dict:
        try:
            if self._cache_file and self._cache_file.exists():
                return json.loads(self._cache_file.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _save_cache(self, etag: str, data: dict):
        try:
            if self._cache_file:
                self._cache_file.write_text(json.dumps({
                    "etag": etag, "data": data,
                }, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def run(self):
        try:
            cache = self._load_cache()
            headers = {
                "User-Agent": f"GKMediaRandomizer/{APP_VERSION}",
                "Accept": "application/vnd.github.v3+json",
            }
            if cache.get("etag"):
                headers["If-None-Match"] = cache["etag"]

            req = Request(GITHUB_API_URL, headers=headers)
            try:
                with urlopen(req, timeout=15) as resp:
                    etag = resp.headers.get("ETag", "")
                    release = json.loads(resp.read().decode())
                    if etag:
                        self._save_cache(etag, release)
            except URLError as e:
                if hasattr(e, 'code') and e.code == 304:
                    # Not modified — use cached data (doesn't count against rate limit)
                    release = cache.get("data")
                    if not release:
                        self.result.emit({})
                        return
                else:
                    raise

            tag = release.get("tag_name", "")
            if not tag:
                self.result.emit({})
                return

            latest = tag.lstrip("v")
            if not self._is_newer(latest, APP_VERSION):
                self.result.emit({})
                return

            assets = release.get("assets", [])
            exe_asset = next((a for a in assets if a["name"].endswith(".exe")), None)
            if not exe_asset:
                self.result.emit({})
                return

            body = release.get("body", "")
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
                    msg = f"HTTP {e.code}: {getattr(e, 'reason', 'Unknown error')}"
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
    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)

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

            actual_sha = sha.hexdigest()
            if self.expected_sha256 and actual_sha != self.expected_sha256:
                try:
                    os.unlink(dest)
                except Exception:
                    pass
                self.error.emit(
                    f"Integrity check failed.\n\n"
                    f"Expected: {self.expected_sha256}\n"
                    f"Actual:   {actual_sha}\n\n"
                    f"The downloaded file has been deleted for safety."
                )
                return
            self.finished.emit(dest)
        except Exception as e:
            self.error.emit(str(e) or type(e).__name__)


# ── About Dialog ─────────────────────────────────────────────
def _load_license_text() -> str:
    candidates = []
    if getattr(sys, 'frozen', False):
        candidates.append(Path(sys._MEIPASS) / 'license.txt')
        candidates.append(Path(sys.executable).parent / 'license.txt')
        candidates.append(Path(sys.executable).parent / 'LICENSE.txt')
    candidates.append(Path(__file__).parent / 'assets' / 'license.txt')
    for p in candidates:
        try:
            if p.exists():
                return p.read_text(encoding='utf-8')
        except Exception:
            continue
    return "License text not available. See LICENSE.txt installed alongside the application."


def _load_third_party_notices() -> str:
    candidates = []
    if getattr(sys, 'frozen', False):
        candidates.append(Path(sys._MEIPASS) / 'THIRD_PARTY_NOTICES.txt')
        candidates.append(Path(sys.executable).parent / 'THIRD_PARTY_NOTICES.txt')
    candidates.append(Path(__file__).parent / 'assets' / 'THIRD_PARTY_NOTICES.txt')
    for p in candidates:
        try:
            if p.exists():
                return p.read_text(encoding='utf-8')
        except Exception:
            continue
    return "Third-party notices not available."


class AboutDialog(QDialog):
    def __init__(self, parent=None, icon_path: Optional[str] = None):
        super().__init__(parent)
        self.setWindowTitle("About GKMediaRandomizer")
        self.setFixedSize(520, 600)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BG_SURFACE};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(32, 24, 32, 20)

        # App icon
        if icon_path:
            icon_label = QLabel()
            icon_pix = QPixmap(icon_path)
            if not icon_pix.isNull():
                icon_label.setPixmap(icon_pix.scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                icon_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(icon_label)

        # App name
        title = QLabel("GKMediaRandomizer")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Version + author
        ver = QLabel(f"Version {APP_VERSION}  —  by George Karagioules")
        ver.setStyleSheet(f"color: {ACCENT}; font-size: 12px;")
        ver.setAlignment(Qt.AlignCenter)
        layout.addWidget(ver)

        layout.addSpacing(8)

        # Tabbed view: License + Third-Party Notices
        from PySide6.QtWidgets import QTextEdit, QTabWidget
        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                background-color: {BG_DARK};
                border: 1px solid {BORDER};
                border-radius: 6px;
            }}
            QTabBar::tab {{
                background-color: {BG_ELEVATED};
                color: {TEXT_SECONDARY};
                padding: 6px 14px;
                border: 1px solid {BORDER};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                font-size: 11px;
            }}
            QTabBar::tab:selected {{
                background-color: {BG_DARK};
                color: {TEXT_PRIMARY};
            }}
        """)

        text_style = f"""
            QTextEdit {{
                background-color: {BG_DARK};
                color: {TEXT_SECONDARY};
                border: none;
                padding: 10px;
                font-size: 11px;
                font-family: "Segoe UI", sans-serif;
            }}
        """

        eula = QTextEdit()
        eula.setReadOnly(True)
        eula.setPlainText(_load_license_text())
        eula.setStyleSheet(text_style)
        tabs.addTab(eula, "License")

        notices = QTextEdit()
        notices.setReadOnly(True)
        notices.setPlainText(_load_third_party_notices())
        notices.setStyleSheet(text_style)
        tabs.addTab(notices, "Third-Party Notices")

        layout.addWidget(tabs, 1)

        layout.addSpacing(8)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(100)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT};
                border: none;
                color: white;
                font-weight: 600;
                padding: 8px 20px;
                border-radius: 6px;
            }}
            QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}
        """)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)


# ── Main Application ─────────────────────────────────────────
class GKMediaRandomizerApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.media_items: List[MediaItem] = []
        self.current_index = -1
        self.current_folder: Optional[Path] = None
        self.scanner_thread: Optional[MediaScanner] = None
        self._update_checker: Optional[UpdateChecker] = None
        self._update_downloader: Optional[UpdateDownloader] = None
        self._update_is_auto = False
        self._update_dialog_open = False
        self._vlc_media: Optional[object] = None   # keeps VLC media object alive
        self.config_file = Path.home() / ".gkmedia_randomizer_config.json"
        self._app_data_dir = Path(os.environ.get("APPDATA", Path.home())) / "GKMediaRandomizer"
        self._app_data_dir.mkdir(parents=True, exist_ok=True)
        self._dismissed_file = self._app_data_dir / "dismissed_update.txt"
        self._pending_file = self._app_data_dir / "pending_update.txt"

        self.load_settings()
        self._build_ui()
        self._setup_shortcuts()

        self._check_pending_update_failed()
        self._cleanup_orphaned_scripts()
        QTimer.singleShot(2000, lambda: self._check_for_updates(is_auto=True))

    # ── UI Construction ──────────────────────────────────────
    def _build_ui(self):
        self.setWindowTitle("GKMediaRandomizer")
        self.setMinimumSize(900, 650)
        self.resize(1100, 780)
        self.setStyleSheet(APP_STYLESHEET)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar ──────────────────────────────────────────
        top_bar = QWidget()
        top_bar.setFixedHeight(42)
        top_bar.setStyleSheet(f"background-color: {BG_SURFACE}; border-bottom: 1px solid {BORDER};")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 0, 16, 0)
        top_layout.setSpacing(12)

        self.file_counter = QLabel("")
        self.file_counter.setStyleSheet(f"""
            color: {ACCENT};
            font-weight: 600;
            font-size: 12px;
            font-family: "Cascadia Code", "Consolas", monospace;
        """)
        top_layout.addWidget(self.file_counter)

        self.file_name_label = QLabel("")
        self.file_name_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        self.file_name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        top_layout.addWidget(self.file_name_label)

        root.addWidget(top_bar)

        # ── Media area ───────────────────────────────────────
        self.media_stack = QStackedWidget()
        self.media_stack.setStyleSheet(f"background-color: {BG_DARK};")

        # Page 0: Image / Welcome
        self.media_label = QLabel()
        self.media_label.setAlignment(Qt.AlignCenter)
        self.media_label.setStyleSheet(f"background-color: {BG_DARK};")
        self.media_stack.addWidget(self.media_label)

        # Page 1: Video
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet(f"background-color: {BG_DARK};")
        self.media_stack.addWidget(self.video_frame)

        root.addWidget(self.media_stack, 1)

        # VLC
        self.vlc_instance = vlc.Instance('--quiet', '--no-video-title-show')
        self.vlc_player = self.vlc_instance.media_player_new()
        self._vlc_poll_timer = QTimer()
        self._vlc_poll_timer.setInterval(250)
        self._vlc_poll_timer.timeout.connect(self._vlc_check_state)

        # ── Bottom toolbar ───────────────────────────────────
        toolbar = QWidget()
        toolbar.setFixedHeight(56)
        toolbar.setStyleSheet(f"background-color: {BG_SURFACE}; border-top: 1px solid {BORDER};")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(16, 8, 16, 8)
        tb_layout.setSpacing(8)

        # Left group: nav + actions
        self.btn_prev = self._make_btn("  Prev", self.show_previous)
        self.btn_next = self._make_btn("Next  ", self.show_next)
        self.btn_folder = self._make_btn("Open Folder", self.select_folder, accent=True)
        self.btn_delete = self._make_btn("Delete", self.delete_current_item, danger=True)
        self.btn_delete.setEnabled(False)

        tb_layout.addWidget(self.btn_prev)
        tb_layout.addWidget(self.btn_next)
        tb_layout.addSpacing(8)
        tb_layout.addWidget(self.btn_folder)
        tb_layout.addWidget(self.btn_delete)

        tb_layout.addStretch()

        # Right group: version, about, update
        self.version_label = QLabel(f"v{APP_VERSION}")
        self.version_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        tb_layout.addWidget(self.version_label)

        self.btn_about = self._make_btn("About", self._show_about)
        tb_layout.addWidget(self.btn_about)

        self.btn_update = self._make_btn("Check for Updates", lambda: self._check_for_updates(is_auto=False))
        tb_layout.addWidget(self.btn_update)

        root.addWidget(toolbar)

        self._show_welcome()
        self.show()
        self.raise_()
        self.activateWindow()

    def _make_btn(self, text: str, callback, accent=False, danger=False) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        if accent:
            btn.setProperty("accent", True)
        if danger:
            btn.setProperty("danger", True)
        # Force style re-evaluation after setting properties
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        btn.clicked.connect(callback)
        return btn

    # ── Welcome Screen ───────────────────────────────────────
    def _get_icon_path(self) -> Optional[str]:
        """Find the app icon file."""
        candidates = [
            Path(__file__).parent / "icon.png",
            Path(__file__).parent / "icon.ico",
        ]
        if getattr(sys, 'frozen', False):
            candidates.insert(0, Path(sys.executable).parent / "icon.png")
            candidates.insert(1, Path(sys.executable).parent / "icon.ico")
        for p in candidates:
            if p.exists():
                return str(p)
        return None

    def _show_welcome(self):
        self._stop_video()
        self.media_stack.setCurrentIndex(0)
        self.file_counter.setText("")
        self.file_name_label.setText("")
        self.btn_delete.setEnabled(False)

        self.media_label.setText("")
        welcome = QPixmap(self.media_stack.size())
        welcome.fill(QColor(BG_DARK))
        painter = QPainter(welcome)
        painter.setRenderHint(QPainter.Antialiasing)

        # Title
        painter.setPen(QColor(TEXT_PRIMARY))
        painter.setFont(QFont("Segoe UI", 26, QFont.Bold))
        painter.drawText(welcome.rect().adjusted(0, -40, 0, 0), Qt.AlignCenter, "GKMediaRandomizer")

        # Subtitle
        painter.setPen(QColor(TEXT_SECONDARY))
        painter.setFont(QFont("Segoe UI", 13))
        painter.drawText(welcome.rect().adjusted(0, 30, 0, 0), Qt.AlignCenter, 'Click "Open Folder" to load media')

        # Hint
        painter.setPen(QColor(TEXT_MUTED))
        painter.setFont(QFont("Segoe UI", 11))
        painter.drawText(welcome.rect().adjusted(0, 70, 0, 0), Qt.AlignCenter,
                         "Arrow keys to navigate  |  Space for next  |  Del to remove")

        painter.end()
        self.media_label.setPixmap(welcome)

    # ── About Dialog ─────────────────────────────────────────
    def _show_about(self):
        dlg = AboutDialog(self, icon_path=self._get_icon_path())
        dlg.exec()

    # ── Folder & Scanning ────────────────────────────────────
    def select_folder(self):
        start_dir = str(self.current_folder) if self.current_folder and self.current_folder.exists() else str(Path.home())
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select a folder containing images and videos",
            start_dir, options=QFileDialog.ShowDirsOnly
        )
        if folder_path:
            self.current_folder = Path(folder_path)
            self.scan_folder()

    def scan_folder(self):
        if not self.current_folder:
            return
        self.scanner_thread = MediaScanner(self.current_folder)
        self.scanner_thread.progress.connect(lambda msg: self.file_name_label.setText(msg))
        self.scanner_thread.finished.connect(self._on_scan_finished)
        self.scanner_thread.error.connect(self._on_scan_error)
        self.file_name_label.setText(f"Scanning {self.current_folder.name}...")
        self.file_counter.setText("...")
        self.scanner_thread.start()

    def _on_scan_finished(self, items: List[MediaItem]):
        self.media_items = self._apply_randomization(items)
        self.current_index = 0
        self.btn_delete.setEnabled(True)
        self.save_settings()
        self._display_current()

    def _on_scan_error(self, error_message: str):
        QMessageBox.warning(self, "Scan Error", error_message)
        self._show_welcome()

    # ── Randomization ────────────────────────────────────────
    def _apply_randomization(self, items: List[MediaItem]) -> List[MediaItem]:
        if not items:
            return items
        shuffled = list(items)
        random.seed(os.urandom(32))
        random.shuffle(shuffled)
        random.seed(os.urandom(32))
        random.shuffle(shuffled)
        return shuffled

    # ── Media Display ────────────────────────────────────────
    def _display_current(self):
        if not self.media_items or self.current_index < 0 or self.current_index >= len(self.media_items):
            self._show_welcome()
            return

        item = self.media_items[self.current_index]
        self.file_counter.setText(f"{self.current_index + 1} / {len(self.media_items)}")
        self.file_name_label.setText(item.path.name)

        if item.type == MediaType.IMAGE:
            self._display_image(item)
        elif item.type == MediaType.VIDEO:
            self._display_video(item)

    def _display_image(self, item: MediaItem):
        self._stop_video()
        self.media_stack.setCurrentIndex(0)
        try:
            pixmap = QPixmap(str(item.path))
            if pixmap.isNull():
                self.media_label.setText("Could not load image")
                return
            label_size = self.media_label.size()
            scaled = pixmap.scaled(label_size.width(), label_size.height(),
                                   Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.media_label.setPixmap(scaled)
        except Exception as e:
            self.media_label.setText(f"Error: {e}")

    def _display_video(self, item: MediaItem):
        self._stop_video()

        # Wait for VLC to fully stop before issuing new commands (stop() is async)
        for _ in range(20):
            state = self.vlc_player.get_state()
            if state in (vlc.State.Stopped, vlc.State.NothingSpecial, vlc.State.Ended):
                break
            QApplication.processEvents()

        self.media_stack.setCurrentIndex(1)
        if sys.platform == 'win32':
            self.vlc_player.set_hwnd(int(self.video_frame.winId()))
        else:
            self.vlc_player.set_xwindow(int(self.video_frame.winId()))

        # Store as instance variable to prevent Python GC from collecting the wrapper
        self._vlc_media = self.vlc_instance.media_new(str(item.path))
        self.vlc_player.set_media(self._vlc_media)
        self.vlc_player.play()
        self._vlc_poll_timer.start()

    def _vlc_check_state(self):
        state = self.vlc_player.get_state()
        if state == vlc.State.Ended:
            self.vlc_player.set_position(0)
            self.vlc_player.play()
        elif state == vlc.State.Error:
            self._vlc_poll_timer.stop()
            self.file_name_label.setText("Playback error")

    def _stop_video(self):
        self._vlc_poll_timer.stop()
        self.vlc_player.stop()
        self._vlc_media = None

    # ── Navigation ───────────────────────────────────────────
    def show_next(self):
        if not self.media_items:
            return
        self.current_index = (self.current_index + 1) % len(self.media_items)
        self._display_current()

    def show_previous(self):
        if not self.media_items:
            return
        self.current_index = (self.current_index - 1) % len(self.media_items)
        self._display_current()

    def delete_current_item(self):
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
                QMessageBox.critical(self, "Delete Failed", f"Could not delete file:\n{e}")
                return
        except Exception as e:
            QMessageBox.critical(self, "Delete Failed", f"Could not delete file:\n{e}")
            return
        self.media_items.pop(self.current_index)
        if not self.media_items:
            self._show_welcome()
        else:
            self.current_index = min(self.current_index, len(self.media_items) - 1)
            self._display_current()

    # ── Shortcuts ────────────────────────────────────────────
    def _setup_shortcuts(self):
        for key, fn in [
            (Qt.Key_Right, self.show_next),
            (Qt.Key_Space, self.show_next),
            (Qt.Key_Left, self.show_previous),
        ]:
            s = QShortcut(QKeySequence(key), self)
            s.activated.connect(fn)

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_Right, Qt.Key_Space):
            self.show_next()
        elif key == Qt.Key_Left:
            self.show_previous()
        elif key == Qt.Key_Delete:
            self.delete_current_item()
        else:
            super().keyPressEvent(event)

    # ── Auto-update system ───────────────────────────────────
    def _check_pending_update_failed(self):
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
        # Don't stack: skip if a checker is in flight, a dialog is up, or a
        # download/install is in progress.
        if self._update_checker and self._update_checker.isRunning():
            return
        if self._update_dialog_open:
            return
        if self._update_downloader and self._update_downloader.isRunning():
            return
        # Disconnect the previous checker's signals so a queued stale result
        # can't fire a second dialog while a fresh check is in flight.
        if self._update_checker is not None:
            try:
                self._update_checker.result.disconnect(self._on_update_check_result)
                self._update_checker.error.disconnect(self._on_update_check_error)
            except (RuntimeError, TypeError):
                pass
        self._update_is_auto = is_auto
        # Disable the button immediately so a click can't enqueue a parallel
        # manual check while the auto-check's signal is in transit.
        self.btn_update.setEnabled(False)
        if not is_auto:
            self.btn_update.setText("Checking...")
        self._update_checker = UpdateChecker(is_auto=is_auto, cache_dir=self._app_data_dir)
        self._update_checker.result.connect(self._on_update_check_result)
        self._update_checker.error.connect(self._on_update_check_error)
        self._update_checker.start()

    def _on_update_check_result(self, info: dict):
        self.btn_update.setText("Check for Updates")
        self.btn_update.setEnabled(True)

        # If a dialog is already up (from a prior result that's still being
        # responded to in a nested event loop), ignore this stale signal.
        if self._update_dialog_open:
            return

        if not info:
            if not self._update_is_auto:
                self.version_label.setText(f"v{APP_VERSION} — up to date")
            return

        is_auto = info.get("is_auto", False)
        tag = info["version"]

        if is_auto and self._is_dismissed(tag):
            return

        self._update_dialog_open = True
        try:
            reply = QMessageBox.question(
                self, "Update Available",
                f"A new version is available: {tag}\n\n"
                f"{info.get('release_notes', '')}\n\n"
                f"Download and install now?",
                QMessageBox.Yes | QMessageBox.No,
            )
        finally:
            self._update_dialog_open = False

        if reply == QMessageBox.Yes:
            self._download_update(info)
        elif is_auto:
            self._dismiss_version(tag)

    def _on_update_check_error(self, error_msg: str):
        self.btn_update.setText("Check for Updates")
        self.btn_update.setEnabled(True)
        QMessageBox.warning(
            self, "Update Check Failed",
            f"Could not check for updates:\n\n{error_msg}"
        )

    def _download_update(self, info: dict):
        self.btn_update.setText("Downloading: 0%")
        self.btn_update.setEnabled(False)
        self._pending_update_info = info
        self._update_downloader = UpdateDownloader(
            info["download_url"], info["file_name"], info.get("expected_sha256")
        )
        self._update_downloader.progress.connect(
            lambda pct: self.btn_update.setText(f"Downloading: {pct}%")
        )
        self._update_downloader.finished.connect(self._on_download_finished)
        self._update_downloader.error.connect(self._on_download_error)
        self._update_downloader.start()

    def _on_download_finished(self, file_path: str):
        self.btn_update.setText("Installing...")
        self._install_update(file_path, self._pending_update_info["version"])

    def _on_download_error(self, error_msg: str):
        self.btn_update.setText("Check for Updates")
        self.btn_update.setEnabled(True)
        QMessageBox.critical(self, "Download Failed", error_msg)

    def _install_update(self, installer_path: str, version: str):
        if not os.path.exists(installer_path):
            return
        try:
            self._pending_file.write_text(version, encoding="utf-8")
        except Exception:
            pass

        app_exe = sys.executable
        tmp = tempfile.gettempdir()
        ts = int(datetime.now().timestamp())

        log_path = os.path.join(tmp, f"gkmr_update_{ts}.log")
        ps1_path = os.path.join(tmp, f"gkmr_relaunch_{ts}.ps1")

        # PowerShell helper. Writes a timestamped log so failures are diagnosable.
        # Uses -PassThru + WaitForExit() (more reliable than -Wait with -Verb RunAs)
        # and polls Test-Path + a non-locked file check for up to 30s before launch.
        ps1_script = f"""$ErrorActionPreference = 'Continue'
function Log {{ param($m) "$([DateTime]::Now.ToString('HH:mm:ss.fff')) $m" | Out-File -FilePath '{log_path}' -Append -Encoding utf8 }}

Log "Helper starting (pid $PID)"
Start-Sleep -Seconds 3

try {{
    Log "Launching installer (elevated): {installer_path}"
    $proc = Start-Process -FilePath '{installer_path}' -ArgumentList '/SILENT','/SUPPRESSMSGBOXES','/NORESTART' -Verb RunAs -PassThru -ErrorAction Stop
    $proc.WaitForExit()
    Log "Installer exited with code $($proc.ExitCode)"
}} catch {{
    Log "Installer launch failed: $_"
    Remove-Item '{ps1_path}' -Force -ErrorAction SilentlyContinue
    exit 1
}}

# Wait up to 30s for the new app exe to exist AND not be file-locked by Inno Setup.
$found = $false
for ($i = 0; $i -lt 60; $i++) {{
    if (Test-Path '{app_exe}') {{
        try {{
            $f = [IO.File]::Open('{app_exe}', 'Open', 'Read', 'ReadWrite')
            $f.Close()
            $found = $true
            Log "App exe ready after $($i * 500)ms"
            break
        }} catch {{ }}
    }}
    Start-Sleep -Milliseconds 500
}}

if ($found) {{
    Log "Relaunching: {app_exe}"
    Start-Process '{app_exe}'
    Log "Relaunch issued"
}} else {{
    Log "App exe never became available; skipping relaunch"
}}

Remove-Item '{ps1_path}' -Force -ErrorAction SilentlyContinue
"""
        with open(ps1_path, "w", encoding="utf-8") as f:
            f.write(ps1_script)

        vbs_path = os.path.join(tmp, f"gkmr_launcher_{ts}.vbs")
        vbs_lines = [
            'Set ws = CreateObject("WScript.Shell")',
            f'ws.Run "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File ""{ps1_path}""", 0, True',
            'CreateObject("Scripting.FileSystemObject").DeleteFile WScript.ScriptFullName',
        ]
        with open(vbs_path, "w", encoding="utf-8") as f:
            f.write("\r\n".join(vbs_lines))

        subprocess.Popen(
            ["wscript.exe", vbs_path],
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            close_fds=True,
        )
        QTimer.singleShot(500, QApplication.instance().quit)

    # ── Settings ─────────────────────────────────────────────
    def save_settings(self):
        try:
            settings = {
                "last_folder": str(self.current_folder) if self.current_folder else None,
            }
            with open(self.config_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception:
            pass

    def load_settings(self):
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    settings = json.load(f)
                    if settings.get("last_folder"):
                        last_folder = Path(settings["last_folder"])
                        if last_folder.exists():
                            self.current_folder = last_folder
        except Exception:
            pass

    def closeEvent(self, event):
        self._stop_video()
        if self.scanner_thread and self.scanner_thread.isRunning():
            self.scanner_thread.stop()
            self.scanner_thread.wait()
        self.save_settings()
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Re-render welcome screen on resize if no media loaded
        if not self.media_items:
            self._show_welcome()


# ── Crash handler ────────────────────────────────────────────
def _install_crash_handler():
    desktop = Path.home() / "Desktop"

    def handle_exception(exc_type, exc_value, exc_tb):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_path = desktop / f"GKMediaRandomizer_crash_{timestamp}.log"
        lines = [
            "GKMediaRandomizer — Crash Report",
            "=" * 50,
            f"Time     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Version  : {APP_VERSION}",
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
            pass
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = handle_exception


def main():
    _install_crash_handler()
    log_path = Path.home() / ".gkmedia_randomizer_error.log"
    try:
        sys.stderr = open(str(log_path), 'w')
    except Exception:
        pass

    app = QApplication(sys.argv)

    # Single-instance guard: if the auto-update helper fires its relaunch
    # late while the user has already manually opened the app, the second
    # instance exits silently instead of stacking another window.
    _lock_dir = Path(os.environ.get("APPDATA", Path.home())) / "GKMediaRandomizer"
    _lock_dir.mkdir(parents=True, exist_ok=True)
    _lock = QLockFile(str(_lock_dir / "app.lock"))
    _lock.setStaleLockTime(5000)
    if not _lock.tryLock(0):
        return

    icon_path = Path(__file__).parent / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    if getattr(sys, 'frozen', False):
        exe_icon = Path(sys.executable).parent / "icon.ico"
        if exe_icon.exists():
            app.setWindowIcon(QIcon(str(exe_icon)))

    window = GKMediaRandomizerApp()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
