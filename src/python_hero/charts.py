from __future__ import annotations
from pathlib import Path
from typing import List, Tuple
from .config import ASSETS_DIR


def _base(song_path: Path) -> str:
    """Returns the clean stem of the song file."""
    return song_path.stem


def list_charts(song_path: Path) -> List[Path]:
    """
    Returns all charts for a specific song found in the assets directory.
    Filters by the naming convention: <song_name>_chart*.txt
    """
    if not song_path:
        return []

    base = _base(song_path)
    # Glob for any txt files starting with the song name and '_chart'
    pattern = f"{base}_chart*.txt"

    charts = [p for p in ASSETS_DIR.glob(pattern) if p.is_file()]
    # Sort naturally (01, 02, 03...)
    return sorted(charts, key=lambda p: p.name.lower())


def next_new_chart_path(song_path: Path) -> Path:
    """
    Generates a unique, non-existent path for a new recording.
    Format: assets/<song_name>_chart_XX.txt
    """
    base = _base(song_path)
    existing_names = {p.name.lower() for p in list_charts(song_path)}

    # Find the first available numeric slot
    for i in range(1, 100):
        filename = f"{base}_chart_{i:02d}.txt"
        if filename.lower() not in existing_names:
            return ASSETS_DIR / filename

    # Fallback to a timestamp or 'new' if 99 charts exist (unlikely)
    return ASSETS_DIR / f"{base}_chart_new_{int(time.time())}.txt"


def save_chart_to_path(chart_path: Path, notes: List[Tuple[int, float]]) -> None:
    """Saves the recorded (lane, timestamp) pairs to a space-separated text file."""
    chart_path.parent.mkdir(parents=True, exist_ok=True)
    with chart_path.open("w", encoding="utf-8") as f:
        for lane, t in notes:
            # Format to 4 decimal places for timing precision
            f.write(f"{lane} {t:.4f}\n")


def load_chart_from_path(chart_path: Path) -> List[Tuple[int, float]]:
    """Reads a chart file and returns a list of notes."""
    if not chart_path or not chart_path.exists():
        return []

    notes: List[Tuple[int, float]] = []
    try:
        with chart_path.open("r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2:
                    lane_s, t_s = parts
                    notes.append((int(lane_s), float(t_s)))
    except (ValueError, IOError):
        # Return what we have or empty list if file is corrupted
        pass

    return notes


def delete_chart(chart_path: Path) -> bool:
    """Attempts to permanently delete the chart file from disk."""
    try:
        if chart_path and chart_path.exists():
            chart_path.unlink()
            return True
    except OSError:
        pass
    return False
