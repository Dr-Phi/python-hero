from __future__ import annotations

import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, Final

import pygame
from . import config

# --- Visual Constants ---
BG_DARK: Final = (10, 10, 14)
TEXT_PRIMARY: Final = (235, 235, 235)
ACCENT_GREEN: Final = (0, 255, 70)
ACCENT_RED: Final = (220, 80, 80)
DIM_TEXT: Final = (150, 150, 160)


@dataclass
class Fonts:
    ascii_font: pygame.font.Font
    hint_font: pygame.font.Font
    title_font: pygame.font.Font
    option_font: pygame.font.Font
    ui_font: pygame.font.Font


def _draw_centered_lines(
    screen: pygame.Surface,
    lines: Sequence[str],
    font: pygame.font.Font,
    color: tuple[int, int, int],
    start_y: int,
) -> None:
    y = start_y
    for line in lines:
        surf = font.render(line, True, color)
        x = (config.WIDTH - surf.get_width()) // 2
        screen.blit(surf, (x, y))
        y += font.get_height() + 6


# ---------- Splash ----------


def draw_splash(screen: pygame.Surface, fonts: Fonts) -> None:
    screen.fill(BG_DARK)

    _draw_centered_lines(
        screen, config.SPLASH_ART, fonts.ascii_font, TEXT_PRIMARY, start_y=220
    )

    # Calculate hint position based on ASCII art height
    hint_y = 220 + (len(config.SPLASH_ART) * 34) + 60

    # Smooth pulsing alpha for the prompt
    pulse = int(120 + 135 * (0.5 + 0.5 * math.sin(time.time() * 3)))
    prompt_surf = fonts.title_font.render(
        "Press ENTER to Start", True, (pulse, pulse, pulse)
    )

    screen.blit(prompt_surf, ((config.WIDTH - prompt_surf.get_width()) // 2, hint_y))


# ---------- Song Select ----------


def draw_song_select(
    screen: pygame.Surface,
    fonts: Fonts,
    songs: Sequence[Path],
    selected_index: int,
) -> None:
    screen.fill(BG_DARK)

    title = fonts.title_font.render("SELECT A SONG", True, TEXT_PRIMARY)
    screen.blit(title, (60, 60))

    if not songs:
        msg = [
            "No .mp3 files found in assets/",
            f"Folder: {config.ASSETS_DIR}",
            "",
            "Please add songs and restart.",
        ]
        _draw_centered_lines(screen, msg, fonts.option_font, ACCENT_RED, 300)
        return

    y = 160
    for i, song in enumerate(songs):
        is_selected = i == selected_index
        prefix = ">> " if is_selected else "   "
        color = TEXT_PRIMARY if is_selected else DIM_TEXT

        surf = fonts.option_font.render(f"{prefix}{song.stem}", True, color)
        screen.blit(surf, (80, y))
        y += surf.get_height() + 15

    # Standard Footer Hint
    hint = "UP/DOWN: Navigate  |  ENTER: Select  |  ESC: Quit"
    hint_surf = fonts.hint_font.render(hint, True, config.HINT_TEXT_COLOR)
    screen.blit(hint_surf, (60, config.HEIGHT - 60))


# ---------- Chart Choice ----------


def draw_chart_choice(
    screen: pygame.Surface,
    fonts: Fonts,
    song_path: Path | None,
    charts: Sequence[Path],
    selected_index: int,
) -> None:
    screen.fill(BG_DARK)
    if not song_path:
        return

    # Header
    screen.blit(
        fonts.title_font.render("CHART SELECTION", True, TEXT_PRIMARY), (60, 60)
    )
    screen.blit(
        fonts.option_font.render(f"Song: {song_path.stem}", True, DIM_TEXT), (80, 110)
    )

    # Recording Option
    rec_color = ACCENT_GREEN if math.sin(time.time() * 5) > 0 else TEXT_PRIMARY
    screen.blit(
        fonts.option_font.render("Press R to record a NEW chart", True, rec_color),
        (80, 180),
    )

    y_list = 260
    if not charts:
        screen.blit(
            fonts.option_font.render("[ NO CHARTS FOUND ]", True, ACCENT_RED),
            (80, y_list),
        )
    else:
        screen.blit(
            fonts.hint_font.render("Existing Charts:", True, DIM_TEXT), (80, y_list)
        )
        y = y_list + 40
        for i, p in enumerate(charts):
            is_selected = i == selected_index
            prefix = ">> " if is_selected else "   "
            color = ACCENT_GREEN if is_selected else DIM_TEXT

            surf = fonts.option_font.render(f"{prefix}{p.name}", True, color)
            screen.blit(surf, (80, y))
            y += surf.get_height() + 12

        # Action labels
        screen.blit(
            fonts.hint_font.render(
                "ENTER: Play Chart  |  D: Delete Chart", True, TEXT_PRIMARY
            ),
            (80, y + 20),
        )

    # Standard Footer Hint
    hint = "UP/DOWN: Navigate  |  ESC: Back to Songs"
    hint_surf = fonts.hint_font.render(hint, True, config.HINT_TEXT_COLOR)
    screen.blit(hint_surf, (60, config.HEIGHT - 60))


# ---------- Modals (Quit / Delete) ----------


def draw_quit_confirm(screen: pygame.Surface, fonts: Fonts) -> None:
    _draw_modal_box(
        screen, fonts, "Quit Game?", "ENTER: Yes | ESC: No", is_danger=False
    )


def draw_confirm_delete(screen: pygame.Surface, fonts: Fonts, chart_name: str) -> None:
    _draw_modal_box(
        screen,
        fonts,
        f"Delete {chart_name}?",
        "ENTER: Confirm | ESC: Cancel",
        is_danger=True,
    )


def _draw_modal_box(
    screen: pygame.Surface,
    fonts: Fonts,
    title_text: str,
    hint_text: str,
    is_danger: bool = False,
) -> None:
    """Internal helper to draw consistent confirmation boxes."""
    overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))

    bw, bh = 600, 220
    bx, by = (config.WIDTH - bw) // 2, (config.HEIGHT - bh) // 2

    border_color = ACCENT_RED if is_danger else ACCENT_GREEN
    bg_color = (40, 20, 20) if is_danger else (30, 30, 40)

    pygame.draw.rect(screen, bg_color, (bx, by, bw, bh))
    pygame.draw.rect(screen, border_color, (bx, by, bw, bh), 3)

    t_surf = fonts.option_font.render(title_text, True, TEXT_PRIMARY)
    h_surf = fonts.hint_font.render(hint_text, True, border_color)

    screen.blit(t_surf, (bx + (bw - t_surf.get_width()) // 2, by + 60))
    screen.blit(h_surf, (bx + (bw - h_surf.get_width()) // 2, by + 130))


# ---------- Gameplay UI ----------


def draw_pause_menu(
    screen: pygame.Surface, fonts: Fonts, mode: str, selected_index: int
) -> None:
    # Semi-transparent black pause screen
    overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))
    screen.blit(overlay, (0, 0))

    title = fonts.title_font.render("PAUSED", True, ACCENT_GREEN)
    screen.blit(title, ((config.WIDTH - title.get_width()) // 2, 150))

    options = (
        ["Resume", "Restart Song", "Exit to Menu"]
        if mode == "play"
        else ["Resume Recording", "Save Chart", "Start Over", "Exit to Menu"]
    )

    y = 280
    for i, opt in enumerate(options):
        is_sel = i == selected_index
        color = ACCENT_GREEN if is_sel else DIM_TEXT
        prefix = "> " if is_sel else "  "
        surf = fonts.option_font.render(prefix + opt, True, color)
        screen.blit(surf, ((config.WIDTH - surf.get_width()) // 2, y))
        y += 50

    hint = fonts.hint_font.render(
        "UP/DOWN: Navigate | ENTER: Select | ESC: Resume", True, ACCENT_GREEN
    )
    screen.blit(hint, ((config.WIDTH - hint.get_width()) // 2, config.HEIGHT - 100))


def draw_pause_countdown(screen: pygame.Surface, fonts: Fonts, value: int) -> None:
    """Draws a semi-transparent overlay with a centered countdown."""
    # 1. Create a semi-transparent overlay (Alpha 160/255)
    overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    # 2. Render the text
    title = fonts.title_font.render("GET READY", True, (0, 255, 70))
    num = fonts.title_font.render(str(value), True, (255, 255, 255))

    # 3. Calculate Vertical Center (using config.HEIGHT)
    # This prevents the text from being "too high"
    center_y = config.HEIGHT // 2

    title_x = (config.WIDTH - title.get_width()) // 2
    title_y = center_y - 80  # Positioned slightly above center

    num_x = (config.WIDTH - num.get_width()) // 2
    num_y = center_y + 20  # Positioned slightly below center

    screen.blit(title, (title_x, title_y))
    screen.blit(num, (num_x, num_y))
