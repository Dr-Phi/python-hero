from pathlib import Path
import pygame

# ============================================================
# PROJECT PATHS
# ============================================================

# Assumes config.py is in src/python_hero/
# .parents[2] goes: src/python_hero -> src -> python-hero/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = PROJECT_ROOT / "assets"

# Ensure directories exist so the game doesn't crash on first run
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# WINDOW CONFIG
# ============================================================

WIDTH = 1400
HEIGHT = 900
FPS = 60

# ============================================================
# GAMEPLAY GEOMETRY
# ============================================================

# Y increases upward in game-space logic
START_Y = 300
END_Y = -146

# Hit window thickness (Total window is 36 units)
HIT_HALF_HEIGHT = 18
HIT_TOP = END_Y + HIT_HALF_HEIGHT
HIT_BOTTOM = END_Y - HIT_HALF_HEIGHT

# Seconds a note takes to travel from START_Y to END_Y
LEAD_TIME = 4.0
NOTE_RADIUS = 14

# ============================================================
# LANE X POSITIONS (Perspective Transform)
# ============================================================

# Order: Y U I O P
LANE_START_X = [-29, -12, 6, 24, 46]
LANE_END_X = [-91, -43, 6, 53, 101]

# ============================================================
# COLORS (RGB)
# ============================================================

# UI & Background
BG_DARK = (10, 10, 14)  # Matches screens.py
BACKGROUND_COLOR = (15, 15, 20)
LANE_COLOR = (70, 70, 80)
HITBOX_COLOR = (120, 120, 140)
HITLINE_COLOR = (180, 180, 200)
UI_TEXT_COLOR = (230, 230, 230)
HINT_TEXT_COLOR = (180, 180, 200)

# Lane Colors (Y: Green, U: Red, I: Yellow, O: Blue, P: Orange)
LANE_COLORS = [
    (0, 220, 0),  # Y
    (220, 40, 40),  # U
    (240, 220, 0),  # I
    (40, 120, 255),  # O
    (255, 140, 0),  # P
]

# ============================================================
# VISUAL PROJECTION CONTROL
# ============================================================

SCALE = 5
X_SQUEEZE = 0.60
CENTER_X = WIDTH // 2

# Force hit line to be visible near bottom
HITLINE_SCREEN_Y = HEIGHT - 180

# Compute CENTER_Y so END_Y maps exactly to HITLINE_SCREEN_Y
CENTER_Y = HITLINE_SCREEN_Y + int(END_Y * SCALE)

# ============================================================
# ASCII SPLASH ART
# ============================================================

SPLASH_ART = [
    "█▀▀█ █  █ ▀▀█▀▀ █  █ █▀▀█ █▀▀▄   █  █ █▀▀ █▀▀█ █▀▀█ ",
    "█  █ █▄▄█   █   █▀▀█ █  █ █  █   █▀▀█ █▀▀ █▄▄▀ █  █ ",
    "█▀▀▀ ▄▄▄█   █   █  █ ▀▀▀▀ ▀  ▀   █  █ ▀▀▀ ▀ ▀▀ ▀▀▀▀ ",
    "",
    " ░▒▓█ Created by Dr-Phi █▓▒░",
]
