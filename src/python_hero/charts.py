from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from .config import ASSETS_DIR


def _base(song_path: Path) -> str:
    return song_path.stem


def list_charts(song_path: Path) -> List[Path]:
    """
    Returns all charts for a song in assets/, sorted by name.
    Naming convention:
      <song>_chart.txt
      <song>_chart_01.txt
      <song>_chart_myversion.txt
    """
    base = _base(song_path)
    patterns = [f"{base}_chart*.txt"]
    charts: List[Path] = []
    for pat in patterns:
        charts.extend([p for p in ASSETS_DIR.glob(pat) if p.is_file()])
    charts = sorted(set(charts), key=lambda p: p.name.lower())
    return charts


def next_new_chart_path(song_path: Path) -> Path:
    """
    Creates a new chart filename that doesn't exist yet.
    Uses numeric suffixes: <song>_chart_01.txt, _02, ...
    """
    base = _base(song_path)
    existing = {p.name.lower() for p in list_charts(song_path)}

    # Prefer _01, _02... and never overwrite.
    for i in range(1, 1000):
        name = f"{base}_chart_{i:02d}.txt"
        if name.lower() not in existing:
            return ASSETS_DIR / name

    # fallback (unlikely)
    return ASSETS_DIR / f"{base}_chart_new.txt"


def save_chart_to_path(chart_path: Path, notes: List[Tuple[int, float]]) -> None:
    chart_path.parent.mkdir(parents=True, exist_ok=True)
    with chart_path.open("w", encoding="utf-8") as f:
        for lane, t in notes:
            f.write(f"{lane} {t:.4f}\n")


def load_chart_from_path(chart_path: Path) -> List[Tuple[int, float]]:
    if not chart_path.exists():
        return []

    notes: List[Tuple[int, float]] = []
    with chart_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                lane_s, t_s = line.split()
                notes.append((int(lane_s), float(t_s)))
            except ValueError:
                continue
    return notes


def delete_chart(chart_path: Path) -> bool:
    try:
        if chart_path.exists():
            chart_path.unlink()
            return True
        return False
    except Exception:
        return False
