from pathlib import Path

SKIP_FILE_PREFIXES: tuple[str, ...] = (
    "._",
    ".DS_Store",
    ".AppleDouble",
    ".Spotlight-V100",
    ".Trashes",
    ".fseventsd",
    "Thumbs.db",
    "desktop.ini",
)

SKIP_DIR_NAMES: frozenset[str] = frozenset(
    {
        "$RECYCLE.BIN",
        "System Volume Information",
        ".Trash",
        "@eaDir",
        "#recycle",
    }
)

VIDEO_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".mp4", ".mov", ".mxf",
        ".avi", ".wmv", ".mkv",
        ".m4v", ".mpg", ".mpeg",
        ".webm", ".flv", ".vob",
        ".ogv", ".ogg", ".dv",
        ".qt", ".f4v", ".m2ts",
        ".ts", ".3gp", ".3g2",
    }
)


def should_skip_file(name: str) -> bool:
    return any(name.startswith(p) for p in SKIP_FILE_PREFIXES)


def should_skip_dir(name: str) -> bool:
    return name in SKIP_DIR_NAMES


def should_skip_path(path: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in path.parts)


def is_video(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS
