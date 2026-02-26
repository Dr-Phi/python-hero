# ===== LINE 1 =====
from pathlib import Path
import pygame

# ============================================================
# ===== LINE 5 : PROJECT PATHS ===============================
# ============================================================

# PROJECT_ROOT -> python-hero/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# assets folder lives at: python-hero/assets/
ASSETS_DIR = PROJECT_ROOT / "assets"


# ============================================================
# ===== LINE 15 : WINDOW CONFIG ==============================
# ============================================================

WIDTH = 1400
HEIGHT = 900
FPS = 60


# ============================================================
# ===== LINE 23 : LANE GEOMETRY (GAME SPACE) ================
# ============================================================

# Y increases upward in game-space
# START_Y = where notes spawn
# END_Y = center of hit line

START_Y = 300
END_Y = -146

# Hit window thickness
HIT_HALF_HEIGHT = 18
HIT_TOP = END_Y + HIT_HALF_HEIGHT
HIT_BOTTOM = END_Y - HIT_HALF_HEIGHT


# ============================================================
# ===== LINE 40 : LANE X POSITIONS ===========================
# ============================================================

# Order: Y U I O P

LANE_START_X = [-29, -12, 6, 24, 46]
LANE_END_X   = [-91, -43, 6, 53, 101]


# ============================================================
# ===== LINE 50 : TIMING =====================================
# ============================================================

# Seconds a note takes to travel from START_Y to END_Y
LEAD_TIME = 4       #(increase = slower/easier)
NOTE_RADIUS = 14


# ============================================================
# ===== LINE 60 : INPUT ======================================
# ============================================================

KEYS = [
    pygame.K_y,
    pygame.K_u,
    pygame.K_i,
    pygame.K_o,
    pygame.K_p,
]

KEY_NAMES = ["Y", "U", "I", "O", "P"]


# ============================================================
# ===== LINE 72 : COLORS =====================================
# ============================================================

# Y green, U red, I yellow, O blue, P orange
LANE_COLORS = [
    (0, 220, 0),      # Y
    (220, 40, 40),    # U
    (240, 220, 0),    # I
    (40, 120, 255),   # O
    (255, 140, 0),    # P
]

BACKGROUND_COLOR = (15, 15, 20)
LANE_COLOR = (70, 70, 80)
HITBOX_COLOR = (120, 120, 140)
HITLINE_COLOR = (180, 180, 200)
UI_TEXT_COLOR = (230, 230, 230)
HINT_TEXT_COLOR = (180, 180, 200)


# ============================================================
# ===== LINE 90 : VISUAL LAYOUT CONTROL ======================
# ============================================================

# Controls how stretched the fretboard looks
SCALE = 5

# < 1.0 = lanes closer together
X_SQUEEZE = 0.60

CENTER_X = WIDTH // 2

# Force hit line to be visible near bottom
HITLINE_SCREEN_Y = HEIGHT - 180

# Compute CENTER_Y so END_Y maps exactly to HITLINE_SCREEN_Y
CENTER_Y = HITLINE_SCREEN_Y + int(END_Y * SCALE)


# ============================================================
# ===== LINE 110 : ASCII SPLASH ART ==========================
# ============================================================

SPLASH_ART = [
    "█▀▀█ █  █ ▀▀█▀▀ █  █ █▀▀█ █▀▀▄   █  █ █▀▀ █▀▀█ █▀▀█ ",
    "█  █ █▄▄█   █   █▀▀█ █  █ █  █   █▀▀█ █▀▀ █▄▄▀ █  █ ",
    "█▀▀▀ ▄▄▄█   █   █  █ ▀▀▀▀ ▀  ▀   █  █ ▀▀▀ ▀ ▀▀ ▀▀▀▀ ",
    "",
    " ░▒▓█ Created by Dr-Phi █▓▒░",
]