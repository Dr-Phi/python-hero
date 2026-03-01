from __future__ import annotations

import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Dict, Final, Tuple

import pygame
from . import config
from .data_manager import Profile
from .songs import display_name

# --- Visual Constants ---
BG_DARK: Final = (10, 10, 14)
TEXT_PRIMARY: Final = (235, 235, 235)
ACCENT_GREEN: Final = (0, 255, 70)
ACCENT_RED: Final = (220, 80, 80)
ACCENT_GOLD: Final = (255, 215, 0)
DIM_TEXT: Final = (150, 150, 160)


@dataclass
class Fonts:
    ascii_font: pygame.font.Font
    hint_font: pygame.font.Font
    title_font: pygame.font.Font
    option_font: pygame.font.Font
    ui_font: pygame.font.Font

    @staticmethod
    def default() -> Fonts:
        """Standard font loader used by the App."""
        return Fonts(
            ascii_font=pygame.font.SysFont("consolas", 28),
            hint_font=pygame.font.SysFont("consolas", 22),
            title_font=pygame.font.SysFont("consolas", 34),
            option_font=pygame.font.SysFont("consolas", 26),
            ui_font=pygame.font.SysFont(None, 34),
        )


# --- Internal Helpers ---


def _draw_centered(
    screen: pygame.Surface, text: str, font: pygame.font.Font, color: tuple, y: int
):
    surf = font.render(text, True, color)
    screen.blit(surf, ((config.WIDTH - surf.get_width()) // 2, y))


def _draw_overlay(screen: pygame.Surface, alpha: int = 200):
    overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, alpha))
    screen.blit(overlay, (0, 0))


def _get_grade(percent: float) -> Tuple[str, tuple]:
    """Returns (Letter, Color) based on accuracy percentage."""
    if percent >= 100:
        return ("S", ACCENT_GOLD)
    if percent >= 90:
        return ("A", ACCENT_GREEN)
    if percent >= 80:
        return ("B", (100, 200, 255))
    if percent >= 70:
        return ("C", (255, 165, 0))
    return ("F", ACCENT_RED)


# --- Primary Screens ---


