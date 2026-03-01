from __future__ import annotations
import json
import pygame
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List


@dataclass
class SongStat:
    best_hits: int = 0
    best_percent: float = 0.0


@dataclass
class PlayerStats:
    # Use SongStat objects instead of raw dicts for better IDE support
    song_data: Dict[str, SongStat] = field(default_factory=dict)


@dataclass
class Profile:
    name: str
    keys: List[int] = field(
        default_factory=lambda: [
            pygame.K_y,
            pygame.K_u,
            pygame.K_i,
            pygame.K_o,
            pygame.K_p,
        ]
    )
    stats: PlayerStats = field(default_factory=PlayerStats)


class DataManager:
    def __init__(self, save_path: str = "save_data"):
        self.base_path = Path(save_path)
        self.base_path.mkdir(exist_ok=True)
        self.global_bests_path = self.base_path / "global_bests.json"
        self._ensure_files()

    def _ensure_files(self):
        if not self.global_bests_path.exists():
            with open(self.global_bests_path, "w") as f:
                json.dump({}, f)

    def list_profile_names(self) -> List[str]:
        """Returns clean list of profile names found in save folder."""
        # ignore system files and metadata
        return [
            f.stem
            for f in self.base_path.glob("*.json")
            if f.stem not in ("global_bests", "profiles_meta")
        ]

    def save_profile(self, profile: Profile):
        # We lowercase the filename to avoid "Guest.json" vs "guest.json" conflicts
        path = self.base_path / f"{profile.name.lower()}.json"
        with open(path, "w") as f:
            json.dump(asdict(profile), f, indent=4)

    def load_profile(self, profile_name: str) -> Profile:
        path = self.base_path / f"{profile_name.lower()}.json"
        if not path.exists():
            return Profile(name=profile_name)

        try:
            with open(path, "r") as f:
                data = json.load(f)

            # Reconstruct SongStat objects from raw dictionary data
            raw_song_data = data.get("stats", {}).get("song_data", {})
            reconstructed_stats = {
                k: SongStat(v.get("best_hits", 0), v.get("best_percent", 0.0))
                for k, v in raw_song_data.items()
            }

            return Profile(
                name=data.get("name", profile_name),
                keys=data.get("keys", Profile(name="").keys),
                stats=PlayerStats(song_data=reconstructed_stats),
            )
        except (json.JSONDecodeError, KeyError, TypeError):
            return Profile(name=profile_name)

    def get_global_bests(self) -> Dict[str, Dict]:
        try:
            with open(self.global_bests_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def update_records(
        self, chart: str, profile: Profile, hits: int, total: int
    ) -> bool:
        """Saves new records if hits are higher than previous bests."""
        percent = round((hits / total) * 100, 2) if total > 0 else 0
        is_new_pb = False

        # 1. Update Global Leaders
        bests = self.get_global_bests()
        # Use .get() safely to compare hits
        global_hits = bests.get(chart, {}).get("hits", -1)

        if hits > global_hits:
            bests[chart] = {"player": profile.name, "hits": hits, "accuracy": percent}
            with open(self.global_bests_path, "w") as f:
                json.dump(bests, f, indent=4)

        # 2. Update Local Profile
        current_pb = profile.stats.song_data.get(chart, SongStat())
        if hits > current_pb.best_hits:
            profile.stats.song_data[chart] = SongStat(
                best_hits=hits, best_percent=percent
            )
            self.save_profile(profile)
            is_new_pb = True

        return is_new_pb

    def reset_chart_score(self, chart_name: str, profile: Profile):
        """Wipes records for a specific chart from global and current profile."""
        bests = self.get_global_bests()
        if chart_name in bests:
            del bests[chart_name]
            with open(self.global_bests_path, "w") as f:
                json.dump(bests, f, indent=4)

        if chart_name in profile.stats.song_data:
            del profile.stats.song_data[chart_name]
            self.save_profile(profile)

    def reset_all_scores(self, profile: Profile):
        """Wipes global leaderboard and current profile's stats."""
        with open(self.global_bests_path, "w") as f:
            json.dump({}, f, indent=4)
        profile.stats.song_data.clear()
        self.save_profile(profile)

    def delete_profile(self, profile_name: str) -> bool:
        path = self.base_path / f"{profile_name}.json"
        if path.exists():
            try:
                path.unlink()
                return True
            except OSError:
                return False
        return False
