# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — one-dir build for Inno Setup packaging

import os

_vlc = r'C:\Program Files\VideoLAN\VLC'
_plug = os.path.join(_vlc, 'plugins')

# Only bundle essential plugins for local media playback (~65 MB)
_vlc_bins = [
    # Core DLLs
    (os.path.join(_vlc, 'libvlc.dll'), '.'),
    (os.path.join(_vlc, 'libvlccore.dll'), '.'),
    # File access (only local filesystem, skip network/bluray/vnc/srt)
    (os.path.join(_plug, 'access', 'libfilesystem_plugin.dll'), 'plugins/access'),
    # Full dirs needed for playback
    (os.path.join(_plug, 'audio_mixer', '*'), 'plugins/audio_mixer'),
    (os.path.join(_plug, 'audio_output', '*'), 'plugins/audio_output'),
    (os.path.join(_plug, 'codec', '*'), 'plugins/codec'),
    (os.path.join(_plug, 'd3d11', '*'), 'plugins/d3d11'),
    (os.path.join(_plug, 'd3d9', '*'), 'plugins/d3d9'),
    (os.path.join(_plug, 'demux', '*'), 'plugins/demux'),
    (os.path.join(_plug, 'packetizer', '*'), 'plugins/packetizer'),
    (os.path.join(_plug, 'video_chroma', '*'), 'plugins/video_chroma'),
    (os.path.join(_plug, 'video_output', '*'), 'plugins/video_output'),
]

a = Analysis(
    ['gkmedia_randomizer.py'],
    pathex=[],
    binaries=_vlc_bins,
    datas=[
        ('icon.ico', '.'),
        ('icon.png', '.'),
        ('assets/license.txt', '.'),
        ('assets/THIRD_PARTY_NOTICES.txt', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GKMediaRandomizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GKMediaRandomizer',
)
