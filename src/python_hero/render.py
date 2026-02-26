# src/python_hero/render.py
from __future__ import annotations

import pygame
from pathlib import Path
from typing import Optional, Sequence

from . import config
from .gameplay import Note
from .screens import Fonts


def to_screen(x: float, y: float) -> tuple[int, int]:
    """Game-space (+Y up) -> screen-space (pygame +Y down)."""
    px = config.CENTER_X + int(x * config.SCALE * config.X_SQUEEZE)
    py = config.CENTER_Y - int(y * config.SCALE)
    return px, py


def draw_game(
    screen: pygame.Surface,
    fonts: Fonts,
    mode: str,
    score: int,
    recorded_count: int,
    song_path: Optional[Path],
    active_notes: Sequence[Note],
    now: float,
    message_text: Optional[str] = None,
) -> None:
    screen.fill(config.BACKGROUND_COLOR)

    # Lanes
    for i in range(5):
        sx, sy = to_screen(config.LANE_START_X[i], config.START_Y)
        ex, ey = to_screen(config.LANE_END_X[i], config.END_Y)
        pygame.draw.line(screen, config.LANE_COLOR, (sx, sy), (ex, ey), 4)
        pygame.draw.circle(screen, config.LANE_COLORS[i], (ex, ey), 18, 3)

    # Hit line + hitbox
    _, hitline_y = to_screen(0, config.END_Y)
    pygame.draw.line(screen, config.HITLINE_COLOR, (0, hitline_y), (config.WIDTH, hitline_y), 2)

    left_x = min(config.LANE_END_X) - 140
    right_x = max(config.LANE_END_X) + 140
    x1, y1 = to_screen(left_x, config.HIT_TOP)
    x2, y2 = to_screen(right_x, config.HIT_BOTTOM)
    hit_rect = pygame.Rect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
    pygame.draw.rect(screen, config.HITBOX_COLOR, hit_rect, 2)

    # Notes
    for n in active_notes:
        xg, yg = n.position(now)
        px, py = to_screen(xg, yg)
        pygame.draw.circle(screen, config.LANE_COLORS[n.lane], (px, py), config.NOTE_RADIUS)

    # UI
    ui1 = fonts.ui_font.render(f"Mode: {mode.upper()}", True, config.UI_TEXT_COLOR)
    ui2 = fonts.ui_font.render(f"Score: {score}   Recorded notes: {recorded_count}", True, config.UI_TEXT_COLOR)
    ui3 = fonts.ui_font.render("Keys: Y U I O P   (S=Save in RECORD)", True, config.UI_TEXT_COLOR)
    screen.blit(ui1, (20, 20))
    screen.blit(ui2, (20, 60))
    screen.blit(ui3, (20, 100))

    if song_path:
        song_name = song_path.name
        song_surf = fonts.hint_font.render(f"Song: {song_name}", True, config.HINT_TEXT_COLOR)
        screen.blit(song_surf, (20, 140))

    # Message overlay
    if message_text:
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))

        msg = fonts.title_font.render(message_text, True, (255, 255, 255))
        screen.blit(msg, ((config.WIDTH - msg.get_width()) // 2, config.HEIGHT // 2 - 30))