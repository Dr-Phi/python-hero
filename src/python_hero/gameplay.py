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
        """Calculates (x, y) in GAME SPACE based on time ratio."""
        # How much time is left until this note hits the line?
        time_to_hit = self.target_time - song_time

        # 1.0 = Just spawned at START_Y, 0.0 = At the hit zone (END_Y)
        ratio = time_to_hit / config.LEAD_TIME

        sx, ex = config.LANE_START_X[self.lane], config.LANE_END_X[self.lane]

        # Linear interpolation (Lerp)
        x = ex + (sx - ex) * ratio
        y = config.END_Y + (config.START_Y - config.END_Y) * ratio
        return x, y


def spawn_notes(
    recorded: List[Tuple[int, float]],
    active_notes: List[Note],
    now: float,
    spawn_index: int,
) -> int:
    """Spawns notes when they enter the LEAD_TIME window."""
    while spawn_index < len(recorded):
        lane, t_note = recorded[spawn_index]

        # Only spawn if the note should be visible on screen
        if now >= t_note - config.LEAD_TIME:
            active_notes.append(Note(lane=lane, target_time=t_note))
            spawn_index += 1
        else:
            break
    return spawn_index


def cleanup_notes(active_notes: List[Note], now: float) -> None:
    """Removes notes that have fallen significantly off-screen."""
    for n in list(active_notes):
        # If the note is more than 1 second past its target time, kill it
        if now > n.target_time + 1.0:
            active_notes.remove(n)


class GameplayManager:
    def __init__(self):
        self.start_time: float = 0.0
        self.pause_start: float = 0.0
        self.total_paused_time: float = 0.0
        self.is_paused: bool = False

    def start_game(self) -> None:
        self.start_time = time.time()
        self.total_paused_time = 0.0
        self.is_paused = False

    def pause(self) -> None:
        if not self.is_paused:
            self.pause_start = time.time()
            self.is_paused = True

    def resume(self) -> None:
        if self.is_paused:
            # Add the duration of the current pause to the total offset
            self.total_paused_time += time.time() - self.pause_start
            self.is_paused = False

    @property
    def current_song_time(self) -> float:
        """The 'true' song time, ignoring pauses."""
        if self.is_paused:
            reference = self.pause_start
        else:
            reference = time.time()

        return reference - self.start_time - self.total_paused_time
