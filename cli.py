import sys
from typing import List

from core.api import API
from core.game import GAMES, NoFoldersFound, MultipleFoldersFound
from core.model import InstalledAddon, InstalledGame


class CliError(Exception):
    """Raise when client should exit due to some error"""


class CurseCli:
    def __init__(self, game_slug: str) -> None:
        try:
            self.game = GAMES[game_slug]
        except KeyError:
            raise CliError(
                f"{game_slug} is not supported. Choose from {', '.join(GAMES.keys())}"
            )

        self.api = API()

        self._installed_game = None

    @property
    def installed_game(self) -> InstalledGame:
        if self._installed_game:
            return self._installed_game
        else:
            try:
                installed_game = self._load_installed_game()
                installed_game.addons = self._resolve_installed_addons(
                    installed_game.addons
                )
                self._installed_game = installed_game
                return self._installed_game
            except NoFoldersFound:
                raise CliError(f"{self.game.slug} is not installed")
            except MultipleFoldersFound:
                raise CliError(
                    f"Discovered multiple installations of {self.game.slug}. Please provide the correct one via {self.game.slug} addpath path/to/game/folder"
                )

    def _save_installed_game(self):
        self.game.save(self.installed_game)

    def _load_installed_game(self) -> InstalledGame:
        try:
            return self.game.load()
        except FileNotFoundError:
            print(f"Discovering {self.game.slug} installation path")
            info = self.api.get_game_info(self.game.curse_id)
            return self.game.discover(info)

    def _resolve_installed_addons(self, addons: List[InstalledAddon]) -> InstalledGame:
        for addon in addons:
            try:
                addon_info = self.api.get_addon(
                    addon.local_info.curse_id, self.game.slug
                )
                addon.info = addon_info
            except Exception:
                pass

        return addons

    def list(self):
        print(self.installed_game.view)

    def search(self, query: str, **kwargs):
        results = self.api.search_addon(
            query, self.game.curse_id, self.game.slug, **kwargs
        )
        for r in results:
            print("=" * 80)
            print(r.view)

    def install(self, query: int, **kwargs):
        extract_path = self.installed_game.path
        self.api.download_addon(int(query), extract_path, self.game.slug)


def parse_args():
    argv = sys.argv[1:]

    game_slug = argv.pop(0)
    action = argv.pop(0)
    args = []
    kwargs = {}

    if action == "list":
        pass
    elif action == "search":
        args = [argv.pop(0)]
        kwargs = {k.lstrip("-"): v for k, v in zip(argv[::2], argv[1::2])}
    elif action == "install":
        args = [argv.pop(0)]
    else:
        raise CliError(f"Action '{action}' is not supported")

    return game_slug, action, args, kwargs


if __name__ == "__main__":
    try:
        game_slug, action, args, kwargs = parse_args()

        cli = CurseCli(game_slug)

        if action == "list":
            cli.list()
        if action == "search":
            cli.search(*args, **kwargs)
        if action == "install":
            cli.install(*args, **kwargs)
    except CliError as ce:
        print(f"[ERROR] {ce}. Exiting...")
