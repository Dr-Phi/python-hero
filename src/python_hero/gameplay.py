# ===== LINE 1 (src/python_hero/gameplay.py) =====
from __future__ import annotations

# ===== LINE 4 =====
from dataclasses import dataclass
from typing import List, Tuple, Optional

# ===== LINE 8 =====
from . import config


# ============================================================
# ===== LINE 12 : Core Note Model ============================
# ============================================================

# ===== LINE 15 =====
@dataclass
class Note:
    lane: int
    target_time: float

    # ===== LINE 20 =====
    def position(self, song_time: float) -> tuple[float, float]:
        """
        Returns (x, y) in GAME SPACE.
        Movement is constant-speed from start->end over config.LEAD_TIME.

        ratio = (time_to_hit / lead_time)
          - ratio == 1.0 when the note should be at spawn point
          - ratio == 0.0 when the note should be at hit point
        """
        # ===== LINE 30 =====
        time_to_hit = self.target_time - song_time
        ratio = time_to_hit / config.LEAD_TIME

        # ===== LINE 34 =====
        sx = config.LANE_START_X[self.lane]
        ex = config.LANE_END_X[self.lane]

        # ===== LINE 38 =====
        x = ex + (sx - ex) * ratio
        y = config.END_Y + (config.START_Y - config.END_Y) * ratio
        return x, y


# ============================================================
# ===== LINE 46 : Gameplay Helpers (optional but clean) =======
# ============================================================

# ===== LINE 50 =====
def spawn_notes(
    recorded: List[Tuple[int, float]],
    active_notes: List[Note],
    now: float,
    spawn_index: int
) -> int:
    """
    Spawns notes into active_notes when they're within LEAD_TIME of being hit.

    recorded: list of (lane, time) sorted by time (it is, because you record in order)
    active_notes: list that gets appended to
    now: current song time
    spawn_index: where we left off

    Returns updated spawn_index.
    """
    # ===== LINE 66 =====
    while spawn_index < len(recorded):
        lane, t_note = recorded[spawn_index]
        if now >= t_note - config.LEAD_TIME:
            active_notes.append(Note(lane=lane, target_time=t_note))
            spawn_index += 1
        else:
            break
    return spawn_index


# ===== LINE 78 =====
def try_hit(
    active_notes: List[Note],
    lane: int,
    now: float,
    hit_bottom: float = config.HIT_BOTTOM,
    hit_top: float = config.HIT_TOP,
) -> bool:
    """
    Attempts to hit a note in the given lane within the hit window.
    Returns True if a note was hit and removed, else False.

    Simple behavior: hits the first matching note found.
    (Later we can improve to pick the closest note to END_Y.)
    """
    # ===== LINE 92 =====
    for n in list(active_notes):
        _, y = n.position(now)
        if n.lane == lane and (hit_bottom <= y <= hit_top):
            active_notes.remove(n)
            return True
    return False


# ===== LINE 102 =====
def cleanup_notes(active_notes: List[Note], now: float) -> None:
    """
    Removes notes that are far past the hit zone (in GAME SPACE).
    This prevents piles of notes on screen if missed.
    """
    # ===== LINE 109 =====
    for n in list(active_notes):
        _, y = n.position(now)
        if y < (config.HIT_BOTTOM - 220):
            active_notes.remove(n)