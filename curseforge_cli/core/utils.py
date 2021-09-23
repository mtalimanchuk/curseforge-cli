from pathlib import Path


def resolve_addon_path(installed_game_path: Path, category_section_path: Path) -> Path:
    path_resolver = {
        "%MYDOCUMENTS%": Path("~").expanduser() / "Documents",
    }

    path_root = category_section_path.parts[0]

    if path_root.startswith("%"):
        category_path = path_resolver[path_root] / category_section_path.relative_to(
            path_root
        )
    else:
        category_path = installed_game_path / category_section_path

    return category_path
