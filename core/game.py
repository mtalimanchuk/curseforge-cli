import json
from pathlib import Path
from typing import List
import winreg

from core.model import (
    AddonLocalInfo,
    CategorySection,
    GameDetectionHint,
    GameInfo,
    InstalledAddon,
    InstalledGame,
)


class GameNotSupportedError(Exception):
    """
    Raise when the slug doesn't exist
    """


class RegKeyNotFound(Exception):
    """
    Raise when the key/value do not exist in registry
    """


class MultipleFoldersFound(Exception):
    """
    Raise when multiple game folders were found and the user should enter it manually via addgame
    """


class NoFoldersFound(Exception):
    """
    Raise when no game folders were found and the user should enter it manually via addgame
    """


def search_registry(reg_key: str, reg_value: str) -> Path:
    try:
        if reg_key.startswith("HKEY_LOCAL_MACHINE"):
            reg_key = reg_key[len("HKEY_LOCAL_MACHINE") :].strip("\\")
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_key)
    except FileNotFoundError:
        import platform

        bitness = platform.architecture()[0]
        if bitness == "32bit":
            other_view_flag = winreg.KEY_WOW64_64KEY
        elif bitness == "64bit":
            other_view_flag = winreg.KEY_WOW64_32KEY

        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                reg_key,
                access=winreg.KEY_READ | other_view_flag,
            )
        except FileNotFoundError:
            """
            We really could not find the key in both views.
            """
            return

    try:
        value = winreg.QueryValueEx(key, reg_value)

        return Path(value[0]).absolute()
    except (FileNotFoundError, TypeError):
        return


def search_directory(path) -> Path:
    return


class Game:
    def __init__(self, curse_id: int, slug: str, game_folder_ending: str) -> None:
        self.curse_id = curse_id
        self.slug = slug
        self.game_folder_ending = game_folder_ending

    def get_addon_local_info(self, addon_path: Path):
        raise NotImplementedError(
            "Override get_addon_local_info method in your custom {self.__name__} child class"
        )

    def _discover_addons(self, path: Path, category_sections: List[CategorySection]):
        local_addons = []

        for cat in category_sections:
            # TODO add proper path builder which resolves %FOLDERS%
            cat_path = path / cat.path
            for addon_path in cat_path.glob("*"):
                local_info = self.get_addon_local_info(addon_path)
                addon = InstalledAddon(local_info=local_info)
                local_addons.append(addon)

        return local_addons

    def _discover_game_path(self, hints: List[GameDetectionHint]) -> Path:
        possible_results = []

        for h in hints:
            game_dir = None

            if h.type == 1:
                game_dir = search_registry(h.path, h.key)
            elif h.type == 2:
                game_dir = search_directory(h.path)
            else:
                raise ValueError(f"Unknown hint type {h.type}")

            if game_dir and game_dir.name == self.game_folder_ending:
                possible_results.append(game_dir)

        result = list(set(possible_results))

        if len(result) > 1:
            raise MultipleFoldersFound(result)
        elif len(result) == 0:
            raise NoFoldersFound()
        else:
            return result[0]

    def save(self, game: InstalledGame):
        path = Path(f"./appdata/installed_games/{self.slug}.json")
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w") as save_f:
            save_f.write(game.json())

    def load(self) -> InstalledGame:
        path = Path(f"./appdata/installed_games/{self.slug}.json")

        game = InstalledGame.parse_file(path, content_type="json")

        return game

    def discover(self, info: GameInfo) -> InstalledGame:
        path = self._discover_game_path(info.game_detection_hints)
        addons = self._discover_addons(path, info.category_sections)

        game = InstalledGame(slug=self.slug, path=path, info=info, addons=addons)
        # self.save(game)

        return game


class WoW(Game):
    def get_addon_local_info(self, addon_path: Path):
        toc_path = list(addon_path.glob("*.toc"))[0]

        interface = None
        curse_id = None
        title = None

        with toc_path.open("r", encoding="utf-8") as toc_f:
            for line in list(toc_f):
                line = line.strip()
                if line.startswith("##"):
                    k, v = [
                        text.strip()
                        for text in line.lstrip("# ").split(":", maxsplit=1)
                    ]
                    if k == "Interface":
                        interface = int(v)
                    elif k == "X-Curse-Project-ID":
                        curse_id = int(v)
                    elif k == "Title":
                        title = v

        return AddonLocalInfo(
            interface=interface,
            folder_name=addon_path.name,
            title=title,
            curse_id=curse_id,
        )


GAMES = {
    "wow_retail": WoW(1, "wow_retail", "_retail_"),
    "wow_classic": WoW(1, "wow_classic", "_classic_era_"),
    "wow_tbc": WoW(1, "wow_burning_crusade", "_classic_"),
}
