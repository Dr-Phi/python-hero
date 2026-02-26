# src/python_hero/songs.py
from __future__ import annotations

from pathlib import Path
from typing import List

from .config import ASSETS_DIR


def list_songs(assets_dir: Path = ASSETS_DIR) -> List[Path]:
    """
    Returns a sorted list of .mp3 files inside assets/.
    """
    if not assets_dir.exists():
        return []

    songs = [p for p in assets_dir.glob("*.mp3") if p.is_file()]
    songs.sort(key=lambda p: p.name.lower())
    return songs


def display_name(song_path: Path) -> str:
    """
    Returns filename without extension.
    """
    return song_path.stem