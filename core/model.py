from datetime import datetime
from pathlib import Path
from typing import List, Optional
import re

from pydantic import BaseModel, validator


class colors:
    BLACK = "\u001b[30m"
    PALE_RED = "\u001b[31m"
    PALE_GREEN = "\u001b[32m"
    PALE_YELLOW = "\u001b[33m"
    PALE_BLUE = "\u001b[34m"
    PALE_MAGENTA = "\u001b[35m"
    PALE_CYAN = "\u001b[36m"

    GRAY = "\u001b[90m"
    RED = "\u001b[91m"
    GREEN = "\u001b[92m"
    YELLOW = "\u001b[93m"
    BLUE = "\u001b[94m"
    MAGENTA = "\u001b[95m"
    CYAN = "\u001b[96m"
    WHITE = "\u001b[97m"

    BG_GRAY = "\u001b[100m"
    BG_BLACK = "\u001b[40m"
    BG_RED = "\u001b[41m"
    BG_GREEN = "\u001b[42m"
    BG_YELLOW = "\u001b[43m"
    BG_BLUE = "\u001b[44m"
    BG_MAGENTA = "\u001b[45m"
    BG_CYAN = "\u001b[46m"
    BG_WHITE = "\u001b[47m"

    BOLD = "\u001b[1m"
    RESET = "\u001b[0m"


class GameDetectionHint(BaseModel):
    type: int
    path: str
    key: Optional[str] = None
    options: int

    @classmethod
    def from_api(cls, data: dict):
        kwargs = dict(
            type=data.get("hintType"),
            path=data.get("hintPath"),
            key=data.get("hintKey"),
            options=data.get("hintOptions"),
        )
        return cls(**kwargs)


class GameFile(BaseModel):
    is_required: bool
    file_name: str
    file_type: int
    platform_type: int

    @classmethod
    def from_api(cls, data: dict):
        kwargs = dict(
            is_required=data.get("isRequired"),
            file_name=data.get("fileName"),
            file_type=data.get("fileType"),
            platform_type=data.get("platformType"),
        )
        return cls(**kwargs)


class CategorySection(BaseModel):
    name: str
    package_type: int
    path: Path
    initial_inclusion_pattern: str
    extra_include_pattern: Optional[str]

    @classmethod
    def from_api(cls, data: dict):
        kwargs = dict(
            name=data.get("name"),
            package_type=data.get("packageType"),
            path=Path(data.get("path")),
            initial_inclusion_pattern=data.get("initialInclusionPattern"),
            extra_include_pattern=data.get("extraIncludePattern"),
        )
        return cls(**kwargs)


class GameInfo(BaseModel):
    curse_id: int
    name: str
    slug: str
    game_files: List[GameFile]
    game_detection_hints: List[GameDetectionHint]
    category_sections: List[CategorySection]
    addon_settings_folder_filter: Optional[str]
    addon_settings_starting_folder: Optional[str]
    addon_settings_file_filter: Optional[str]
    addon_settings_file_removal_filter: Optional[str]

    @classmethod
    def from_api(cls, data: dict):
        kwargs = dict(
            curse_id=data.get("id"),
            name=data.get("name"),
            slug=data.get("slug"),
            game_files=[GameFile.from_api(f) for f in data.get("gameFiles")],
            game_detection_hints=[
                GameDetectionHint.from_api(h) for h in data.get("gameDetectionHints")
            ],
            category_sections=[
                CategorySection.from_api(c) for c in data.get("categorySections")
            ],
            addon_settings_folder_filter=data.get("addonSettingsFolderFilter"),
            addon_settings_starting_folder=data.get("addonSettingsStartingFolder"),
            addon_settings_file_filter=data.get("addonSettingsFileFilter"),
            addon_settings_file_removal_filter=data.get(
                "addonSettingsFileRemovalFilter"
            ),
        )
        return cls(**kwargs)


