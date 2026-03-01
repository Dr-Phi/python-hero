# src/python_hero/render.py
from __future__ import annotations
import pygame
from pathlib import Path
from typing import Optional, Sequence
from . import config
from .gameplay import Note
from .screens import Fonts
from .data_manager import Profile
from .songs import display_name


def to_screen(x: float, y: float) -> tuple[int, int]:
    """Converts Game-space (+Y up) to screen-space (Pygame +Y down)."""
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
    profile: Optional[Profile] = None,
    total_notes: int = 0,
) -> None:
    # Use config background color
    screen.fill(config.BACKGROUND_COLOR)

    # 1. Draw Fretboard (Lanes & Targets)
    for i in range(5):
        sx, sy = to_screen(config.LANE_START_X[i], config.START_Y)
        ex, ey = to_screen(config.LANE_END_X[i], config.END_Y)

        # Draw the lane path
        pygame.draw.line(screen, config.LANE_COLOR, (sx, sy), (ex, ey), 4)

        # Target circles (Hit Zone)
        pygame.draw.circle(screen, config.LANE_COLORS[i], (ex, ey), 24, 3)
        pygame.draw.circle(screen, (20, 20, 25), (ex, ey), 20)  # Dark inner hole

    # 2. Global Hit Line Visual
    _, hitline_y = to_screen(0, config.END_Y)
    pygame.draw.line(
        screen, config.HITLINE_COLOR, (0, hitline_y), (config.WIDTH, hitline_y), 2
    )

    # 3. Draw Falling Notes
    for n in active_notes:
        xg, yg = n.position(now)
        px, py = to_screen(xg, yg)

        # Note White Glow/Border
        pygame.draw.circle(screen, (255, 255, 255), (px, py), config.NOTE_RADIUS + 3)
        # Note Core Color
        pygame.draw.circle(
            screen, config.LANE_COLORS[n.lane], (px, py), config.NOTE_RADIUS
        )

    # 4. HUD (Heads-Up Display)
    hud_x = 40
    curr_y = 40
    accent = (0, 255, 70)  # Neon Green

    # Mode Indicator
    mode_txt = f"MODE: {mode.upper()}"
    screen.blit(fonts.ui_font.render(mode_txt, True, accent), (hud_x, curr_y))
    curr_y += 45

    # Score / Recording Count
    if mode == "play":
        score_txt = f"SCORE: {score:04d} / {total_notes:04d}"
        screen.blit(
            fonts.ui_font.render(score_txt, True, (255, 255, 255)), (hud_x, curr_y)
        )
    else:
        rec_txt = f"RECORDED: {recorded_count:03d}"
        screen.blit(fonts.ui_font.render(rec_txt, True, (255, 80, 80)), (hud_x, curr_y))
    curr_y += 45

    # Dynamic Key Hints
    if profile:
        key_names = [pygame.key.name(k).upper() for k in profile.keys]
        keys_str = "  ".join(key_names)
        screen.blit(
            fonts.hint_font.render(f"KEYS: {keys_str}", True, (160, 160, 170)),
            (hud_x, curr_y),
        )

    # 5. Track Info (Top Right)
    if song_path:
        track_name = display_name(song_path).upper()
        track_surf = fonts.hint_font.render(
            f"TRACK: {track_name}", True, (200, 200, 200)
        )
        screen.blit(track_surf, (config.WIDTH - track_surf.get_width() - 40, 40))

    # 6. Message Overlays (Pauses/Notices)
    if message_text:
        # Create Dimmed Background
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Render Message Box
        msg_surf = fonts.title_font.render(message_text, True, (255, 255, 255))
        rect = msg_surf.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2))

        # Subtle glowing border for the message
        pygame.draw.rect(screen, accent, rect.inflate(60, 30), 3, border_radius=10)
        screen.blit(msg_surf, rect)
