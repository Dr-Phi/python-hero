# ===== LINE 1 (src/python_hero/app.py) =====
from __future__ import annotations

# ===== LINE 4 =====
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# ===== LINE 10 =====
import pygame

# ===== LINE 12 =====
from . import config
from .songs import list_songs
from .charts import (
    list_charts,
    next_new_chart_path,
    load_chart_from_path,
    save_chart_to_path,
    delete_chart,
)
from .gameplay import Note
from . import screens
from . import render


# ===== LINE 21 =====
@dataclass
class Message:
    text: str
    until_ts: float
    # action after message expires:
    # "to_song_select" | "to_chart_choice" | "to_game_record" | "to_game" | None
    next_action: Optional[str] = None


# ===== LINE 30 =====
class App:
    # ===== LINE 32 =====
    def __init__(self) -> None:
        pygame.init()
        pygame.mixer.init()

        self.screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
        self.clock = pygame.time.Clock()
        pygame.display.set_caption("Python Hero")

        # Fonts bundle used by screens + render
        self.fonts = screens.Fonts(
            ascii_font=pygame.font.SysFont("consolas", 28),
            hint_font=pygame.font.SysFont("consolas", 22),
            title_font=pygame.font.SysFont("consolas", 34),
            option_font=pygame.font.SysFont("consolas", 26),
            ui_font=pygame.font.SysFont(None, 34),
        )

        # State machine
        self.state: str = (
            "splash"  # splash -> song_select -> chart_choice -> confirm_delete -> message -> game
        )
        self.message: Optional[Message] = None

        # Song selection
        self.songs: list[Path] = list_songs(config.ASSETS_DIR)
        self.song_index: int = 0
        self.song_path: Optional[Path] = None

        # Charts for selected song
        self.charts: list[Path] = []
        self.chart_index: int = 0
        self.current_chart_path: Optional[Path] = None  # where RECORD saves
        self.pending_delete: Optional[Path] = None  # chart awaiting confirmation

        # Gameplay state
        self.mode: str = "idle"  # idle | record | play
        self.score: int = 0
        self.recorded: list[tuple[int, float]] = []
        self.active_notes: list[Note] = []
        self.spawn_index: int = 0

        # Song clock (set when song starts)
        self.t0: Optional[float] = None

    # ===== LINE 77 =====
    def run(self) -> None:
        # ===== LINE 79 =====
        running = True
        while running:
            # ===== LINE 82 =====
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    self.handle_event(event)

            # ===== LINE 91 =====
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(config.FPS)

        # ===== LINE 97 =====
        pygame.quit()

    # ===== LINE 100 =====
    def song_time(self) -> float:
        # ===== LINE 102 =====
        if self.t0 is None:
            return 0.0
        return time.time() - self.t0

    # ===== LINE 106 =====
    def restart_song_clock(self) -> None:
        # ===== LINE 108 =====
        pygame.mixer.music.stop()
        pygame.mixer.music.play()
        self.t0 = time.time()

    # ===== LINE 113 =====
    def start_record(self) -> None:
        # ===== LINE 115 =====
        assert self.song_path is not None

        # ===== LINE 118 =====
        self.mode = "record"
        self.state = "game"
        self.score = 0
        self.recorded = []
        self.active_notes.clear()
        self.spawn_index = 0

        # ===== LINE 126 =====
        pygame.mixer.music.load(str(self.song_path))
        pygame.mixer.music.play()
        self.t0 = time.time()

    # ===== LINE 132 =====
    def start_play(self, chart: list[tuple[int, float]]) -> None:
        # ===== LINE 134 =====
        assert self.song_path is not None

        # ===== LINE 137 =====
        self.mode = "play"
        self.state = "game"
        self.score = 0
        self.recorded = list(chart)
        self.active_notes.clear()
        self.spawn_index = 0

        # ===== LINE 145 =====
        pygame.mixer.music.load(str(self.song_path))
        pygame.mixer.music.play()
        self.t0 = time.time()

    # ===== LINE 151 =====
    def show_message(
        self, text: str, seconds: float, next_action: Optional[str] = None
    ) -> None:
        # ===== LINE 153 =====
        self.message = Message(
            text=text, until_ts=time.time() + seconds, next_action=next_action
        )
        self.state = "message"

    # ===== LINE 158 =====
    def handle_event(self, event: pygame.event.Event) -> None:
        # ===== LINE 160 =====
        if event.type != pygame.KEYDOWN:
            return

        # ===== LINE 164 =====
        if self.state == "splash":
            if event.key == pygame.K_SPACE:
                self.state = "song_select"
            return

        # ===== LINE 170 =====
        if self.state == "song_select":
            if not self.songs:
                return

            if event.key == pygame.K_UP:
                self.song_index = (self.song_index - 1) % len(self.songs)
            elif event.key == pygame.K_DOWN:
                self.song_index = (self.song_index + 1) % len(self.songs)
            elif event.key == pygame.K_RETURN:
                self.song_path = self.songs[self.song_index]
                self.charts = list_charts(self.song_path)
                self.chart_index = 0
                self.pending_delete = None
                self.state = "chart_choice"
            return

        # ===== LINE 184 =====
        if self.state == "chart_choice":
            if event.key == pygame.K_BACKSPACE:
                self.state = "song_select"
                self.song_path = None
                self.charts = []
                self.chart_index = 0
                self.current_chart_path = None
                self.pending_delete = None
                return
            if self.song_path is None:
                self.state = "song_select"
                return

            # refresh list (in case files changed)
            self.charts = list_charts(self.song_path)
            if self.chart_index >= len(self.charts):
                self.chart_index = max(0, len(self.charts) - 1)

            if event.key == pygame.K_UP and self.charts:
                self.chart_index = (self.chart_index - 1) % len(self.charts)
                return
            if event.key == pygame.K_DOWN and self.charts:
                self.chart_index = (self.chart_index + 1) % len(self.charts)
                return

            # Record NEW chart
            if event.key == pygame.K_r:
                self.current_chart_path = next_new_chart_path(self.song_path)
                self.start_record()
                return

            # Load selected chart (L or Enter)
            if event.key in (pygame.K_l, pygame.K_RETURN):
                if not self.charts:
                    self.show_message(
                        "No chart found. Entering recording mode...",
                        3.0,
                        next_action="to_game_record",
                    )
                    return

                chosen = self.charts[self.chart_index]
                chart = load_chart_from_path(chosen)
                if chart:
                    self.current_chart_path = chosen
                    self.start_play(chart)
                else:
                    self.show_message(
                        "Chart is empty/corrupt. Entering recording mode...",
                        3.0,
                        next_action="to_game_record",
                    )
                return

            # Delete selected chart
            if event.key == pygame.K_d and self.charts:
                self.pending_delete = self.charts[self.chart_index]
                self.state = "confirm_delete"
                return

            return

        # ===== LINE 200 =====
        if self.state == "message":
            # ignore keypresses during message overlay
            return

        if self.state == "confirm_delete":
            if event.key in (pygame.K_n, pygame.K_BACKSPACE):
                self.pending_delete = None
                self.state = "chart_choice"
                return
            if event.key == pygame.K_y and self.pending_delete is not None:
                ok = delete_chart(self.pending_delete)
                name = self.pending_delete.name
                self.pending_delete = None
                self.charts = list_charts(self.song_path) if self.song_path else []
                self.chart_index = 0
                self.show_message(
                    ("Deleted: " + name) if ok else ("Could not delete: " + name),
                    1.6,
                    next_action="to_chart_choice",
                )
                return

            if event.key == pygame.K_n:
                self.pending_delete = None
                self.state = "chart_choice"
                return

            return

        # ===== LINE 205 =====
        if self.state == "game":
            # ===== LINE 207 =====
            # Save chart (S) while recording
            if (
                event.key == pygame.K_s
                and self.mode == "record"
                and self.song_path is not None
            ):
                if self.current_chart_path is None:
                    self.current_chart_path = next_new_chart_path(self.song_path)
                save_chart_to_path(self.current_chart_path, self.recorded)
                self.show_message("Chart saved!", 1.5, next_action="to_game")
                return

            # ===== LINE 214 =====
            # In record mode: SPACE switches to play using what you just recorded
        if (
            event.key == pygame.K_SPACE
            and self.mode == "record"
            and self.song_path is not None
        ):
            self.start_play(self.recorded)
            return

            # ===== LINE 220 =====
            # Lane keys: Y U I O P
        if event.key in config.KEYS:
            lane = config.KEYS.index(event.key)

            if self.mode == "record":
                self.recorded.append((lane, self.song_time()))

            elif self.mode == "play":
                now = self.song_time()
                # Hit detection in GAME space (y)
                for n in list(self.active_notes):
                    _, y = n.position(now)
                    if n.lane == lane and (config.HIT_BOTTOM <= y <= config.HIT_TOP):
                        self.score += 1
                        self.active_notes.remove(n)
                        break

    # ===== LINE 243 =====
    def update(self) -> None:
        # ===== LINE 245 =====
        if self.state == "message" and self.message is not None:
            if time.time() >= self.message.until_ts:
                action = self.message.next_action
                self.message = None

                # ===== LINE 252 =====
                if action == "to_game_record":
                    if self.song_path is not None:
                        self.current_chart_path = next_new_chart_path(self.song_path)
                    self.start_record()
                elif action == "to_game":
                    self.state = "game"
                elif action == "to_chart_choice":
                    self.state = "chart_choice"
                else:
                    # default return to chart choice if we have a song, else song select
                    self.state = (
                        "chart_choice" if self.song_path is not None else "song_select"
                    )
            return

        # ===== LINE 262 =====
        if self.state != "game":
            return

        # ===== LINE 266 =====
        if self.mode != "play":
            return

        now = self.song_time()

        # ===== LINE 272 =====
        # Spawn notes when they are LEAD_TIME seconds away from hit time
        while self.spawn_index < len(self.recorded):
            lane, t_note = self.recorded[self.spawn_index]
            if now >= t_note - config.LEAD_TIME:
                self.active_notes.append(Note(lane, t_note))
                self.spawn_index += 1
            else:
                break

        # ===== LINE 283 =====
        # Cleanup notes after they pass far beyond hit window (GAME space)
        for n in list(self.active_notes):
            _, y = n.position(now)
            if y < (config.HIT_BOTTOM - 220):
                self.active_notes.remove(n)

    # ===== LINE 292 =====
    def draw(self) -> None:
        # ===== LINE 294 =====
        if self.state == "splash":
            screens.draw_splash(self.screen, self.fonts)
            return

        # ===== LINE 299 =====
        if self.state == "song_select":
            screens.draw_song_select(
                screen=self.screen,
                fonts=self.fonts,
                songs=self.songs,
                selected_index=self.song_index,
            )
            return

        # ===== LINE 309 =====
        if self.state == "chart_choice":
            screens.draw_chart_choice(
                screen=self.screen,
                fonts=self.fonts,
                song_path=self.song_path,
                charts=self.charts,
                selected_index=self.chart_index,
            )
            return
        if self.state == "confirm_delete":
            screens.draw_confirm_delete(
                screen=self.screen,
                fonts=self.fonts,
                chart_name=(self.pending_delete.name if self.pending_delete else ""),
            )
            return

        # ===== LINE 320 =====
        # game or message overlay: draw the game view
        now = self.song_time()
        render.draw_game(
            screen=self.screen,
            fonts=self.fonts,
            mode=self.mode,
            score=self.score,
            recorded_count=len(self.recorded),
            song_path=self.song_path,
            active_notes=self.active_notes,
            now=now,
            message_text=(
                self.message.text
                if (self.state == "message" and self.message)
                else None
            ),
        )
