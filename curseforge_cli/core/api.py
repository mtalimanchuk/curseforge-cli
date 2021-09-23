from ..core.utils import resolve_addon_path
from io import BytesIO
from pathlib import Path
from typing import List
from zipfile import ZipFile

from requests import Session
from tqdm import tqdm

from ..core.model import AddonInfo, GameInfo


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

    def download_addon(
        self, id: int, installed_game_path: Path, game_flavor: str = None
    ):
        addon = self.get_addon(id, game_flavor)

        modules = ", ".join(addon.latest_file.modules)
        print(
            f"Downloading {addon.name} [{modules}] from {addon.latest_file.file_date:%d %b %Y}"
        )

        extract_path = resolve_addon_path(
            installed_game_path, addon.category_section.path
        )

        with Session() as session:
            r = session.get(addon.latest_file.url, headers=self.headers, stream=True)

        total_size_in_bytes = int(r.headers.get("content-length", 0))
        chunk_size = 1024  # 1 Kibibyte
        progress_bar = tqdm(total=total_size_in_bytes, unit="iB", unit_scale=True)

        zip_io = BytesIO()

        for chunk in r.iter_content(chunk_size):
            progress_bar.update(len(chunk))
            zip_io.write(chunk)

        progress_bar.close()

        if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
            print("ERROR, downloading went wrong")

        zip_io.seek(0)

        try:
            print(f"Extracting to {extract_path.absolute()}... ", end="")

            with ZipFile(zip_io, "r") as zip_f:
                zip_f.extractall(extract_path)

            print("Done")
        except Exception as e:
            print(f"Failed because {type(e)}: {e}")

    def search_addon(
        self,
        query: str,
        game_id: int,
        game_flavor: str,
        game_version: str = "",
        page_size: int = 50,
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
        url = f"{self.base_url}/addon/search?{kwargs_str}"

        with Session() as session:
            r = session.get(
                url,
                headers=self.headers,
            )
            data = r.json()

        results = []

        for row in data:
            addon = _apply_filter(row, game_flavor)
            if addon:
                results.append(addon)

        return results
