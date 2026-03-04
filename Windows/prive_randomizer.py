#!/usr/bin/env python3
"""
PriveRandomizer - A portable Windows app to randomly view images and videos
Rewritten from Swift macOS app for Windows using PyQt5
"""

import sys
import os
import json
import random
from pathlib import Path
from enum import Enum
from typing import List, Optional, Dict
from datetime import datetime

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


class PriveRandomizerApp(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.media_items: List[MediaItem] = []
        self.current_index = -1
        self.current_folder: Optional[Path] = None
        self.randomization_mode = RandomizationMode.GLOBAL_SHUFFLE
        self.scanner_thread: Optional[MediaScanner] = None
        self.config_file = Path.home() / ".prive_randomizer_config.json"
        
        # Load settings
        self.load_settings()
        
        # Setup UI
        self.init_ui()
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("PriveRandomizer")
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
        self.media_items = items
        
        # Apply randomization
        if self.randomization_mode == RandomizationMode.GLOBAL_SHUFFLE:
            random.shuffle(self.media_items)
        
        self.current_index = 0
        self.info_label.setText(f"Loaded {len(self.media_items)} media files")
        self.delete_btn.setEnabled(True)
        self.save_settings()
        
        self.display_current_media()
    
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
        """Delete current item to recycle bin"""
        if not self.media_items or self.current_index < 0:
            return
        
        item = self.media_items[self.current_index]
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Move '{item.path.name}' to Recycle Bin?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                import send2trash
                send2trash.send2trash(str(item.path))
                self.media_items.pop(self.current_index)
                
                if not self.media_items:
                    self.show_welcome_screen()
                else:
                    self.current_index = min(self.current_index, len(self.media_items) - 1)
                    self.display_current_media()
                
                QMessageBox.information(self, "Success", "File moved to Recycle Bin")
            except ImportError:
                # Fallback if send2trash is not available
                try:
                    import winreg
                    # Use Windows API to move to recycle bin
                    os.system(f'del "{item.path}"')
                    self.media_items.pop(self.current_index)
                    self.display_current_media()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to delete file: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete file: {str(e)}")
    
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
        else:
            super().keyPressEvent(event)
    
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


def main():
    """Main entry point"""
    # Redirect stderr to a log file for the windowed exe so crashes aren't silent
    log_path = Path.home() / ".prive_randomizer_error.log"
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

    window = PriveRandomizerApp()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