def draw_splash(screen: pygame.Surface, fonts: Fonts) -> None:
    screen.fill(BG_DARK)
    y = 220
    for line in config.SPLASH_ART:
        surf = fonts.ascii_font.render(line, True, TEXT_PRIMARY)
        screen.blit(surf, ((config.WIDTH - surf.get_width()) // 2, y))
        y += fonts.ascii_font.get_height() + 2

    pulse = int(120 + 135 * (0.5 + 0.5 * math.sin(time.time() * 3)))
    _draw_centered(
        screen, "Press ENTER to Start", fonts.title_font, (pulse, pulse, pulse), y + 60
    )


def draw_main_menu(screen: pygame.Surface, fonts: Fonts, selected_index: int) -> None:
    screen.fill(BG_DARK)
    _draw_centered(screen, "PYTHON HERO", fonts.title_font, ACCENT_GREEN, 80)

    options = ["Play Game", "Settings", "Profiles", "High Scores", "Quit"]
    for i, opt in enumerate(options):
        is_sel = i == selected_index
        color = ACCENT_GREEN if is_sel else DIM_TEXT
        prefix = ">> " if is_sel else "   "
        _draw_centered(screen, prefix + opt, fonts.option_font, color, 250 + i * 60)


def draw_settings(
    screen: pygame.Surface,
    fonts: Fonts,
    current_keys: List[int],
    rebinding_idx: int,
    menu_index: int,
) -> None:
    screen.fill(BG_DARK)
    _draw_centered(screen, "SETTINGS: KEY BINDINGS", fonts.title_font, TEXT_PRIMARY, 60)

    y = 200
    lanes = ["Lane 1", "Lane 2", "Lane 3", "Lane 4", "Lane 5"]

    for i, lane_name in enumerate(lanes):
        # 1. Determine Color/Text based on state
        is_active = i == rebinding_idx
        is_hovered = i == menu_index and rebinding_idx == -1

        if is_active:
            color, text = (255, 255, 0), f"{lane_name}: [ PRESS ANY KEY ]"
        elif is_hovered:
            color, text = (
                ACCENT_GREEN,
                f"{lane_name}: [{pygame.key.name(current_keys[i]).upper()}] <<",
            )
        else:
            color, text = (
                DIM_TEXT,
                f"{lane_name}: [{pygame.key.name(current_keys[i]).upper()}]",
            )

        # 2. Render
        surf = fonts.option_font.render(text, True, color)
        screen.blit(surf, ((config.WIDTH - surf.get_width()) // 2, y))
        y += 60

    _draw_centered(
        screen,
        "UP/DOWN: Select | ENTER: Rebind | R: Reset | ESC: Save",
        fonts.hint_font,
        DIM_TEXT,
        config.HEIGHT - 80,
    )


def draw_profile_select(
    screen: pygame.Surface, fonts: Fonts, names: List[str], selected: int, active: str
) -> None:
    screen.fill(BG_DARK)
    _draw_centered(screen, "SELECT PROFILE", fonts.title_font, TEXT_PRIMARY, 60)
    _draw_centered(
        screen, f"Logged in as: {active}", fonts.hint_font, ACCENT_GREEN, 120
    )

    opts = names + ["[ Create New Profile ]"]
    for i, name in enumerate(opts):
        color = TEXT_PRIMARY if i == selected else DIM_TEXT
        _draw_centered(screen, name, fonts.option_font, color, 200 + i * 50)

    _draw_centered(
        screen,
        "ESC: Back | ENTER: Select | D: Delete Profile",
        fonts.hint_font,
        DIM_TEXT,
        config.HEIGHT - 60,
    )


def draw_song_select(
    screen: pygame.Surface, fonts: Fonts, songs: Sequence[Path], selected: int
) -> None:
    screen.fill(BG_DARK)
    _draw_centered(screen, "SELECT A SONG", fonts.title_font, TEXT_PRIMARY, 60)

    for i, song in enumerate(songs):
        color = TEXT_PRIMARY if i == selected else DIM_TEXT
        prefix = ">> " if i == selected else "   "
        clean_name = display_name(song)
        surf = fonts.option_font.render(f"{prefix}{clean_name}", True, color)
        screen.blit(surf, (100, 180 + i * 45))

    _draw_centered(
        screen,
        "UP/DOWN: Navigate | ENTER: Select | ESC: Main Menu",
        fonts.hint_font,
        DIM_TEXT,
        config.HEIGHT - 60,
    )


def draw_chart_choice(screen, fonts, song, charts, selected, profile) -> None:
    screen.fill(BG_DARK)
    if not song:
        return
    _draw_centered(screen, f"CHART: {song.stem}", fonts.title_font, TEXT_PRIMARY, 60)

    y = 180
    if not charts:
        _draw_centered(screen, "[ NO CHARTS FOUND ]", fonts.option_font, ACCENT_RED, y)
    else:
        for i, p in enumerate(charts):
            is_sel = i == selected
            color = ACCENT_GREEN if is_sel else DIM_TEXT
            surf = fonts.option_font.render(
                f"{'>> ' if is_sel else '   '}{p.name}", True, color
            )
            screen.blit(surf, (100, y))

            if is_sel and p.name in profile.stats.song_data:
                pb = profile.stats.song_data[p.name]
                pb_txt = fonts.hint_font.render(
                    f"(PB: {pb.best_percent}%)", True, ACCENT_GREEN
                )
                screen.blit(pb_txt, (110 + surf.get_width(), y + 5))
            y += 45

    _draw_centered(
        screen,
        "ENTER: Play | R: Record | D: Delete | X: Reset",
        fonts.hint_font,
        DIM_TEXT,
        config.HEIGHT - 100,
    )


from .songs import display_name  # Ensure this import is at the top of screens.py


def draw_high_scores(screen, fonts, records) -> None:
    screen.fill(BG_DARK)
    _draw_centered(screen, "WORLD RECORDS", fonts.title_font, ACCENT_GOLD, 50)

    y = 150
    # Header for the table
    header_str = f"{'PLAYER':<15} {'SCORE (ACC%)':<25} {'SONG':<20}"
    header = fonts.hint_font.render(header_str, True, DIM_TEXT)
    screen.blit(header, (100, y))

    y += 45
    if not records:
        _draw_centered(
            screen, "[ NO RECORDS YET ]", fonts.option_font, DIM_TEXT, y + 40
        )
    else:
        # 1. Sort records by hits (score) so the best players are at the top
        sorted_items = sorted(
            records.items(), key=lambda item: item[1].get("hits", 0), reverse=True
        )

        for chart_name, data in sorted_items:
            # 2. Use the new display_name logic (handles underscores and casing)
            # We strip the chart suffix first, then pass to the path utility
            base_name = (
                chart_name.replace(".txt", "").replace(".json", "").split("_chart_")[0]
            )
            song = display_name(Path(base_name))[:20]

            # 3. Format the row data
            player = data.get("player", "???")[:12]
            hits = data.get("hits", 0)
            acc = data.get("accuracy", 0)

            row_text = f"{player:<15} {hits} ({acc}%)".ljust(41) + f"{song}"

            # 4. Render the row
            screen.blit(fonts.ascii_font.render(row_text, True, TEXT_PRIMARY), (100, y))
            y += 40

            # Prevent drawing off the bottom of the screen
            if y > config.HEIGHT - 100:
                break

    _draw_centered(
        screen,
        "ESC: Back | C: Wipe All Records",
        fonts.hint_font,
        DIM_TEXT,
        config.HEIGHT - 60,
    )


# ---------- New Results Screen ----------
def draw_pause_countdown(screen: pygame.Surface, fonts: Fonts, value: int) -> None:
    """Draws a semi-transparent overlay with a centered countdown number."""
    # 1. Create a semi-transparent dark overlay
    overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    # 2. Render the "GET READY" text and the countdown number
    title = fonts.title_font.render("GET READY", True, ACCENT_GREEN)
    num = fonts.title_font.render(str(value), True, TEXT_PRIMARY)

    # 3. Position them in the center of the screen
    center_x = config.WIDTH // 2
    center_y = config.HEIGHT // 2

    screen.blit(title, (center_x - title.get_width() // 2, center_y - 80))
    screen.blit(num, (center_x - num.get_width() // 2, center_y + 20))


def draw_results(screen: pygame.Surface, fonts: Fonts, hits: int, total: int) -> None:
    screen.fill(BG_DARK)
    percent = (hits / total * 100) if total > 0 else 0
    grade_char, grade_color = _get_grade(percent)

    _draw_centered(screen, "PERFORMANCE RESULTS", fonts.title_font, TEXT_PRIMARY, 80)

    # Draw Grade
    grade_font = pygame.font.SysFont("consolas", 120, bold=True)
    grade_surf = grade_font.render(grade_char, True, grade_color)
    screen.blit(grade_surf, ((config.WIDTH - grade_surf.get_width()) // 2, 180))

    # Stats
    _draw_centered(
        screen, f"Notes Hit: {hits} / {total}", fonts.option_font, TEXT_PRIMARY, 340
    )
    _draw_centered(
        screen, f"Accuracy: {percent:.2f}%", fonts.option_font, grade_color, 390
    )

    _draw_centered(
        screen,
        "Press ENTER to Continue",
        fonts.hint_font,
        DIM_TEXT,
        config.HEIGHT - 100,
    )


# ---------- Overlays & Modals ----------


def draw_pause_menu(
    screen: pygame.Surface, fonts: Fonts, mode: str, selected_index: int
) -> None:
    _draw_overlay(screen, 220)  # Using our helper from the previous optimization
    _draw_centered(screen, "PAUSED", fonts.title_font, ACCENT_GREEN, 150)

    options = (
        ["Resume", "Restart", "Exit"]
        if mode == "play"
        else ["Resume", "Save Chart", "Exit"]
    )

    for i, opt in enumerate(options):
        is_sel = i == selected_index
        color = ACCENT_GREEN if is_sel else DIM_TEXT
        prefix = "> " if is_sel else "  "
        _draw_centered(screen, prefix + opt, fonts.option_font, color, 280 + i * 50)


def draw_confirm_dialog(screen, fonts, title, subtext, is_danger=True):
    _draw_overlay(screen)
    rect = pygame.Rect(0, 0, 550, 220)
    rect.center = (config.WIDTH // 2, config.HEIGHT // 2)
    border = ACCENT_RED if is_danger else ACCENT_GREEN
    pygame.draw.rect(screen, (25, 25, 35), rect)
    pygame.draw.rect(screen, border, rect, 3)

    _draw_centered(screen, title, fonts.title_font, border, rect.top + 40)
    _draw_centered(screen, subtext, fonts.hint_font, TEXT_PRIMARY, rect.top + 100)
    _draw_centered(
        screen,
        "ENTER: Confirm | ESC: Cancel",
        fonts.hint_font,
        DIM_TEXT,
        rect.bottom - 50,
    )


def draw_create_profile(
    screen: pygame.Surface, fonts: Fonts, current_name: str
) -> None:
    """Draws the text input screen for creating a new profile."""
    screen.fill(BG_DARK)

    _draw_centered(screen, "CREATE NEW PROFILE", fonts.title_font, ACCENT_GREEN, 150)
    _draw_centered(screen, "Enter your name:", fonts.option_font, TEXT_PRIMARY, 250)

    # Draw the input box area
    input_rect = pygame.Rect(0, 0, 600, 60)
    input_rect.center = (config.WIDTH // 2, 350)

    # Draw a border that glows slightly
    pygame.draw.rect(screen, ACCENT_GREEN, input_rect, 2, border_radius=10)

    # Render the name typed so far
    # We add a "|" character at the end to act as a typing cursor
    name_surf = fonts.option_font.render(f"{current_name}|", True, (255, 255, 255))
    screen.blit(name_surf, (input_rect.x + 20, input_rect.y + 10))

    _draw_centered(
        screen,
        "ENTER: Confirm | ESC: Cancel",
        fonts.hint_font,
        DIM_TEXT,
        config.HEIGHT - 100,
    )
