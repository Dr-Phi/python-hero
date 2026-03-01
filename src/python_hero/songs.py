# src/python_hero/songs.py
from __future__ import annotations
from pathlib import Path
from typing import List
from .config import ASSETS_DIR


def list_songs(assets_dir: Path = ASSETS_DIR) -> List[Path]:
    """
    Returns a naturally sorted list of all .mp3 files found in the assets directory.
    """
    if not assets_dir.exists():
        assets_dir.mkdir(parents=True, exist_ok=True)
        return []

    # Filter for mp3 files and sort alphabetically
    songs = [p for p in assets_dir.glob("*.mp3") if p.is_file()]
    songs.sort(key=lambda p: p.name.lower())
    return songs


def display_name(song_path: Path) -> str:
    """
    Returns a clean, UI-friendly version of the song title.
    Example: 'beat_it' -> 'Beat It'
    """
    if not song_path:
        return "Unknown Track"

    return song_path.stem.replace("_", " ").title()
