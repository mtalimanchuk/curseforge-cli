from ..core.utils import resolve_addon_path
from pathlib import Path
from typing import List, Optional
import winreg
from zipfile import ZipFile

from ..core.model import (
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
    def __init__(
        self, curse_id: int, slug: str, game_folder_ending: Optional[str] = None
    ) -> None:
        """Dummy Game class. Custom Games must inherit this.

        Args:
            curse_id (int): Game id according to curseforge API
            slug (str): Game slug (short form) according to curseforge API
            game_folder_ending (Optional[str], optional): Name of the game folder.
                Some games like WoW store game files inside a subfolder, e.g. WoW/_classic_, WoW/_retail_.
                Provide the name of this subfolder if the game does that.
                Defaults to None.
        """
        self.curse_id = curse_id
        self.slug = slug
        self.game_folder_ending = game_folder_ending

    def get_addon_local_info(self, addon_path: Path):
        raise NotImplementedError(
            f"Override get_addon_local_info method in {type(self)}"
        )

    def get_config_dir(self, installed_game_path: Path):
        raise NotImplementedError(f"Override get_config_dir method in {type(self)}")

    def export_config(self, installed_game_path: Path, export_path: Path):
        raise NotImplementedError(f"Override export_config method in {type(self)}")

    def import_config(self, installed_game_path: Path, import_path: Path):
        raise NotImplementedError(f"Override import_config method in {type(self)}")

    def _discover_addons(self, path: Path, category_sections: List[CategorySection]):
        local_addons = []

        for cat in category_sections:
            cat_path = resolve_addon_path(path, cat.path)

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

            if game_dir:
                if self.game_folder_ending and game_dir.name != self.game_folder_ending:
                    continue
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
        print(f"Discovered {info.name} in {path.absolute()}")

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
                    try:
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
                    except Exception:
                        pass

        return AddonLocalInfo(
            interface=interface,
            folder_name=addon_path.name,
            title=title,
            curse_id=curse_id,
        )

    def get_config_dir(self, installed_game_path: Path):
        return installed_game_path / "WTF"

    def export_config(self, installed_game_path: Path, export_path: str):
        export_path = Path(export_path)
        config_dir = self.get_config_dir(installed_game_path)

        with ZipFile(export_path, "w") as config_zip_f:
            for p in config_dir.glob("**/*"):
                config_zip_f.write(p, arcname=p.relative_to(config_dir))

        print(f"Exported {config_dir} contents to {export_path}")


class TES(Game):
    def get_addon_local_info(self, addon_path: Path):
        txt_path = list(addon_path.glob("*.txt"))[0]

        interface = None
        curse_id = None
        title = None

        with txt_path.open("r", encoding="utf-8") as toc_f:
            for line in list(toc_f):
                line = line.strip()
                if line.startswith("##"):
                    try:
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
                    except Exception:
                        pass

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
    "teso": TES(455, "teso", None),
}

"""
Other known games. Will be added later.
64 - The Secret World
335 - runes of magic
423 - world of tanks
424 - rift
432 - minecraft
449 - skyrim
454 - wildstar
"""
