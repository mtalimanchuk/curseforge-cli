from io import BytesIO
from pathlib import Path
from typing import List
from zipfile import ZipFile

from requests import Session

from .model import AddonFile, AddonInfo, GameInfo


class SORT_TYPE:
    FEATURED = 0  # Sort by Featured
    POPULARITY = 1  # Sort by Popularity
    LAST_UPDATE = 2  # Sort by Last Update
    NAME = 3  # Sort by Name
    AUTHOR = 4  # Sort by Author
    TOTAL_DOWNLOADS = 5  # Sort by Total Downloads


def _apply_filter(row: dict, game_flavor: str = None):
    latest_files = []

    for f in row["latestFiles"]:
        f_game_flavor = f["gameVersionFlavor"]
        if f_game_flavor and f_game_flavor != game_flavor:
            continue
        latest_files.append(f)

    if latest_files:
        row["latestFiles"] = latest_files
        return AddonInfo.from_api(row)


class API:
    def __init__(self) -> None:
        self.base_url = "https://addons-ecs.forgesvc.net/api/v2"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"
        }

    def get_game_info(self, id: int) -> GameInfo:
        with Session() as session:
            r = session.get(f"{self.base_url}/game/{id}", headers=self.headers)
            data = r.json()

        return GameInfo.from_api(data)

    def get_addon(self, id: int, game_flavor: str = None):
        with Session() as session:
            r = session.get(f"{self.base_url}/addon/{id}", headers=self.headers)
            data = r.json()

        addon = _apply_filter(data, game_flavor)
        if addon:
            return addon

    def download_addon(self, id: int, extract_path: Path, game_flavor: str = None):
        addon = self.get_addon(id, game_flavor)
        latest_file = sorted(
            addon.latest_files, key=lambda lf: lf.file_date, reverse=True
        )[0]
        extract_path = extract_path / addon.category_section.path

        with Session() as session:
            r = session.get(latest_file.url, headers=self.headers)

        zip_io = BytesIO()
        zip_io.write(r.content)
        zip_io.seek(0)

        with ZipFile(zip_io, "r") as zip_f:
            zip_f.extractall(extract_path)

    def search_addon(
        self,
        query: str,
        game_id: int,
        game_flavor: str,
        game_version: str = "",
        page_size: int = 500,
        sort: SORT_TYPE = SORT_TYPE.POPULARITY,
    ) -> List[AddonInfo]:
        kwargs = {
            "gameId": game_id,
            "searchFilter": query,
            "gameVersion": game_version,
            "pageSize": page_size,
            "sort": sort,
        }
        kwargs_str = "&".join(f"{k}={v}" for k, v in kwargs.items())

        with Session() as session:
            r = session.get(
                f"{self.base_url}/addon/search?{kwargs_str}",
                headers=self.headers,
            )
            data = r.json()

        results = []

        for row in data:
            addon = _apply_filter(row, game_flavor)
            if addon:
                results.append(addon)

        return results
