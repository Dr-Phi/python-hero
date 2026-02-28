from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Tuple, Final

from . import config


@dataclass
class Note:
    lane: int
    target_time: float

    def position(self, song_time: float) -> tuple[float, float]:
        """
        Returns (x, y) in GAME SPACE.
        Movement is constant-speed from start->end over config.LEAD_TIME.
        """
        # We use the managed song_time to calculate how close the note is to the hit zone
        time_to_hit = self.target_time - song_time
        ratio = time_to_hit / config.LEAD_TIME

        sx = config.LANE_START_X[self.lane]
        ex = config.LANE_END_X[self.lane]

        # Linear interpolation based on the time ratio
        x = ex + (sx - ex) * ratio
        y = config.END_Y + (config.START_Y - config.END_Y) * ratio
        return x, y


def spawn_notes(
    recorded: List[Tuple[int, float]],
    active_notes: List[Note],
    now: float,
    spawn_index: int,
) -> int:
    """
    Spawns notes into active_notes when they're within LEAD_TIME of being hit.
    'now' MUST be gameplay_manager.current_song_time.
    """
    while spawn_index < len(recorded):
        lane, t_note = recorded[spawn_index]
        # Check if it's time to show the note based on LEAD_TIME
        if now >= t_note - config.LEAD_TIME:
            active_notes.append(Note(lane=lane, target_time=t_note))
            spawn_index += 1
        else:
            break
    return spawn_index


def try_hit(
    active_notes: List[Note],
    lane: int,
    now: float,
    hit_bottom: float = config.HIT_BOTTOM,
    hit_top: float = config.HIT_TOP,
) -> bool:
    """Attempts to hit a note in the given lane within the hit window."""
    for n in list(active_notes):
        _, y = n.position(now)
        if n.lane == lane and (hit_bottom <= y <= hit_top):
            active_notes.remove(n)
            return True
    return False


def cleanup_notes(active_notes: List[Note], now: float) -> None:
    """Removes notes that are far past the hit zone."""
    for n in list(active_notes):
        _, y = n.position(now)
        # If the note has moved 220 units past the bottom, remove it
        if y < (config.HIT_BOTTOM - 220):
            active_notes.remove(n)


class GameplayManager:
    def __init__(self, song_start_delay: float = 3.0):
        self.start_time: float = 0.0
        self.pause_start: float = 0.0
        self.total_paused_time: float = 0.0
        self.is_paused: bool = False
        self.song_start_delay: Final[float] = song_start_delay

    def start_game(self) -> None:
        """Initializes the start reference point."""
        self.start_time = time.time()
        self.total_paused_time = 0.0
        self.is_paused = False

    def pause(self) -> None:
        """Captures the exact moment the pause started."""
        if not self.is_paused:
            self.pause_start = time.time()
            self.is_paused = True

    def resume(self) -> None:
        """Calculates how long we were paused and adds to the offset."""
        if self.is_paused:
            # Calculate duration of the CURRENT pause and add to global offset
            pause_duration = time.time() - self.pause_start
            self.total_paused_time += pause_duration
            self.is_paused = False

    @property
    def current_song_time(self) -> float:
        """
        Returns the adjusted time in seconds that the song has been playing.
        Subtracts all time spent in the pause menu.
        """
        if self.is_paused:
            # Return the "frozen" time from when the pause began
            return self.pause_start - self.start_time - self.total_paused_time

        return time.time() - self.start_time - self.total_paused_time

    def get_chart_position(self) -> float:
        """Returns the time used to calculate note positions."""
        return self.current_song_time - self.song_start_delay
