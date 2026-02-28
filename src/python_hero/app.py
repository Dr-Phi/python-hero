from __future__ import annotations

import time
import sys
import pygame
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Tuple

from . import config
from .songs import list_songs
from .charts import (
    list_charts,
    next_new_chart_path,
    load_chart_from_path,
    save_chart_to_path,
    delete_chart,
)
from .gameplay import Note, GameplayManager, spawn_notes, cleanup_notes
from . import screens
from . import render


@dataclass
class Message:
    text: str
    until_ts: float
    next_action: Optional[str] = None


class App:
    def __init__(self) -> None:
        pygame.init()
        pygame.mixer.init()

        self.screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
        self.clock = pygame.time.Clock()
        pygame.display.set_caption("Python Hero")

        self.gameplay_manager = GameplayManager()

        self.fonts = screens.Fonts(
            ascii_font=pygame.font.SysFont("consolas", 28),
            hint_font=pygame.font.SysFont("consolas", 22),
            title_font=pygame.font.SysFont("consolas", 34),
            option_font=pygame.font.SysFont("consolas", 26),
            ui_font=pygame.font.SysFont(None, 34),
        )

        self.state: str = "splash"
        self.message: Optional[Message] = None

        self.songs: List[Path] = list_songs(config.ASSETS_DIR)
        self.song_index: int = 0
        self.song_path: Optional[Path] = None
        self.charts: List[Path] = []
        self.chart_index: int = 0
        self.current_chart_path: Optional[Path] = None
        self.pending_delete: Optional[Path] = None

        self.mode: str = "idle"
        self.score: int = 0
        self.recorded: List[Tuple[int, float]] = []
        self.active_notes: List[Note] = []
        self.spawn_index: int = 0

        self.pause_index: int = 0
        self.pause_countdown_until: Optional[float] = None
        self.pause_countdown_value: int = 0

    def run(self) -> None:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle_event(event)

            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(config.FPS)
        pygame.quit()

    def song_time(self) -> float:
        return self.gameplay_manager.current_song_time

    # --- Actions ---

    def start_record(self) -> None:
        if not self.song_path:
            return
        self.message = None
        self.mode = "record"
        self.state = "game"
        self.score = 0
        self.recorded = []
        self.active_notes.clear()
        self.spawn_index = 0
        self.current_chart_path = next_new_chart_path(self.song_path)
        pygame.mixer.music.load(str(self.song_path))
        pygame.mixer.music.play()
        self.gameplay_manager.start_game()

    def start_play(self, chart: List[Tuple[int, float]]) -> None:
        if not self.song_path:
            return
        self.message = None
        self.mode = "play"
        self.state = "game"
        self.score = 0
        self.recorded = list(chart)
        self.active_notes.clear()
        self.spawn_index = 0
        pygame.mixer.music.load(str(self.song_path))
        pygame.mixer.music.play()
        self.gameplay_manager.start_game()

    def perform_save(self) -> None:
        if self.mode == "record" and self.current_chart_path:
            save_chart_to_path(self.current_chart_path, self.recorded)
            self.show_message(
                f"Saved: {self.current_chart_path.name}", 2.0, "chart_choice"
            )
            pygame.mixer.music.stop()
            self.mode = "idle"

    def execute_delete(self) -> None:
        if self.pending_delete:
            success = delete_chart(self.pending_delete)
            if success:
                self.show_message(f"Deleted {self.pending_delete.name}", 1.5)
            else:
                self.show_message("Error deleting file", 2.0)

            self.pending_delete = None
            self.charts = list_charts(self.song_path)
            self.chart_index = 0
            self.state = "chart_choice"

    def pause_game(self) -> None:
        if self.state != "game":
            return
        pygame.mixer.music.pause()
        self.gameplay_manager.pause()
        self.pause_index = 0
        self.state = "pause"

    def resume_game(self) -> None:
        pygame.mixer.music.unpause()
        self.gameplay_manager.resume()
        self.state = "game"

    def start_pause_countdown(self) -> None:
        self.pause_countdown_until = time.time() + 3.0
        self.pause_countdown_value = 3
        self.state = "pause_countdown"

    def exit_to_song_select(self) -> None:
        pygame.mixer.music.stop()
        self.state = "song_select"
        self.mode = "idle"
        self.song_path = None

    def show_message(
        self, text: str, seconds: float, next_action: Optional[str] = None
    ) -> None:
        self.message = Message(
            text=text, until_ts=time.time() + seconds, next_action=next_action
        )
        self.state = "message"

    # --- Event Handling ---

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        if self.state == "splash":
            if event.key == pygame.K_RETURN:
                self.state = "song_select"
            elif event.key == pygame.K_ESCAPE:
                self.state = "quit_confirm"

        elif self.state == "song_select":
            if event.key == pygame.K_ESCAPE:
                self.state = "quit_confirm"
            elif event.key == pygame.K_UP:
                self.song_index = (self.song_index - 1) % len(self.songs)
            elif event.key == pygame.K_DOWN:
                self.song_index = (self.song_index + 1) % len(self.songs)
            elif event.key == pygame.K_RETURN:
                if self.songs:
                    self.song_path = self.songs[self.song_index]
                    self.charts = list_charts(self.song_path)
                    self.chart_index = 0
                    self.state = "chart_choice"

        elif self.state == "chart_choice":
            if event.key == pygame.K_ESCAPE:
                self.state = "song_select"
                return

            if event.key == pygame.K_UP and self.charts:
                self.chart_index = (self.chart_index - 1) % len(self.charts)
            elif event.key == pygame.K_DOWN and self.charts:
                self.chart_index = (self.chart_index + 1) % len(self.charts)
            elif event.key == pygame.K_r:
                self.start_record()
                return
            elif event.key == pygame.K_d and self.charts:
                self.pending_delete = self.charts[self.chart_index]
                self.state = "confirm_delete"
                return
            elif event.key == pygame.K_RETURN:
                if not self.charts:
                    self.show_message("No charts. Press 'R' to record.", 2.0)
                else:
                    chosen = self.charts[self.chart_index]
                    self.current_chart_path = chosen
                    self.start_play(load_chart_from_path(chosen))

        elif self.state == "game":
            if event.key == pygame.K_ESCAPE:
                self.pause_game()
            elif event.key == pygame.K_s and self.mode == "record":
                self.perform_save()
            elif event.key in config.KEYS:
                self._handle_lane_input(config.KEYS.index(event.key))

        elif self.state == "pause":
            opts_count = 3 if self.mode == "play" else 4
            if event.key == pygame.K_ESCAPE:
                self.start_pause_countdown()
            elif event.key == pygame.K_UP:
                self.pause_index = (self.pause_index - 1) % opts_count
            elif event.key == pygame.K_DOWN:
                self.pause_index = (self.pause_index + 1) % opts_count
            elif event.key == pygame.K_RETURN:
                self._handle_pause_selection()

        elif self.state in ("quit_confirm", "confirm_delete"):
            if event.key == pygame.K_RETURN:
                if self.state == "quit_confirm":
                    pygame.quit()
                    sys.exit()
                else:
                    self.execute_delete()
            elif event.key == pygame.K_ESCAPE:
                self.state = (
                    "song_select" if self.state == "quit_confirm" else "chart_choice"
                )
                self.pending_delete = None

    def _handle_lane_input(self, lane: int) -> None:
        now = self.song_time()
        if self.mode == "record":
            self.recorded.append((lane, now))
        elif self.mode == "play":
            for n in list(self.active_notes):
                _, y = n.position(now)
                if n.lane == lane and (config.HIT_BOTTOM <= y <= config.HIT_TOP):
                    self.score += 1
                    self.active_notes.remove(n)
                    break

    def _handle_pause_selection(self) -> None:
        options = (
            ["Resume", "Restart", "Exit"]
            if self.mode == "play"
            else ["Resume", "Save Chart", "Start Over", "Exit"]
        )
        choice = options[self.pause_index]
        if choice == "Resume":
            self.start_pause_countdown()
        elif choice == "Save Chart":
            self.perform_save()
        elif choice == "Exit":
            self.exit_to_song_select()
        elif choice in ("Restart", "Start Over"):
            if self.mode == "play":
                self.start_play(load_chart_from_path(self.current_chart_path))
            else:
                self.start_record()

    def update(self) -> None:
        if self.state == "pause_countdown" and self.pause_countdown_until:
            rem = self.pause_countdown_until - time.time()
            if rem <= 0:
                self.resume_game()
            else:
                self.pause_countdown_value = int(rem) + 1
        elif self.state == "message" and self.message:
            if time.time() >= self.message.until_ts:
                self.state = self.message.next_action or "chart_choice"
                self.message = None
        elif self.state == "game":
            now = self.song_time()
            if self.mode == "play":
                self.spawn_index = spawn_notes(
                    self.recorded, self.active_notes, now, self.spawn_index
                )
                cleanup_notes(self.active_notes, now)

    def draw(self) -> None:
        # 1. Menu screens (Static)
        if self.state == "splash":
            screens.draw_splash(self.screen, self.fonts)
            return
        elif self.state == "song_select":
            screens.draw_song_select(
                self.screen, self.fonts, self.songs, self.song_index
            )
            return
        elif self.state == "quit_confirm":
            screens.draw_song_select(
                self.screen, self.fonts, self.songs, self.song_index
            )
            screens.draw_quit_confirm(self.screen, self.fonts)
            return
        elif self.state == "chart_choice":
            screens.draw_chart_choice(
                self.screen, self.fonts, self.song_path, self.charts, self.chart_index
            )
            return
        elif self.state == "confirm_delete":
            screens.draw_chart_choice(
                self.screen, self.fonts, self.song_path, self.charts, self.chart_index
            )
            screens.draw_confirm_delete(
                self.screen,
                self.fonts,
                self.pending_delete.name if self.pending_delete else "",
            )
            return

        # 2. Gameplay & Overlays
        # Only pass message_text if we are explicitly in the "message" state
        msg_to_render = (
            self.message.text if (self.state == "message" and self.message) else None
        )

        render.draw_game(
            screen=self.screen,
            fonts=self.fonts,
            mode=self.mode,
            score=self.score,
            recorded_count=len(self.recorded),
            song_path=self.song_path,
            active_notes=self.active_notes,
            now=self.song_time(),
            message_text=msg_to_render,  # FIX: Use the filtered variable
        )

        # Overlays on top of the game view
        if self.state == "pause":
            screens.draw_pause_menu(
                self.screen, self.fonts, self.mode, self.pause_index
            )
        elif self.state == "pause_countdown":
            screens.draw_pause_countdown(
                self.screen, self.fonts, self.pause_countdown_value
            )
        # --- 1. Static Menu Screens ---
        if self.state == "splash":
            screens.draw_splash(self.screen, self.fonts)
            return
        elif self.state == "song_select":
            screens.draw_song_select(
                self.screen, self.fonts, self.songs, self.song_index
            )
            return
        elif self.state == "quit_confirm":
            screens.draw_song_select(
                self.screen, self.fonts, self.songs, self.song_index
            )
            screens.draw_quit_confirm(self.screen, self.fonts)
            return
        elif self.state == "chart_choice":
            screens.draw_chart_choice(
                self.screen, self.fonts, self.song_path, self.charts, self.chart_index
            )
            return
        elif self.state == "confirm_delete":
            screens.draw_chart_choice(
                self.screen, self.fonts, self.song_path, self.charts, self.chart_index
            )
            screens.draw_confirm_delete(
                self.screen,
                self.fonts,
                self.pending_delete.name if self.pending_delete else "",
            )
            return

        # --- 2. Gameplay & Overlays (Pause / Countdown) ---
        # We draw the game background for Game, Pause, and Countdown states
        render.draw_game(
            screen=self.screen,
            fonts=self.fonts,
            mode=self.mode,
            score=self.score,
            recorded_count=len(self.recorded),
            song_path=self.song_path,
            active_notes=self.active_notes,
            now=self.song_time(),
            message_text=self.message.text if self.message else None,
        )

        # Draw the specific UI layer ON TOP of the game view
        if self.state == "pause":
            screens.draw_pause_menu(
                self.screen, self.fonts, self.mode, self.pause_index
            )
        elif self.state == "pause_countdown":
            screens.draw_pause_countdown(
                self.screen, self.fonts, self.pause_countdown_value
            )