class AddonFile(BaseModel):
    id: int
    display_name: str
    file_name: str
    file_date: datetime
    url: str
    dependencies: List[str]
    modules: List[str]
    project_id: int
    game_id: int
    game_version: List[str]
    game_version_flavor: Optional[str]

    @classmethod
    def from_api(cls, data: dict):
        date_str = data.get("fileDate")
        date_str = date_str.rstrip("Z")
        date_parts = date_str.rsplit(".", maxsplit=1)

        try:
            date_str, microseconds = date_parts
        except ValueError:
            date_str = date_parts[0]
            microseconds = 0

        date_str = f"{date_str}.{microseconds:<06}"
        file_date = datetime.fromisoformat(date_str)

        # TODO parse dependency id and discover addon name
        dependencies = [
            str(d.get("addonId", "not found")) for d in data.get("dependencies")
        ]

        kwargs = dict(
            id=data.get("id"),
            display_name=data.get("displayName"),
            file_name=data.get("fileName"),
            file_date=file_date,
            url=data.get("downloadUrl"),
            dependencies=dependencies,
            modules=[m["foldername"] for m in data.get("modules")],
            project_id=data.get("projectId"),
            game_id=data.get("gameId"),
            game_version=data.get("gameVersion"),
            game_version_flavor=data.get("gameVersionFlavor"),
        )
        return cls(**kwargs)

    @property
    def view(self) -> str:
        versions = ", ".join(self.game_version)
        indent = f"{colors.BG_YELLOW} {colors.RESET} "

        full_game_name = f"{self.game_version_flavor or 'version'} {versions}"
        header = f"{indent}{colors.BOLD}{self.file_date:%d %b %Y}{colors.RESET} {self.display_name} for {colors.BOLD}{full_game_name}{colors.RESET}"

        game_info = f"{indent}{self.url}"

        dependencies = ", ".join(self.dependencies)
        if dependencies:
            dependencies = f"{indent}Depends on: {dependencies}\n"

        view = "\n".join(f"{row}" for row in [header, game_info, dependencies])

        return view


class AddonLocalInfo(BaseModel):
    folder_name: str
    interface: Optional[int]
    title: Optional[str]
    curse_id: Optional[int]

    @validator("title", always=True)
    def remove_coloring(cls, v, values) -> str:
        return re.sub(r"\|c[0-9a-fA-F]{8}|\|r", "", v)


class AddonInfo(BaseModel):
    curse_id: int
    name: str
    authors: List[str]
    url: str
    summary: str
    download_count: int
    latest_files: List[AddonFile]
    category_section: CategorySection
    slug: str

    @classmethod
    def from_api(cls, data: dict):
        latest_files_unsorted = [AddonFile.from_api(f) for f in data.get("latestFiles")]
        latest_files = sorted(
            latest_files_unsorted, key=lambda lf: lf.file_date, reverse=True
        )

        kwargs = dict(
            curse_id=data.get("id"),
            name=data.get("name"),
            authors=[a.get("name") for a in data.get("authors")],
            url=data.get("websiteUrl"),
            summary=data.get("summary"),
            download_count=int(data.get("downloadCount")),
            latest_files=latest_files,
            category_section=CategorySection.from_api(data.get("categorySection")),
            slug=data.get("slug"),
        )
        return cls(**kwargs)

    @property
    def latest_file(self) -> AddonFile:
        return self.latest_files[0]

    @property
    def view(self) -> str:
        authors = ", ".join(self.authors)
        download_count = self.download_count
        if download_count > 1e6:
            download_count = f"{download_count // int(1e6)}M"
        elif download_count > 1e3:
            download_count = f"{download_count // int(1e3)}K"
        header = f"{colors.BLACK}{colors.BG_YELLOW}#{colors.BG_WHITE}{self.curse_id} | {self.name} {colors.RESET} by {colors.BOLD}{authors} [{download_count} downloads]{colors.RESET}"

        summary = f"{self.summary}\n"

        files = "\n".join(f.view for f in self.latest_files)

        view = "\n".join([header, summary, files])

        return view

    @property
    def summary_view(self) -> str:
        header = f"#{self.curse_id} | {self.name}"

        summary = f"{self.summary}\n"

        view = "\n".join([header, summary])

        return view


class InstalledAddon(BaseModel):
    local_info: AddonLocalInfo
    info: Optional[AddonInfo]
    date_installed: Optional[datetime]

    @property
    def view(self):
        header = f"{colors.BOLD}{self.local_info.title or self.local_info.folder_name}{colors.RESET}"

        body = ""
        if self.info:
            body = self.info.summary_view

        view = "\n".join([header, body])

        return view


class InstalledGame(BaseModel):
    slug: str
    path: Path
    info: GameInfo
    addons: Optional[List[InstalledAddon]] = []

    def to_dict(self) -> dict:
        as_dict = dict(
            slug=self.slug,
            path=self.path,
            info=self.info,
            addons=self.addons,
        )
        return as_dict

    @property
    def view(self):
        if self.addons:
            view = "\n".join(a.view for a in self.addons)
        else:
            view = f"\nNo addons installed for {self.info.name}"

        return view
