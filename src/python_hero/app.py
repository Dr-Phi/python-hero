from __future__ import annotations
import time, sys, pygame
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Tuple

from . import config, screens, render
from .songs import list_songs
from .charts import (
    list_charts,
    next_new_chart_path,
    load_chart_from_path,
    save_chart_to_path,
    delete_chart,
)
from .gameplay import Note, GameplayManager, spawn_notes, cleanup_notes
from .data_manager import DataManager, Profile


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
        self.fonts = screens.Fonts.default()
        self.data = DataManager()
        self.current_profile = self.data.load_profile("Guest")

        # Application State
        self.state = "splash"
        self.mode = "idle"
        self.menu_index = 0
        self.message: Optional[Message] = None

        # Song & Chart State
        self.songs = list_songs(config.ASSETS_DIR)
        self.song_index = 0
        self.song_path: Optional[Path] = None
        self.charts: List[Path] = []
        self.chart_index = 0
        self.current_chart_path: Optional[Path] = None

        # Deletion & Settings
        self.pending_delete: Optional[Path] = None
        self.pending_delete_name: Optional[str] = None
        self.rebinding_index = -1
        self.new_profile_name = ""

        # Gameplay State
        self.score = 0
        self.final_hits = 0
        self.final_total = 0
        self.recorded: List[Tuple[int, float]] = []
        self.active_notes: List[Note] = []
        self.spawn_index = 0

        # Pause State
        self.pause_index = 0
        self.pause_countdown_until: Optional[float] = None
        self.pause_countdown_value = 0

    def run(self) -> None:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                self.handle_event(event)
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(config.FPS)

    def quit(self):
        pygame.quit()
        sys.exit()

    def song_time(self) -> float:
        return self.gameplay_manager.current_song_time

    # --- Gameplay Actions ---

    def start_record(self) -> None:
        if not self.song_path:
            return
        self.mode, self.state, self.score, self.recorded = "record", "game", 0, []
        self._prepare_engine(self.song_path)
        self.current_chart_path = next_new_chart_path(self.song_path)

    def start_play(self, chart_data: List[Tuple[int, float]]) -> None:
        if not self.song_path:
            return
        self.mode, self.state, self.score, self.recorded = (
            "play",
            "game",
            0,
            list(chart_data),
        )
        self._prepare_engine(self.song_path)

    def _prepare_engine(self, path: Path):
        self.active_notes.clear()
        self.spawn_index = 0
        pygame.mixer.music.load(str(path))
        pygame.mixer.music.play()
        self.gameplay_manager.start_game()

    def finalize_game_results(self) -> None:
        if not self.current_chart_path:
            self.state = "main_menu"
            return

        if self.mode == "record":
            save_chart_to_path(self.current_chart_path, self.recorded)
            self.show_message(
                f"Saved: {self.current_chart_path.name}", 2.0, "chart_choice"
            )
            return

        self.final_hits = self.score
        self.final_total = len(self.recorded)
        self.data.update_records(
            self.current_chart_path.name,
            self.current_profile,
            self.final_hits,
            self.final_total,
        )
        self.state = "results"
        pygame.mixer.music.stop()

    def show_message(
        self, text: str, seconds: float, next_action: Optional[str] = None
    ) -> None:
        self.message = Message(
            text=text, until_ts=time.time() + seconds, next_action=next_action
        )
        self.state = "message"

    def pause_game(self) -> None:
        pygame.mixer.music.pause()
        self.gameplay_manager.pause()
        self.pause_index, self.state = 0, "pause"

    def resume_game(self) -> None:
        pygame.mixer.music.unpause()
        self.gameplay_manager.resume()
        self.state = "game"

    def start_pause_countdown(self) -> None:
        self.pause_countdown_until = time.time() + 3.0
        self.pause_countdown_value = 3
        self.state = "pause_countdown"

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

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        s = self.state

        if s == "splash":
            if event.key == pygame.K_RETURN:
                self.state, self.menu_index = "main_menu", 0
            elif event.key == pygame.K_ESCAPE:
                self.state = "quit_confirm"

        elif s == "main_menu":
            if event.key == pygame.K_UP:
                self.menu_index = (self.menu_index - 1) % 5
            elif event.key == pygame.K_DOWN:
                self.menu_index = (self.menu_index + 1) % 5
            elif event.key == pygame.K_RETURN:
                choices = [
                    "song_select",
                    "settings",
                    "profile_select",
                    "high_scores",
                    "quit_confirm",
                ]
                self.state = choices[self.menu_index]
                self.menu_index = 0

        elif s == "song_select":
            if event.key == pygame.K_ESCAPE:
                self.state, self.menu_index = "main_menu", 0
            elif event.key == pygame.K_UP:
                self.song_index = (self.song_index - 1) % len(self.songs)
            elif event.key == pygame.K_DOWN:
                self.song_index = (self.song_index + 1) % len(self.songs)
            elif event.key == pygame.K_RETURN and self.songs:
                self.song_path = self.songs[self.song_index]
                self.charts = list_charts(self.song_path)
                self.state, self.chart_index = "chart_choice", 0

        elif s == "chart_choice":
            count = len(self.charts) or 1
            if event.key == pygame.K_UP:
                self.chart_index = (self.chart_index - 1) % count
            elif event.key == pygame.K_DOWN:
                self.chart_index = (self.chart_index + 1) % count
            elif event.key == pygame.K_ESCAPE:
                self.state = "song_select"
            elif event.key == pygame.K_r:
                self.start_record()
            elif event.key == pygame.K_RETURN:
                if self.charts and self.chart_index < len(self.charts):
                    self.current_chart_path = self.charts[self.chart_index]
                    self.start_play(load_chart_from_path(self.current_chart_path))
                else:
                    self.start_record()
            elif event.key == pygame.K_d and self.charts:
                self.pending_delete, self.state = (
                    self.charts[self.chart_index],
                    "confirm_delete",
                )
            elif event.key == pygame.K_x and self.charts:
                self.pending_delete, self.state = (
                    self.charts[self.chart_index],
                    "confirm_reset_single",
                )

        elif s == "game":
            if event.key == pygame.K_ESCAPE:
                self.pause_game()
            elif event.key in self.current_profile.keys:
                self._handle_lane_input(self.current_profile.keys.index(event.key))

        elif s == "results":
            if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                self.score, self.active_notes, self.state = 0, [], "chart_choice"

        elif s == "pause":
            opts_count = 3 if self.mode == "play" else 4
            if event.key == pygame.K_UP:
                self.pause_index = (self.pause_index - 1) % opts_count
            elif event.key == pygame.K_DOWN:
                self.pause_index = (self.pause_index + 1) % opts_count
            elif event.key == pygame.K_ESCAPE:
                self.start_pause_countdown()
            elif event.key == pygame.K_RETURN:
                opts = (
                    ["Resume", "Restart", "Exit"]
                    if self.mode == "play"
                    else ["Resume", "Save Chart", "Start Over", "Exit"]
                )
                choice = opts[self.pause_index]
                if choice == "Resume":
                    self.start_pause_countdown()
                elif choice == "Save Chart":
                    save_chart_to_path(self.current_chart_path, self.recorded)
                    self.show_message("Chart Saved!", 1.0, "chart_choice")
                elif choice == "Exit":
                    pygame.mixer.music.stop()
                    self.state = "song_select"
                elif choice in ("Restart", "Start Over"):
                    if self.mode == "play":
                        self.start_play(load_chart_from_path(self.current_chart_path))
                    else:
                        self.start_record()

        elif s == "settings":
            if self.rebinding_index != -1:
                if event.key != pygame.K_ESCAPE:
                    self.current_profile.keys[self.rebinding_index] = event.key
                    self.rebinding_index = (
                        self.rebinding_index + 1 if self.rebinding_index < 4 else -1
                    )
                else:
                    self.rebinding_index = -1
                return
            if event.key == pygame.K_UP:
                self.menu_index = (self.menu_index - 1) % 5
            elif event.key == pygame.K_DOWN:
                self.menu_index = (self.menu_index + 1) % 5
            elif event.key == pygame.K_RETURN:
                self.rebinding_index = self.menu_index
            elif event.key == pygame.K_r:
                # Revert to the default keys defined in the Profile dataclass
                self.current_profile.keys = [
                    pygame.K_y,
                    pygame.K_u,
                    pygame.K_i,
                    pygame.K_o,
                    pygame.K_p,
                ]
                self.show_message("Keys Reset to Default", 1.0, "settings")
            elif event.key == pygame.K_ESCAPE:
                self.data.save_profile(self.current_profile)
                self.state, self.menu_index = "main_menu", 1

        elif s == "high_scores":
            if event.key == pygame.K_ESCAPE:
                self.state, self.menu_index = "main_menu", 3
            elif event.key == pygame.K_c:
                self.state = "confirm_reset_all"

        elif s == "profile_select":
            names = self.data.list_profile_names()
            count = len(names) + 1
            if event.key == pygame.K_UP:
                self.menu_index = (self.menu_index - 1) % count
            elif event.key == pygame.K_DOWN:
                self.menu_index = (self.menu_index + 1) % count
            elif event.key == pygame.K_ESCAPE:
                self.state, self.menu_index = "main_menu", 2
            elif event.key == pygame.K_d and self.menu_index < len(names):
                target = names[self.menu_index]
                if target == self.current_profile.name:
                    self.show_message(
                        "Cannot delete active profile!", 1.5, "profile_select"
                    )
                else:
                    self.pending_delete_name, self.state = (
                        target,
                        "confirm_profile_delete",
                    )
            elif event.key == pygame.K_RETURN:
                if self.menu_index < len(names):
                    self.current_profile = self.data.load_profile(
                        names[self.menu_index]
                    )
                    self.show_message(
                        f"Logged in: {self.current_profile.name}", 1.0, "main_menu"
                    )
                else:
                    self.new_profile_name, self.state = "", "create_profile"

        elif s == "create_profile":
            if event.key == pygame.K_RETURN and self.new_profile_name.strip():
                new_p = Profile(name=self.new_profile_name.strip())
                self.data.save_profile(new_p)
                self.current_profile = new_p
                self.show_message(f"Welcome, {new_p.name}!", 1.5, "main_menu")
            elif event.key == pygame.K_ESCAPE:
                self.state = "profile_select"
            elif event.key == pygame.K_BACKSPACE:
                self.new_profile_name = self.new_profile_name[:-1]
            elif len(self.new_profile_name) < 15 and (
                event.unicode.isalnum() or event.key == pygame.K_SPACE
            ):
                self.new_profile_name += event.unicode

        elif s == "confirm_delete":
            if event.key == pygame.K_RETURN:
                if delete_chart(self.pending_delete):
                    if self.pending_delete.name in self.current_profile.stats.song_data:
                        del self.current_profile.stats.song_data[
                            self.pending_delete.name
                        ]
                        self.data.save_profile(self.current_profile)
                self.charts = list_charts(self.song_path)
                self.state, self.chart_index = "chart_choice", 0
            elif event.key == pygame.K_ESCAPE:
                self.state = "chart_choice"

        elif s == "confirm_reset_single":
            if event.key == pygame.K_RETURN:
                self.data.reset_chart_score(
                    self.pending_delete.name, self.current_profile
                )
                self.state = "chart_choice"
            elif event.key == pygame.K_ESCAPE:
                self.state = "chart_choice"

        elif s == "confirm_reset_all":
            if event.key == pygame.K_RETURN:
                self.data.reset_all_scores(self.current_profile)
                self.show_message("RECORDS WIPED", 1.5, "main_menu")
            elif event.key == pygame.K_ESCAPE:
                self.state = "high_scores"

        elif s == "confirm_profile_delete":
            if event.key == pygame.K_RETURN:
                self.data.delete_profile(self.pending_delete_name)
                self.state, self.menu_index = "profile_select", 0
            elif event.key == pygame.K_ESCAPE:
                self.state = "profile_select"

        elif s == "quit_confirm":
            if event.key == pygame.K_RETURN:
                self.quit()
            elif event.key == pygame.K_ESCAPE:
                self.state, self.menu_index = "main_menu", 4

    def update(self) -> None:
        now = time.time()
        if self.state == "message" and self.message:
            if now >= self.message.until_ts:
                self.state, self.message = self.message.next_action or "main_menu", None
            return
        elif self.state == "pause_countdown":
            rem = self.pause_countdown_until - now
            if rem <= 0:
                self.resume_game()
            else:
                self.pause_countdown_value = int(rem) + 1
        elif self.state == "game":
            if not pygame.mixer.music.get_busy():
                self.finalize_game_results()
                return
            t = self.song_time()
            if self.mode == "play":
                self.spawn_index = spawn_notes(
                    self.recorded, self.active_notes, t, self.spawn_index
                )
                cleanup_notes(self.active_notes, t)

    def draw(self) -> None:
        self.screen.fill((0, 0, 0))
        s = self.state

        if s == "splash":
            screens.draw_splash(self.screen, self.fonts)
        elif s == "main_menu":
            screens.draw_main_menu(self.screen, self.fonts, self.menu_index)
        elif s == "song_select":
            screens.draw_song_select(
                self.screen, self.fonts, self.songs, self.song_index
            )
        elif s == "message" and self.message:
            screens.draw_confirm_dialog(
                self.screen,
                self.fonts,
                "NOTIFICATION",
                self.message.text,
                is_danger=False,
            )
        elif s == "chart_choice":
            screens.draw_chart_choice(
                self.screen,
                self.fonts,
                self.song_path,
                self.charts,
                self.chart_index,
                self.current_profile,
            )
        elif s == "high_scores":
            screens.draw_high_scores(
                self.screen, self.fonts, self.data.get_global_bests()
            )
        elif s == "results":
            screens.draw_results(
                self.screen, self.fonts, self.final_hits, self.final_total
            )
        elif s == "profile_select":
            screens.draw_profile_select(
                self.screen,
                self.fonts,
                self.data.list_profile_names(),
                self.menu_index,
                self.current_profile.name,
            )
        elif s == "create_profile":
            screens.draw_create_profile(self.screen, self.fonts, self.new_profile_name)
        elif s == "settings":
            screens.draw_settings(
                self.screen,
                self.fonts,
                self.current_profile.keys,
                self.rebinding_index,
                self.menu_index,
            )
        elif s == "quit_confirm":
            screens.draw_main_menu(self.screen, self.fonts, self.menu_index)
            screens.draw_confirm_dialog(
                self.screen,
                self.fonts,
                "QUIT GAME?",
                "Are you sure you want to exit?",
                True,
            )
        elif s in (
            "confirm_delete",
            "confirm_profile_delete",
            "confirm_reset_all",
            "confirm_reset_single",
        ):
            screens.draw_confirm_dialog(
                self.screen,
                self.fonts,
                "ARE YOU SURE?",
                "This action is permanent.",
                True,
            )
        elif s in ("game", "pause", "pause_countdown"):
            render.draw_game(
                self.screen,
                self.fonts,
                self.mode,
                self.score,
                len(self.recorded),
                self.song_path,
                self.active_notes,
                self.song_time(),
                None,
                self.current_profile,
                len(self.recorded),
            )
            if s == "pause":
                screens.draw_pause_menu(
                    self.screen, self.fonts, self.mode, self.pause_index
                )
            elif s == "pause_countdown":
                screens.draw_pause_countdown(
                    self.screen, self.fonts, self.pause_countdown_value
                )
