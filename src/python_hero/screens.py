from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import pygame
import time
import math

from . import config


# Minimal font bundle used by render/app
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
    screen.fill((10, 10, 14))

    _draw_centered_lines(
        screen,
        config.SPLASH_ART,
        fonts.ascii_font,
        (235, 235, 235),
        start_y=220,
    )
    # lower position (more separation from ASCII art)
    hint_y = 220 + len(config.SPLASH_ART) * 34 + 50

    # slow fade blink
    alpha = int(60 + 195 * (0.5 + 0.5 * math.sin(time.time() * 1.5)))
    color = (alpha, alpha, alpha)

    hint = "Press Space to get started."
    hint_surf = fonts.hint_font.render(hint, True, color)
    screen.blit(
        hint_surf,
        ((config.WIDTH - hint_surf.get_width()) // 2, hint_y),
    )


# ---------- Song Select ----------


def draw_song_select(
    screen: pygame.Surface,
    fonts: Fonts,
    songs: Sequence[Path],
    selected_index: int,
) -> None:
    screen.fill((10, 10, 14))

    title = fonts.title_font.render("Select a song:", True, (235, 235, 235))
    screen.blit(title, (40, 40))

    if not songs:
        msg = [
            "No .mp3 files found in assets/",
            f"Folder: {config.ASSETS_DIR}",
            "",
            "Add songs and restart.",
        ]
        _draw_centered_lines(
            screen, msg, fonts.option_font, (235, 235, 235), start_y=250
        )
        return

    y = 120
    for i, song in enumerate(songs):
        name = song.name
        prefix = "> " if i == selected_index else "  "
        color = (255, 255, 255) if i == selected_index else (180, 180, 200)
        surf = fonts.option_font.render(prefix + name, True, color)
        screen.blit(surf, (60, y))
        y += fonts.option_font.get_height() + 10

    hint = "UP/DOWN to navigate • ENTER to select • ESC to quit"
    hint_surf = fonts.hint_font.render(hint, True, config.HINT_TEXT_COLOR)
    screen.blit(hint_surf, (40, config.HEIGHT - 60))


# ---------- Chart Choice ----------


def draw_chart_choice(
    screen: pygame.Surface,
    fonts: Fonts,
    song_path: Path | None,
    charts: Sequence[Path],
    selected_index: int,
) -> None:
    screen.fill((10, 10, 14))

    if song_path is None:
        return

    screen.blit(
        fonts.title_font.render("Song selected:", True, (235, 235, 235)), (40, 40)
    )
    screen.blit(
        fonts.option_font.render(song_path.name, True, (200, 200, 220)), (60, 95)
    )

    screen.blit(
        fonts.option_font.render("R = record NEW chart", True, (235, 235, 235)),
        (60, 160),
    )

    if not charts:
        # Show only [NOT FOUND] in red (no filename)
        nf = fonts.option_font.render("[NOT FOUND]", True, (220, 80, 80))
        screen.blit(nf, (60, 210))

        screen.blit(
            fonts.hint_font.render(
                "Press R to start recording.", True, config.HINT_TEXT_COLOR
            ),
            (60, 255),
        )
        screen.blit(
            fonts.hint_font.render("ESC to quit", True, config.HINT_TEXT_COLOR),
            (40, config.HEIGHT - 60),
        )
        return

    # Charts list
    screen.blit(
        fonts.option_font.render("Select a chart:", True, (235, 235, 235)), (60, 210)
    )

    y = 260
    for i, p in enumerate(charts):
        prefix = "> " if i == selected_index else "  "
        color = (0, 255, 70) if i == selected_index else (0, 180, 0)
        screen.blit(fonts.option_font.render(prefix + p.name, True, color), (60, y))
        y += fonts.option_font.get_height() + 10

    screen.blit(
        fonts.option_font.render(
            "L / ENTER = load selected chart", True, (235, 235, 235)
        ),
        (60, y + 10),
    )
    screen.blit(
        fonts.option_font.render("D = delete selected chart", True, (235, 235, 235)),
        (60, y + 55),
    )
    screen.blit(
        fonts.hint_font.render(
            "UP/DOWN to choose • ESC to quit", True, config.HINT_TEXT_COLOR
        ),
        (40, config.HEIGHT - 60),
    )


def draw_confirm_delete(
    screen: pygame.Surface,
    fonts: Fonts,
    chart_name: str,
) -> None:
    screen.fill((10, 10, 14))
    screen.blit(
        fonts.title_font.render("Delete chart?", True, (235, 235, 235)), (40, 40)
    )
    screen.blit(fonts.option_font.render(chart_name, True, (200, 200, 220)), (60, 95))

    screen.blit(
        fonts.option_font.render("Press Y to confirm delete", True, (235, 235, 235)),
        (60, 170),
    )
    screen.blit(
        fonts.option_font.render("Press N to cancel", True, (235, 235, 235)),
        (60, 215),
    )
